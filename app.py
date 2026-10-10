"""EchoMind — First Domino AI (v2: live tracking build).

Run:  streamlit run app.py
Live pieces: Open-Meteo rainfall feed (auto-refresh), live incident feed,
optional browser-GPS device tracking. Risk scores remain illustrative indices.
"""
import html
from datetime import datetime
from pathlib import Path

import altair as alt
import folium
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import requests
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

import engine as eng

try:  # optional: browser GPS
    from streamlit_js_eval import get_geolocation
except Exception:  # pragma: no cover
    get_geolocation = None

st.set_page_config(page_title="EchoMind | First Domino AI", page_icon="🌧️", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.hero {padding: 1.2rem 1.4rem; border-radius: 18px; background: linear-gradient(120deg,#10233f,#176b87); color: white; margin-bottom: .8rem;}
.hero h1 {color:white; margin:0;}
.hero p {color:#d9eef7; margin:.4rem 0 0 0;}
.pill {display:inline-block; padding:.15rem .6rem; border-radius:999px; font-size:.78rem; font-weight:600; margin-right:.4rem;}
.pill.live {background:#dcfce7; color:#166534;} .pill.off {background:#e2e8f0; color:#475569;}
.pill.sim {background:#ede9fe; color:#5b21b6;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🌧️ EchoMind — First Domino AI</h1>'
            '<p>Track live rain and community reports, simulate cascading neighbourhood failures, '
            'and test preventive actions before the first domino falls.</p></div>', unsafe_allow_html=True)
st.caption("HACKATHON PROTOTYPE • LIVE WEATHER + LIVE REPORT FEED • RISK PINS & INDICES ARE SIMULATED • NOT AN OPERATIONAL WARNING SYSTEM")

CITY_COORDS = {
    "Warangal, Telangana": (17.9689, 79.5941),
    "Hyderabad, Telangana": (17.3850, 78.4867),
    "New Delhi, India": (28.6139, 77.2090),
}
INCIDENT_FILE = Path(__file__).with_name("incident_reports.csv")
REFRESH_OPTIONS = {"Off": None, "30 seconds": 30, "1 minute": 60, "5 minutes": 300}
AGE_OPTIONS = {"Last 6 hours": 6, "Last 24 hours": 24, "Last 3 days": 72, "Last 7 days": 168, "All saved": None}
STATUS_COLOUR = {eng.STATUSES[0]: "purple", eng.STATUSES[1]: "cadetblue",
                 eng.STATUSES[2]: "gray", eng.STATUSES[3]: "green"}


# --------------------------------------------------------------------------
# Data access
# --------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def _fetch_weather(lat, lon):
    """Cached 60 s. Raises on failure so errors are never cached."""
    r = requests.get(eng.OPEN_METEO_URL, params=eng.weather_params(lat, lon), timeout=6)
    r.raise_for_status()
    return r.json(), datetime.now().strftime("%H:%M:%S")


def get_weather(lat, lon):
    try:
        payload, fetched = _fetch_weather(lat, lon)
        parsed = eng.parse_weather(payload)
        if not parsed["current"]:
            return None, None, "no current data returned"
        return parsed, fetched, None
    except Exception as exc:  # network down, timeout, bad JSON
        return None, None, type(exc).__name__


def safe_load_incidents():
    try:
        return eng.load_incidents(INCIDENT_FILE)
    except Exception:
        st.warning("Saved incident reports could not be read. The file was left unchanged.")
        return pd.DataFrame(columns=eng.INCIDENT_COLUMNS)


def filter_by_age(df, hours):
    if hours is None or df.empty:
        return df
    ts = pd.to_datetime(df["reported_at"], errors="coerce", utc=True)
    return df[(ts >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=hours)).fillna(False)]


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("Live tracking")
    map_city = st.selectbox("Monitoring area", list(CITY_COORDS), index=0)
    center_lat, center_lon = CITY_COORDS[map_city]
    refresh_label = st.select_slider("Auto-refresh live panel", options=list(REFRESH_OPTIONS), value="1 minute")
    refresh_s = REFRESH_OPTIONS[refresh_label]
    live_weather = st.checkbox("Live rainfall feed (Open-Meteo)", value=True)
    drive_from_live = st.checkbox("Drive the simulation from live rainfall", value=True, disabled=not live_weather,
                                  help="Rainfall input = observed past 3 h + forecast next 3 h at the area centre.")
    blend_reports = st.checkbox("Blend recent community reports into flood index", value=False,
                                help="Adds up to +20 index points to street flooding from unresolved reports in the last 24 h.")
    track_me = st.checkbox("Track my device location (browser GPS)", value=False,
                           help="Your browser will ask permission. Needs HTTPS or localhost. Location stays in this session.")
    report_age_label = st.selectbox("Show reports", list(AGE_OPTIONS), index=1)

    st.divider()
    st.header("Scenario controls")
    weather, fetched_at, weather_err = (None, None, None)
    live_rain_mm = None
    if live_weather:
        weather, fetched_at, weather_err = get_weather(center_lat, center_lon)
        if weather:
            past_mm, fut_mm, peak_prob = eng.rainfall_window(weather["hourly"], weather["now"], 3, 3)
            live_rain_mm = past_mm + fut_mm
    using_live_rain = bool(drive_from_live and live_rain_mm is not None)
    if using_live_rain:
        rain_mm = min(100.0, live_rain_mm)
        st.slider("Rainfall (mm / scenario period)", 0.0, 100.0, float(rain_mm), disabled=True,
                  help="Locked to the live feed. Untick 'Drive the simulation from live rainfall' to edit.")
        st.caption(f"🟢 Live: {past_mm:.1f} mm past 3 h + {fut_mm:.1f} mm next 3 h")
    else:
        rain_mm = st.slider("Rainfall (mm / scenario period)", 0, 100, 75, 5)
        if drive_from_live and live_weather:
            st.caption("⚪ Live rainfall unavailable — using the manual value.")
    blockage_pct = st.slider("Drain blockage (%)", 0, 100, 85, 5)
    traffic_load = st.slider("Starting traffic load (%)", 0, 100, 65, 5)
    intervention = st.selectbox("Test one intervention", eng.INTERVENTIONS)
    st.info("Blockage and traffic are manual inputs: no drain sensors or live traffic feed are connected.")

# --------------------------------------------------------------------------
# Model run
# --------------------------------------------------------------------------
all_reports = safe_load_incidents()
pressure_24h = eng.report_pressure(all_reports, 24)
pressure = pressure_24h if blend_reports else 0.0
baseline = eng.simulate(rain_mm, blockage_pct, traffic_load, eng.INTERVENTIONS[0], pressure)
after = eng.simulate(rain_mm, blockage_pct, traffic_load, intervention, pressure)
trigger, impact = eng.top_trigger(baseline)
worst_base = eng.worst_downstream(baseline) * 100
band = eng.risk_band(worst_base)


def data_signature(weather_obj, reports_df):
    """Fingerprint of the live inputs the model depends on besides the sliders."""
    obs = None
    if weather_obj:
        p, f, _ = eng.rainfall_window(weather_obj["hourly"], weather_obj["now"], 3, 3)
        obs = (str(weather_obj["current"].get("time")), round(p + f, 2))
    rep = tuple(zip(reports_df["report_id"], reports_df["status"])) if not reports_df.empty else ()
    return obs, rep


RUN_SIGNATURE = data_signature(weather, all_reports)

pills = [
    '<span class="pill live">● LIVE WEATHER</span>' if weather else '<span class="pill off">○ WEATHER OFFLINE</span>',
    '<span class="pill live">● SIM DRIVEN BY LIVE RAIN</span>' if using_live_rain else '<span class="pill sim">SIM: MANUAL RAIN</span>',
    f'<span class="pill live">● AUTO-REFRESH {refresh_label.upper()}</span>' if refresh_s else '<span class="pill off">AUTO-REFRESH OFF</span>',
    '<span class="pill live">● GPS ON</span>' if track_me else '<span class="pill off">GPS OFF</span>',
]
st.markdown(" ".join(pills), unsafe_allow_html=True)

if band == "HIGH":
    st.error(f"Simulated cascade concern: **HIGH** ({worst_base:.0f}/100 worst downstream index). Illustrative only — not an official warning.")
elif band == "ELEVATED":
    st.warning(f"Simulated cascade concern: **ELEVATED** ({worst_base:.0f}/100 worst downstream index). Illustrative only.")
else:
    st.success(f"Simulated cascade concern: **LOW** ({worst_base:.0f}/100 worst downstream index).")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rainfall input", f"{rain_mm:.1f} mm", help="Live-driven" if using_live_rain else "Manual")
c2.metric("Drain blockage", f"{blockage_pct}%")
c3.metric("Highest baseline index", f"{max(baseline.values()) * 100:.0f}/100")
c4.metric("First Domino candidate", trigger)
c5.metric("Report pressure (24 h)", f"{pressure_24h * 100:.0f}/100",
          help="Volume × severity of unresolved reports. Self-reported and unverified.")

tab_live, tab_sim, tab_report, tab_about = st.tabs(["📡 Live monitor", "🧪 Simulation", "📝 Report an incident", "⚠️ Limitations"])


# --------------------------------------------------------------------------
# TAB 1 — live monitor (auto-refreshing fragment)
# --------------------------------------------------------------------------
def live_panel():
    w, err = None, None
    if live_weather:
        w, _, err = get_weather(center_lat, center_lon)
    reports = safe_load_incidents()

    # If a live input the model uses has changed, refresh the whole page so scores update.
    if (drive_from_live or blend_reports) and data_signature(w, reports) != RUN_SIGNATURE:
        st.rerun()

    shown = filter_by_age(reports, AGE_OPTIONS[report_age_label])
    st.caption(f"Panel refreshed {datetime.now().strftime('%H:%M:%S')} (device clock)"
               + (f" • auto-refresh every {refresh_label}" if refresh_s else " • auto-refresh off"))

    # ---- Weather ----
    if w:
        cur = w["current"]
        obs_time = cur.get("time", "unknown")
        age_note = ""
        try:
            age_min = (datetime.now() - pd.to_datetime(obs_time).to_pydatetime()).total_seconds() / 60
            if age_min > 180:
                age_note = f" ⚠️ observation is {age_min / 60:.0f} h old"
        except Exception:
            pass
        st.markdown(f"**Live conditions — {map_city}** · source time {obs_time} (Asia/Kolkata){age_note}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Temperature", f"{cur.get('temperature_2m', '—')} °C")
        m2.metric("Precipitation now", f"{cur.get('precipitation', '—')} mm")
        m3.metric("Humidity", f"{cur.get('relative_humidity_2m', '—')}%")
        m4.metric("Wind", f"{cur.get('wind_speed_10m', '—')} km/h")

        hourly = w["hourly"].copy()
        if not hourly.empty:
            now_h = pd.Timestamp(w["now"]).floor("h")
            hourly["Period"] = hourly["time"].apply(lambda t: "Past / observed" if t < now_h else "Forecast")
            bars = alt.Chart(hourly).mark_bar().encode(
                x=alt.X("time:T", title="Hour (Asia/Kolkata)"),
                y=alt.Y("precip_mm:Q", title="Precipitation (mm/h)"),
                color=alt.Color("Period:N", scale=alt.Scale(domain=["Past / observed", "Forecast"], range=["#176b87", "#f59e0b"])),
                tooltip=[alt.Tooltip("time:T", title="Hour"), alt.Tooltip("precip_mm:Q", title="mm"),
                         alt.Tooltip("precip_prob:Q", title="Chance of rain %")])
            rule = alt.Chart(pd.DataFrame({"time": [now_h]})).mark_rule(strokeDash=[4, 4], color="#ef4444").encode(x="time:T")
            st.altair_chart((bars + rule).properties(height=210, title="Rain: past 24 h and next 24 h (red line = now)"),
                            use_container_width=True)
            nxt = hourly[hourly["time"] >= now_h].head(6)
            if not nxt.empty and nxt["precip_mm"].sum() >= 10:
                st.warning(f"Forecast shows {nxt['precip_mm'].sum():.1f} mm in the next 6 h at the area centre. "
                           "Consider checking drains early. (Forecasts are uncertain.)")
    elif live_weather:
        st.info(f"Live weather unavailable ({err}). Check your internet connection; the simulation still works with manual inputs.")
    else:
        st.caption("Live rainfall feed is switched off in the sidebar.")

    # ---- GPS tracking ----
    my_loc = None
    if track_me:
        if get_geolocation is None:
            st.info("GPS tracking needs the optional package: `pip install streamlit-js-eval`, then restart the app.")
        else:
            geo = get_geolocation()
            coords = geo.get("coords") if isinstance(geo, dict) else None
            if coords and coords.get("latitude") is not None:
                my_loc = {"lat": float(coords["latitude"]), "lon": float(coords["longitude"]),
                          "acc": float(coords.get("accuracy") or 0)}
                trail = st.session_state.setdefault("gps_trail", [])
                if not trail or (trail[-1][0], trail[-1][1]) != (my_loc["lat"], my_loc["lon"]):
                    trail.append((my_loc["lat"], my_loc["lon"], datetime.now().strftime("%H:%M:%S")))
                    del trail[:-50]
                st.session_state["my_loc"] = my_loc
            else:
                st.caption("Waiting for your browser's location permission…")
    else:
        st.session_state.pop("my_loc", None)
        st.session_state.pop("gps_trail", None)

    # ---- Map ----
    map_points = pd.DataFrame([
        {"Location": "Demo drain D-04", "latitude": center_lat + 0.010, "longitude": center_lon - 0.012, "System": "Drain blockage", "Risk": baseline["Drain blockage"] * 100},
        {"Location": "Demo low point L-2", "latitude": center_lat + 0.003, "longitude": center_lon - 0.003, "System": "Street flooding", "Risk": after["Street flooding"] * 100},
        {"Location": "Demo road junction", "latitude": center_lat - 0.006, "longitude": center_lon + 0.004, "System": "Road disruption", "Risk": after["Road disruption"] * 100},
        {"Location": "Demo avenue", "latitude": center_lat + 0.006, "longitude": center_lon + 0.010, "System": "Traffic congestion", "Risk": after["Traffic congestion"] * 100},
        {"Location": "Demo clinic access", "latitude": center_lat - 0.010, "longitude": center_lon + 0.012, "System": "Emergency delay", "Risk": after["Emergency delay"] * 100},
    ])
    colour_for = lambda v: "red" if v >= 70 else "orange" if v >= 40 else "green"

    focus = (my_loc["lat"], my_loc["lon"]) if my_loc else (center_lat, center_lon)
    fmap = folium.Map(location=focus, zoom_start=14 if my_loc else 13, control_scale=True)
    folium.Marker([center_lat, center_lon], tooltip=f"Map centre: {map_city}", icon=folium.Icon(color="blue", icon="info-sign")).add_to(fmap)
    for _, p in map_points.iterrows():
        col = colour_for(p["Risk"])
        folium.CircleMarker(
            [p["latitude"], p["longitude"]], radius=9, color=col, fill=True, fill_color=col, fill_opacity=0.8,
            tooltip=f"{p['Location']} | simulated index {p['Risk']:.0f}/100",
            popup=f"<b>{html.escape(p['Location'])}</b><br>System: {p['System']}<br>Simulated index: {p['Risk']:.0f}/100<br>"
                  "<i>Illustrative point, not a verified incident.</i>").add_to(fmap)
    cluster = MarkerCluster(name="Community reports").add_to(fmap)
    for _, r in shown.iterrows():
        try:
            lat, lon = float(r["latitude"]), float(r["longitude"])
        except (TypeError, ValueError):
            continue
        esc = lambda k: html.escape(str(r[k]))
        folium.Marker(
            [lat, lon], tooltip=f"Report ({esc('status')}): {esc('incident_type')}",
            icon=folium.Icon(color=STATUS_COLOUR.get(r["status"], "purple"), icon="exclamation-sign"),
            popup=folium.Popup(f"<b>COMMUNITY REPORT</b><br>ID: {esc('report_id')}<br>Type: {esc('incident_type')}<br>Area: {esc('area')}<br>"
                               f"Severity (self-reported): {esc('severity')}<br>Description: {esc('description')}<br>"
                               f"Status: {esc('status')}<br>Reported: {esc('reported_at')}", max_width=300)).add_to(cluster)
    if my_loc:
        folium.Circle([my_loc["lat"], my_loc["lon"]], radius=max(my_loc["acc"], 10), color="#2563eb", fill=True, fill_opacity=0.12).add_to(fmap)
        folium.CircleMarker([my_loc["lat"], my_loc["lon"]], radius=7, color="#ffffff", weight=2, fill=True,
                            fill_color="#2563eb", fill_opacity=1, tooltip="You are here").add_to(fmap)
        trail = st.session_state.get("gps_trail", [])
        if len(trail) > 1:
            folium.PolyLine([(a, b) for a, b, _ in trail], color="#2563eb", weight=3, opacity=0.7,
                            tooltip="Your trail (this session)").add_to(fmap)

    map_col, side_col = st.columns([3, 1])
    with map_col:
        st_folium(fmap, use_container_width=True, height=470, returned_objects=[])
    with side_col:
        st.markdown("**Legend**")
        st.markdown("🔴 Sim. index 70–100  \n🟠 40–69  \n🟢 0–39")
        st.markdown("Report pins: purple = unverified, teal = plausible, grey = not supported, green = resolved. Blue dot = you (GPS).")
        st.markdown("**Data status**")
        st.write("Weather: " + ("Live API" if w else "Off / unavailable"))
        st.write("Reports: live file feed")
        st.write("Risk pins: simulated")
        st.write("Traffic: simulated")
        st.write("Drain sensors: not connected")
        if my_loc:
            st.write(f"GPS accuracy: ±{my_loc['acc']:.0f} m")
            row, dist = eng.nearest(my_loc["lat"], my_loc["lon"], shown)
            if row is not None:
                st.info(f"Nearest report: **{row['incident_type']}** · {eng.fmt_distance(dist)} away (unverified).")
            hz, hd = eng.nearest(my_loc["lat"], my_loc["lon"], map_points)
            if hz is not None:
                st.caption(f"Nearest demo risk point: {hz['Location']} · {eng.fmt_distance(hd)}")

    # ---- Live incident feed ----
    st.markdown(f"#### Live report feed — {report_age_label.lower()}")
    if shown.empty:
        st.info("No reports in this time window.")
    else:
        feed = shown.assign(_t=pd.to_datetime(shown["reported_at"], errors="coerce", utc=True)).sort_values("_t", ascending=False)
        st.dataframe(feed[["reported_at", "incident_type", "area", "severity", "status"]].head(25),
                     use_container_width=True, hide_index=True)


live_fragment = st.fragment(live_panel, run_every=refresh_s) if refresh_s else st.fragment(live_panel)
with tab_live:
    live_fragment()


# --------------------------------------------------------------------------
# TAB 2 — simulation
# --------------------------------------------------------------------------
with tab_sim:
    st.markdown("### Failure chain")
    g = eng.build_graph(after)
    pos = {"Heavy rainfall": (0, 2), "Drain blockage": (0, 0), "Street flooding": (1.7, 1), "Road disruption": (3.4, 1),
           "Traffic congestion": (5.1, 1), "Emergency delay": (6.8, 1), "Power interruption": (3.4, -0.5)}
    fig, ax = plt.subplots(figsize=(13, 4.8))
    colors = [(0.95, 0.35 + 0.4 * (1 - after[n]), 0.18 + 0.25 * (1 - after[n])) for n in g.nodes]
    nx.draw_networkx_edges(g, pos, ax=ax, arrows=True, arrowsize=18, width=1.8, edge_color="#718096", connectionstyle="arc3,rad=0.04")
    nx.draw_networkx_nodes(g, pos, ax=ax, node_color=colors, node_size=3000, edgecolors="#ffffff", linewidths=2)
    nx.draw_networkx_labels(g, pos, labels={n: f"{n}\nIndex: {after[n] * 100:.0f}" for n in g.nodes}, ax=ax, font_size=8, font_weight="bold")
    ax.set_title("Illustrative dependency graph — redder nodes have higher simulated risk", fontsize=12, pad=12)
    ax.axis("off")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("### Risk before vs. after intervention")
    rows = [{"Event / system": n, "Affected location": eng.LOCATIONS[n], "Baseline index": round(baseline[n] * 100),
             "After intervention": round(after[n] * 100), "Change (index points)": round((after[n] - baseline[n]) * 100)}
            for n in baseline]
    st.dataframe(pd.DataFrame(rows).sort_values("Baseline index", ascending=False), use_container_width=True, hide_index=True)
    mb, ma = eng.worst_downstream(baseline), eng.worst_downstream(after)
    m1, m2, m3 = st.columns(3)
    m1.metric("Worst downstream · baseline", f"{mb * 100:.0f}/100")
    m2.metric("Worst downstream · intervention", f"{ma * 100:.0f}/100")
    m3.metric("Illustrative reduction", f"{(mb - ma) * 100:.0f} points", delta=f"{(mb - ma) * 100:.0f} points")

    st.markdown("### Which intervention helps most? (same scenario, all options)")
    ranking = eng.rank_interventions(rain_mm, blockage_pct, traffic_load, pressure)
    st.dataframe(ranking, use_container_width=True, hide_index=True)
    st.altair_chart(alt.Chart(ranking).mark_bar(color="#176b87").encode(
        y=alt.Y("Intervention:N", sort="x", title=None),
        x=alt.X("Worst downstream index:Q", scale=alt.Scale(domain=[0, 100])),
        tooltip=["Intervention", "Worst downstream index", "Reduction vs baseline (points)"]).properties(height=200),
        use_container_width=True)

    st.markdown("### First Domino reasoning")
    st.write(f"Between the two starting hazards, **{trigger}** is the current candidate "
             f"(impact score {impact[trigger]:.2f} vs {min(impact.values()):.2f}). The heuristic multiplies the starting hazard's index "
             "by 1 + the summed indices of everything downstream. It is a prioritisation aid, not proof of causality or a learned prediction.")
    st.markdown("### Recommended preventive actions")
    for title, desc in [
        ("1. Inspect and clear Drain D-04", "Best fit when blockage is high: remove the initiating drainage constraint before peak rainfall."),
        ("2. Pre-position pumps at Low point L-2", "Contingency if rainfall stays high or the drain cannot be cleared in time."),
        ("3. Prepare a diversion at Bridge Road", "Reduce exposure to the flooded segment and avoid pushing all vehicles onto one alternate road."),
        ("4. Notify the Community Clinic", "Confirm an alternate emergency access route; never rely on this prototype for dispatch."),
    ]:
        st.markdown(f"**{title}** — {desc}")


# --------------------------------------------------------------------------
# TAB 3 — reporting
# --------------------------------------------------------------------------
with tab_report:
    st.markdown("### Community incident reporting")
    st.caption("Reports are saved to incident_reports.csv on the machine running this app and appear on the live map within one refresh. "
               "They are unverified and are not sent to any authority.")
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))
    gps_loc = st.session_state.get("my_loc")
    with st.form("incident_report_form", clear_on_submit=True):
        incident_type = st.selectbox("Incident type", ["Street flooding / waterlogging", "Blocked drain", "Road disruption",
                                                       "Traffic congestion", "Power interruption", "Other hazard"])
        description = st.text_area("What did you observe?", placeholder="Describe what you saw. Avoid personal or sensitive information.", max_chars=500)
        severity = st.select_slider("Observed severity (self-reported)", options=list(eng.SEVERITY_WEIGHT), value="Moderate")
        area = st.text_input("Area / landmark", placeholder="e.g., near a market or junction")
        use_gps = st.checkbox("Use my tracked GPS location", value=bool(gps_loc), disabled=gps_loc is None,
                              help="Turn on device tracking in the sidebar first." if gps_loc is None else None)
        lc1, lc2 = st.columns(2)
        lat_in = lc1.number_input("Latitude", -90.0, 90.0, float(center_lat), format="%.6f")
        lon_in = lc2.number_input("Longitude", -180.0, 180.0, float(center_lon), format="%.6f")
        st.caption("Coordinates default to the area centre. Adjust only if you know the incident location.")
        if st.form_submit_button("Save incident report", type="primary"):
            if not description.strip() or not area.strip():
                st.error("Please add a short description and an area/landmark before saving.")
            else:
                lat, lon = (gps_loc["lat"], gps_loc["lon"]) if (use_gps and gps_loc) else (lat_in, lon_in)
                try:
                    rid = eng.save_incident(INCIDENT_FILE, incident_type, description, severity, lat, lon, area)
                    st.session_state["flash"] = f"Report {rid} saved locally as unverified. It has not been sent to any authority."
                    st.rerun()
                except OSError as exc:
                    st.error(f"Could not save the report locally: {exc}")

    st.markdown("#### All saved reports")
    reports_now = safe_load_incidents()
    if reports_now.empty:
        st.info("No community reports saved yet.")
    else:
        st.caption(f"{len(reports_now)} saved report(s).")
        st.dataframe(reports_now[["report_id", "reported_at", "incident_type", "area", "severity", "status"]]
                     .sort_values("reported_at", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("Download incident reports (CSV)", reports_now.to_csv(index=False).encode("utf-8"),
                           file_name="echomind_incident_reports.csv", mime="text/csv")
        with st.expander("Reviewer tools (demo — no authentication)"):
            st.caption("Anyone with access to this app can change a status. A real deployment needs authentication and an audit log.")
            types_by_id = reports_now.set_index("report_id")["incident_type"]
            rid_pick = st.selectbox("Report", reports_now["report_id"].tolist(), format_func=lambda i: f"{i} · {types_by_id.get(i, '')}")
            new_status = st.selectbox("New status", eng.STATUSES)
            if st.button("Update status"):
                if eng.update_status(INCIDENT_FILE, rid_pick, new_status):
                    st.session_state["flash"] = f"{rid_pick} marked: {new_status}"
                    st.rerun()


# --------------------------------------------------------------------------
# TAB 4 — limitations
# --------------------------------------------------------------------------
with tab_about:
    st.warning("""
- **What is live:** current weather and a ±24 h hourly rainfall series from Open-Meteo (model-based, at the area centre — not a street gauge), the community report file, and optional browser GPS for *your own* device.
- **What is not live:** drain status, traffic, road closures, and utility status are manual or simulated. No sensors are connected.
- Risk pins are illustrative points around the area centre, not verified infrastructure.
- Scores are **risk indices, not calibrated probabilities**. The model is hand-authored; no ML model is trained.
- Weather does not confirm flooding. Reports are self-reported and unverified; status changes are not authenticated.
- Intervention effects are assumed by the rules; the comparison is not evidence of real-world prevention.
- GPS is used only in your browser session and is never written to disk unless you submit a report using it.
- Use only for a hackathon demonstration — not for public alerts, emergency dispatch, or infrastructure decisions.
""")
    with st.expander("What would make this a genuine predictive system?"):
        st.write("Collect timestamped rainfall, drain status, flood reports, road closures and response-time outcomes from permitted, reliable sources. "
                 "Define a target (e.g. road segment floods within the next hour), split by time/location to avoid leakage, compare against simple baselines, "
                 "calibrate probabilities, measure false alarms and misses, and validate with local experts before considering scikit-learn models.")

st.caption("EchoMind | BEST OF FOUR | Live tracking build")
