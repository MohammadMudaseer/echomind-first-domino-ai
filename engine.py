"""EchoMind core logic: scenario model, live-weather helpers, geo maths, incident store.

Nothing here imports Streamlit, so it can be unit-tested on its own.
All risk scores are illustrative indices (0-1), NOT calibrated probabilities.
"""
from __future__ import annotations

import math
import os
import tempfile
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import networkx as nx
import pandas as pd

# --------------------------------------------------------------------------
# Dependency graph
# --------------------------------------------------------------------------
NODE_INFO = {
    "Heavy rainfall": ("Weather", "Rainfall intensity exceeds the scenario threshold."),
    "Drain blockage": ("Drainage", "Reduced drainage capacity increases water accumulation."),
    "Street flooding": ("Flooding", "Runoff and blocked drainage combine to create local waterlogging."),
    "Road disruption": ("Transport", "Waterlogging makes a road segment difficult to use."),
    "Traffic congestion": ("Transport", "Vehicles divert onto fewer usable routes."),
    "Emergency delay": ("Emergency", "Congestion and road disruption increase response delay."),
    "Power interruption": ("Utilities", "Flooding may affect a vulnerable utility point."),
}
EDGES = [
    ("Heavy rainfall", "Street flooding"),
    ("Drain blockage", "Street flooding"),
    ("Street flooding", "Road disruption"),
    ("Road disruption", "Traffic congestion"),
    ("Traffic congestion", "Emergency delay"),
    ("Street flooding", "Power interruption"),
]
LOCATIONS = {
    "Drain blockage": "Drain D-04 · Market Lane",
    "Street flooding": "Low point L-2 · Market Lane",
    "Road disruption": "Bridge Road junction",
    "Traffic congestion": "Central Avenue",
    "Emergency delay": "Community Clinic access",
    "Power interruption": "Utility cabinet U-3",
    "Heavy rainfall": "Neighborhood-wide",
}
INTERVENTIONS = [
    "No intervention (baseline)",
    "Clear the critical drain",
    "Deploy temporary water pumps",
    "Protect the critical road",
    "Reroute traffic early",
]
DOWNSTREAM = ["Street flooding", "Road disruption", "Traffic congestion", "Emergency delay"]


