# EchoMind — First Domino AI

A low-cost hackathon MVP that demonstrates cascading urban risks with simulated data.

## 1. Requirements
- Python 3.10 or newer
- Internet connection for the initial package installation
- No API keys, sensors, database, or cloud account required

## 2. Run locally
```bash
# Windows PowerShell or Command Prompt
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

On macOS/Linux, activate with:
```bash
source .venv/bin/activate
```
Streamlit prints a local URL, usually http://localhost:8501.

## 3. Demo
1. Leave the default high rainfall and drain blockage.
2. Explain the graph: rainfall and blockage contribute to street flooding; flooding affects a road, traffic, emergency access, and a utility point.
3. Note the risk indices and affected locations.
4. Change the intervention to **Clear the critical drain**.
5. Compare the baseline and intervention indices.
6. Try **Protect the critical road** or **Reroute traffic early** to show different intervention points.
7. Read the limitations aloud: this is a transparent rule-based simulation, not a trained forecast.

## 4. Folder structure
```text
echomind_first_domino/
├── app.py
├── requirements.txt
├── README.md
├── ARCHITECTURE.md
├── DEMO_SCRIPT.md
├── PRESENTATION.md
└── RESEARCH_NOTES.md
```

## 5. Technical design
- Streamlit: controls, dashboard, data table, metrics
- Python: scenario rules and intervention comparison
- NetworkX: directed dependency graph and downstream reach
- Matplotlib: graph visualization
- pandas: before/after table
- SQLite: intentionally omitted; there is no persistent data in the MVP
- scikit-learn: intentionally omitted until a real labeled dataset exists

## 6. Score interpretation
The 0–100 display is a normalized **illustrative risk index**, not a probability, measured confidence, or calibrated real-world risk. The intervention comparison reflects assumptions coded into the simulator.

## 7. Known limitations
- Fictional neighborhood and dependencies
- No geospatial map or actual road routing
- No real-time data, sensors, forecasts, or alerts
- No calibrated probability estimates
- No trained machine-learning model
- Simplified linear/interaction formulas do not represent fluid dynamics or actual drainage hydraulics
