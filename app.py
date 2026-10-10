import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="EchoMind | First Domino AI", page_icon="🌧️", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
.hero {padding: 1.2rem 1.4rem; border-radius: 18px; background: linear-gradient(120deg,#10233f,#176b87); color: white; margin-bottom: 1rem;}
.hero h1 {color:white; margin:0;}
.hero p {color:#d9eef7; margin:.4rem 0 0 0;}
.small-note {color:#64748b; font-size:.88rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🌧️ EchoMind — First Domino AI</h1><p>Simulate cascading neighborhood failures. Find the earliest high-impact trigger and test preventive actions.</p></div>', unsafe_allow_html=True)
st.caption("HACKATHON PROTOTYPE • SIMULATED DATA ONLY • NOT AN OPERATIONAL WARNING SYSTEM")

# The graph is a simplified causal/dependency model, not a calibrated city model.
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
BASE_SEVERITY = {
    "Heavy rainfall": 0.0, "Drain blockage": 0.0, "Street flooding": 0.0,
    "Road disruption": 0.0, "Traffic congestion": 0.0,
    "Emergency delay": 0.0, "Power interruption": 0.0
}

def clamp(x):
    return max(0.0, min(1.0, float(x)))

def simulate(rain_mm, blockage_pct, traffic_load, intervention):
    """Transparent scenario rules. Scores are illustrative indices, not probabilities."""
    rain = clamp((rain_mm - 10) / 70)
    blockage = clamp(blockage_pct / 100)
    if intervention == "Clear the critical drain":
        blockage *= 0.18
    elif intervention == "Deploy temporary water pumps":
        rain_effect = rain * 0.55
    else:
        rain_effect = rain
    if intervention != "Deploy temporary water pumps":
        rain_effect = rain

    flood = clamp(0.62 * rain_effect + 0.58 * blockage + 0.12 * rain_effect * blockage)
    if intervention == "Protect the critical road":
        road_protection = 0.42
    else:
        road_protection = 1.0
    road = clamp(flood * 0.88 * road_protection)
    traffic = clamp((0.52 * road + 0.48 * clamp(traffic_load / 100)) * (0.72 if intervention == "Reroute traffic early" else 1.0))
    emergency = clamp(0.68 * traffic + 0.42 * road)
    power = clamp(flood * 0.58)
    scores = {
        "Heavy rainfall": rain,
        "Drain blockage": blockage,
        "Street flooding": flood,
        "Road disruption": road,
        "Traffic congestion": traffic,
        "Emergency delay": emergency,
        "Power interruption": power,
    }
    return scores

def build_graph(scores):
    g = nx.DiGraph()
    for n, (kind, desc) in NODE_INFO.items():
        g.add_node(n, kind=kind, description=desc, risk=scores[n])
    g.add_edges_from(EDGES)
    return g

def draw_graph(scores):
    g = build_graph(scores)
    pos = {
        "Heavy rainfall": (0, 2), "Drain blockage": (0, 0),
        "Street flooding": (1.7, 1), "Road disruption": (3.4, 1),
        "Traffic congestion": (5.1, 1), "Emergency delay": (6.8, 1),
        "Power interruption": (3.4, -0.5),
    }
    fig, ax = plt.subplots(figsize=(13, 4.8))
    colors = []
    for n in g.nodes:
        r = scores[n]
        colors.append((0.95, 0.35 + 0.4*(1-r), 0.18 + 0.25*(1-r)))
    nx.draw_networkx_edges(g, pos, ax=ax, arrows=True, arrowsize=18, width=1.8, edge_color="#718096", connectionstyle="arc3,rad=0.04")
    nx.draw_networkx_nodes(g, pos, ax=ax, node_color=colors, node_size=3000, edgecolors="#ffffff", linewidths=2)
    labels = {n: f"{n}\nRisk index: {scores[n]*100:.0f}" for n in g.nodes}
    nx.draw_networkx_labels(g, pos, labels=labels, ax=ax, font_size=8, font_weight="bold")
    ax.set_title("Illustrative dependency graph — redder nodes have higher simulated risk", fontsize=12, pad=12)
    ax.axis("off")
    fig.tight_layout()
    return fig

def top_trigger(scores):
    # A simple impact proxy: downstream reach weighted by current risk.
    g = build_graph(scores)
    candidates = ["Heavy rainfall", "Drain blockage"]
    impact = {}
    for n in candidates:
        downstream = nx.descendants(g, n)
        impact[n] = scores[n] * (1 + sum(scores[d] for d in downstream))
    return max(impact, key=impact.get), impact

with st.sidebar:
    st.header("Scenario controls")
    rain_mm = st.slider("Rainfall (mm / scenario period)", 0, 100, 75, 5)
    blockage_pct = st.slider("Drain blockage (%)", 0, 100, 85, 5)
    traffic_load = st.slider("Starting traffic load (%)", 0, 100, 65, 5)
    intervention = st.selectbox("Test one intervention", [
        "No intervention (baseline)",
        "Clear the critical drain",
        "Deploy temporary water pumps",
        "Protect the critical road",
        "Reroute traffic early",
    ])
    st.info("Try 75–90 mm rainfall and 80–100% blockage, then change the intervention.")

baseline = simulate(rain_mm, blockage_pct, traffic_load, "No intervention (baseline)")
after = simulate(rain_mm, blockage_pct, traffic_load, intervention)
trigger, impact = top_trigger(baseline)

st.subheader("Neighborhood status")
c1,c2,c3,c4 = st.columns(4)
c1.metric("Rainfall input", f"{rain_mm} mm")
c2.metric("Drain blockage", f"{blockage_pct}%")
c3.metric("Highest baseline risk", f"{max(baseline.values())*100:.0f}/100")
c4.metric("First Domino candidate", trigger)

st.markdown("### Failure chain")
st.pyplot(draw_graph(after), use_container_width=True)

st.markdown("### Risk before vs. after intervention")
rows = []
for n in baseline:
    rows.append({
        "Event / system": n,
        "Affected location": LOCATIONS[n],
        "Baseline index": round(baseline[n]*100),
        "After intervention": round(after[n]*100),
        "Change (index points)": round((after[n]-baseline[n])*100),
        "Interpretation": "Higher simulated index means more concern in this toy model."
    })
df = pd.DataFrame(rows).sort_values("Baseline index", ascending=False)
st.dataframe(df, use_container_width=True, hide_index=True)

max_before = max(baseline["Street flooding"], baseline["Road disruption"], baseline["Traffic congestion"], baseline["Emergency delay"])
max_after = max(after["Street flooding"], after["Road disruption"], after["Traffic congestion"], after["Emergency delay"])
delta = max_before - max_after
m1,m2,m3 = st.columns(3)
m1.metric("Worst downstream index · baseline", f"{max_before*100:.0f}/100")
m2.metric("Worst downstream index · intervention", f"{max_after*100:.0f}/100")
m3.metric("Illustrative reduction", f"{delta*100:.0f} points", delta=f"{delta*100:.0f} points")

st.markdown("### First Domino reasoning")
st.write(f"Among the two starting hazards, **{trigger}** is the current candidate under the prototype's simple impact heuristic. The heuristic combines the starting hazard's index with the risk scores of its downstream descendants. It is a prioritization aid, not proof of causality or a learned prediction.")
st.markdown("### Recommended preventive actions")
recommendations = [
    ("1. Inspect and clear Drain D-04", "Best fit when blockage is high: reduce the initiating drainage constraint before peak rainfall."),
    ("2. Pre-position pumps at Low point L-2", "Useful as a contingency if rainfall remains high or the drain cannot be cleared in time."),
    ("3. Prepare a diversion at Bridge Road", "Reduce exposure to the flooded segment and avoid pushing all vehicles onto one alternate road."),
    ("4. Notify the Community Clinic", "Confirm an alternate emergency access route; do not rely on this prototype for dispatch decisions."),
]
for title, desc in recommendations:
    st.markdown(f"**{title}** — {desc}")

st.markdown("---")
st.markdown("### Confidence, assumptions & limitations")
st.warning("""
- All values and locations are fictional and simulated. The displayed 0–100 scores are **risk indices, not calibrated probabilities**.
- This version uses hand-authored equations and a small dependency graph. It does not contain a trained predictive ML model.
- It omits terrain, drainage capacity measurements, rainfall forecasts, road geometry, human behavior, and uncertainty calibration.
- An intervention's effect is assumed by the scenario rules; the comparison is not evidence of real-world prevention.
- Use only for a hackathon demonstration, not public alerts, emergency dispatch, or infrastructure decisions.
""")
with st.expander("What would make this a genuine predictive system?"):
    st.write("""
    Collect timestamped rainfall, drain status, flood reports, road closures, and response-time outcomes from a permitted and reliable source. Define a target (for example, whether a road segment floods within the next hour), split data by time/location to avoid leakage, compare against simple baselines, calibrate probabilities, evaluate false alarms and missed events, and validate with local domain experts. Only then consider a model such as scikit-learn RandomForest or HistGradientBoosting.
    """)

st.caption("EchoMind | BEST OF FOUR | Prototype build")