def clamp(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def simulate(rain_mm, blockage_pct, traffic_load, intervention=INTERVENTIONS[0], report_pressure=0.0):
    """Transparent scenario rules. Returns {node: index in 0..1}.

    report_pressure (0..1) optionally nudges the flood index upward to reflect
    recent community reports. Default 0 keeps the pure scenario model.
    """
    rain = clamp((rain_mm - 10) / 70)
    blockage = clamp(blockage_pct / 100)
    traffic_in = clamp(traffic_load / 100)

    rain_effect = rain * 0.55 if intervention == "Deploy temporary water pumps" else rain
    if intervention == "Clear the critical drain":
        blockage *= 0.18
    road_protection = 0.42 if intervention == "Protect the critical road" else 1.0
    traffic_relief = 0.72 if intervention == "Reroute traffic early" else 1.0

    flood = clamp(0.62 * rain_effect + 0.58 * blockage + 0.12 * rain_effect * blockage
                  + 0.20 * clamp(report_pressure))
    road = clamp(flood * 0.88 * road_protection)
    traffic = clamp((0.52 * road + 0.48 * traffic_in) * traffic_relief)
    emergency = clamp(0.68 * traffic + 0.42 * road)
    power = clamp(flood * 0.58)
    return {
        "Heavy rainfall": rain, "Drain blockage": blockage, "Street flooding": flood,
        "Road disruption": road, "Traffic congestion": traffic,
        "Emergency delay": emergency, "Power interruption": power,
    }


def build_graph(scores):
    g = nx.DiGraph()
    for n, (kind, desc) in NODE_INFO.items():
        g.add_node(n, kind=kind, description=desc, risk=scores[n])
    g.add_edges_from(EDGES)
    return g


def top_trigger(scores):
    """Downstream-reach heuristic: starting-hazard index x (1 + sum of descendant indices)."""
    g = build_graph(scores)
    impact = {n: scores[n] * (1 + sum(scores[d] for d in nx.descendants(g, n)))
              for n in ("Heavy rainfall", "Drain blockage")}
    return max(impact, key=impact.get), impact


def worst_downstream(scores) -> float:
    return max(scores[n] for n in DOWNSTREAM)


def rank_interventions(rain_mm, blockage_pct, traffic_load, report_pressure=0.0) -> pd.DataFrame:
    """Run every intervention against the same scenario and rank by worst downstream index."""
    base = worst_downstream(simulate(rain_mm, blockage_pct, traffic_load, INTERVENTIONS[0], report_pressure))
    rows = []
    for name in INTERVENTIONS:
        s = simulate(rain_mm, blockage_pct, traffic_load, name, report_pressure)
        w = worst_downstream(s)
        rows.append({"Intervention": name, "Worst downstream index": round(w * 100),
                     "Reduction vs baseline (points)": round((base - w) * 100)})
    return pd.DataFrame(rows).sort_values("Worst downstream index").reset_index(drop=True)


def risk_band(index_0_100: float) -> str:
    if index_0_100 >= 70:
        return "HIGH"
    if index_0_100 >= 40:
        return "ELEVATED"
    return "LOW"


# --------------------------------------------------------------------------
# Live weather (Open-Meteo) parsing
# --------------------------------------------------------------------------
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_FIELDS = "temperature_2m,relative_humidity_2m,precipitation,rain,showers,wind_speed_10m"
HOURLY_FIELDS = "precipitation,precipitation_probability"


def weather_params(lat, lon):
    return {
        "latitude": lat, "longitude": lon,
        "current": CURRENT_FIELDS, "hourly": HOURLY_FIELDS,
        "past_hours": 24, "forecast_hours": 24, "timezone": "Asia/Kolkata",
    }


def parse_weather(payload: dict) -> dict:
    """Turn an Open-Meteo response into {'current': dict, 'hourly': DataFrame, 'now': Timestamp}."""
    current = payload.get("current") or {}
    hourly = payload.get("hourly") or {}
    df = pd.DataFrame({
        "time": pd.to_datetime(hourly.get("time", [])),
        "precip_mm": pd.to_numeric(pd.Series(hourly.get("precipitation", [])), errors="coerce"),
        "precip_prob": pd.to_numeric(pd.Series(hourly.get("precipitation_probability", [])), errors="coerce"),
    })
    now = pd.to_datetime(current.get("time")) if current.get("time") else (df["time"].max() if len(df) else pd.NaT)
    return {"current": current, "hourly": df, "now": now}


def rainfall_window(hourly: pd.DataFrame, now, past_h=3, future_h=3):
    """Observed/analysis mm over the past `past_h` hours and forecast mm over the next `future_h`.

    Hour stamps are the START of each hour. Returns (past_mm, future_mm, peak_prob_pct_or_None).
    """
    if hourly.empty or pd.isna(now):
        return 0.0, 0.0, None
    hour_now = pd.Timestamp(now).floor("h")
    past = hourly[(hourly["time"] >= hour_now - pd.Timedelta(hours=past_h)) & (hourly["time"] < hour_now)]
    fut = hourly[(hourly["time"] >= hour_now) & (hourly["time"] < hour_now + pd.Timedelta(hours=future_h))]
    prob = fut["precip_prob"].max() if not fut.empty else float("nan")
    return (float(past["precip_mm"].sum(skipna=True)), float(fut["precip_mm"].sum(skipna=True)),
            None if pd.isna(prob) else float(prob))


# --------------------------------------------------------------------------
# Geo helpers (device tracking)
# --------------------------------------------------------------------------
def haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest(lat, lon, points: pd.DataFrame, lat_col="latitude", lon_col="longitude"):
    """Return (row, metres) of the closest point, or (None, None)."""
    best, best_d = None, None
    for _, row in points.iterrows():
        try:
            d = haversine_m(lat, lon, float(row[lat_col]), float(row[lon_col]))
        except (TypeError, ValueError):
            continue
        if best_d is None or d < best_d:
            best, best_d = row, d
    return best, best_d


def fmt_distance(m) -> str:
    return f"{m:.0f} m" if m < 1000 else f"{m / 1000:.1f} km"


# --------------------------------------------------------------------------
# Incident store (CSV, atomic writes, schema migration)
# --------------------------------------------------------------------------
INCIDENT_COLUMNS = ["report_id", "reported_at", "incident_type", "description", "severity",
                    "latitude", "longitude", "area", "status"]
SEVERITY_WEIGHT = {"Low": 0.25, "Moderate": 0.5, "High": 0.8, "Critical": 1.0}
STATUSES = ["Unverified — needs review", "Reviewed — plausible", "Reviewed — not supported", "Resolved"]
_WRITE_LOCK = threading.Lock()


def load_incidents(path: Path) -> pd.DataFrame:
    """Read the CSV, tolerating older files that lack newer columns (e.g. report_id)."""
    if not Path(path).exists():
        return pd.DataFrame(columns=INCIDENT_COLUMNS)
    data = pd.read_csv(path, dtype=str).fillna("")
    for col in INCIDENT_COLUMNS:
        if col not in data.columns:
            data[col] = ""
    missing = data["report_id"] == ""
    if missing.any():
        data.loc[missing, "report_id"] = [f"R-{uuid.uuid4().hex[:8]}" for _ in range(int(missing.sum()))]
    return data[INCIDENT_COLUMNS]


def _atomic_write(path: Path, df: pd.DataFrame):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    os.close(fd)
    try:
        df.to_csv(tmp, index=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def save_incident(path: Path, incident_type, description, severity, lat, lon, area,
                  source="manual") -> str:
    """Append a report atomically. Returns the new report_id."""
    rid = f"R-{uuid.uuid4().hex[:8]}"
    row = {
        "report_id": rid,
        "reported_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "incident_type": incident_type, "description": description.strip(),
        "severity": severity, "latitude": float(lat), "longitude": float(lon),
        "area": area.strip(), "status": STATUSES[0],
    }
    with _WRITE_LOCK:
        existing = load_incidents(path)
        out = pd.concat([existing, pd.DataFrame([row], columns=INCIDENT_COLUMNS)], ignore_index=True)
        _atomic_write(path, out)
    return rid


def update_status(path: Path, report_id: str, status: str) -> bool:
    if status not in STATUSES:
        raise ValueError("Unknown status")
    with _WRITE_LOCK:
        data = load_incidents(path)
        mask = data["report_id"] == report_id
        if not mask.any():
            return False
        data.loc[mask, "status"] = status
        _atomic_write(path, data)
    return True


def recent_incidents(df: pd.DataFrame, hours=24, now=None) -> pd.DataFrame:
    """Reports from the last `hours`, excluding 'Resolved' and 'not supported' ones."""
    if df.empty:
        return df
    now = now or datetime.now().astimezone()
    ts = pd.to_datetime(df["reported_at"], errors="coerce", utc=True)
    cutoff = pd.Timestamp(now).tz_convert("UTC") - timedelta(hours=hours)
    keep = (ts >= cutoff) & ~df["status"].isin(["Resolved", "Reviewed — not supported"])
    return df[keep.fillna(False)]


def report_pressure(df: pd.DataFrame, hours=24, now=None) -> float:
    """0..1 summary of recent report volume x severity. Saturates at ~3 critical-equivalents."""
    recent = recent_incidents(df, hours, now)
    if recent.empty:
        return 0.0
    total = sum(SEVERITY_WEIGHT.get(s, 0.5) for s in recent["severity"])
    return clamp(total / 3.0)
