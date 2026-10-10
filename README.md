# EchoMind — First Domino AI

A Streamlit hackathon prototype that simulates how an urban hazard can cascade through connected systems and compares illustrative preventive interventions.

## Features
- Adjustable rainfall, drain blockage, and starting traffic load.
- NetworkX dependency graph and rule-based risk indices.
- Baseline vs. intervention comparison.
- Interactive Folium map for Warangal, Hyderabad, or New Delhi.
- Optional current weather from Open-Meteo when internet access is available.
- Community incident reporting with location coordinates, severity, and description.
- Reports stored locally in `incident_reports.csv`, displayed as unverified purple pins, and downloadable as CSV.

## Run locally
Use Python 3.10 or newer.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Demo flow
1. Set rainfall to around 75 mm, blockage to 85%, and traffic to 65%.
2. Review the map and weather status.
3. Submit a clearly fictional incident report and show its purple pin.
4. Inspect the dependency graph and baseline risks.
5. Select “Clear the critical drain” and compare indices.

See `DEMO_VIDEO_SCRIPT.md` and `DEMO_VIDEO_CAPTIONS.srt` for the timed video plan and captions.

## Data and safety limitations
This is a demonstration, not an operational warning system. The graph and scores are rule-based and illustrative—not calibrated probabilities or verified predictions. Map risk pins are sample points around the selected city center. Weather does not verify flooding. Incident reports are user-submitted and unverified, saved only to the local app machine, and are not transmitted to authorities. Do not use the prototype for emergency dispatch or infrastructure decisions.
