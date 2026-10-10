# EchoMind — First Domino AI (v2 · live tracking build)

A Streamlit hackathon prototype that tracks live rain and community reports, simulates how an urban hazard cascades through connected systems, and compares illustrative preventive interventions.

## What's new in v2
**Live tracking**
- 📡 **Live rainfall feed** (Open-Meteo): current conditions plus a past-24 h / next-24 h hourly rain chart with a "now" marker.
- 🔄 **Auto-refresh** live panel (30 s / 1 min / 5 min / off) using Streamlit fragments — no full-page flicker.
- 🌧️ **Simulation driven by live rain**: rainfall input = observed past 3 h + forecast next 3 h; the model recalculates automatically when new data arrives.
- 📍 **Device tracking (optional)**: browser GPS shows "you are here", accuracy ring, session trail, and distance to the nearest report / demo risk point. One tick to use your GPS position in a report.
- 🗺️ **Live report feed**: new reports appear on the map and table automatically, with time filters, clustering, and status-coloured pins.
- 🚦 Status banner (LOW / ELEVATED / HIGH) and a forecast heads-up when ≥10 mm is expected in the next 6 h.

**v3 additions**
- ⏱️ **Hourly risk forecast** — "when does the first domino fall?": illustrative index per hour from forecast rain, baseline vs your selected intervention, with first-ELEVATED / first-HIGH times.
- 📈 **Session trend** that grows with each auto-refresh (rain input, worst index, report pressure).
- 🌍 **Compare all areas live** (Warangal / Hyderabad / New Delhi) on rainfall.
- 🔎 **Evidence check**: compares model concern with recent community reports and flags mismatches.
- 📄 **Downloadable situation report** (Markdown) with inputs, status, first-crossing times, intervention effect and open reports.
- 🧪 **Demo helpers**: load/remove 4 clearly-labelled fictional reports in one click.
- 17 unit tests (was 13).

**Model & product improvements**
- Cleaner, unit-tested engine (`engine.py`); fixed convoluted pump-intervention logic.
- Rank **all** interventions against the same scenario (table + chart).
- "Report pressure" indicator; optional blending of unresolved recent reports into the flood index.
- Reports now have IDs, atomic writes, automatic upgrade of old CSV files, and reviewer statuses (Unverified → Plausible / Not supported / Resolved).
- Tabbed layout: Live monitor · Simulation · Report · Limitations. XSS-safe map popups.

## Run locally
Python 3.10+.
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```
Run tests: `python -m unittest discover -s tests -v`

GPS needs `streamlit-js-eval` (in requirements) and a secure context: `localhost` or HTTPS. Browsers block geolocation on plain-HTTP remote hosts.

## Demo flow (live version)
1. Leave "Live rainfall feed" and "Drive the simulation" ticked; show the status pills and live chart.
2. Tick "Track my device location", allow GPS, show the blue dot and trail.
3. Submit a clearly fictional report (tick "Use my tracked GPS location"); watch it appear on the map.
4. Open a second browser tab, submit another report — the first tab picks it up at the next refresh.
5. In Simulation, show the failure chain and the intervention ranking; pick "Clear the critical drain".
6. If it's dry that day, untick "Drive from live rainfall" and set 75 mm to demonstrate a heavy-rain scenario.

## Data and safety limitations
Demonstration only — not an operational warning system. Live data: Open-Meteo weather (model-based at the area centre, not a street gauge) and the local report file. Drain status, traffic and utilities are manual or simulated; no sensors are connected. Scores are illustrative indices, not calibrated probabilities. Reports are unverified, stored on the app machine, shared only with users of that same app instance, and never sent to authorities. Reviewer status changes are unauthenticated. Do not use for emergency dispatch or infrastructure decisions.
