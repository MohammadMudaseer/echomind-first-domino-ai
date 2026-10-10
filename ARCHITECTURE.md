# EchoMind architecture

```text
┌──────────────────────────────┐
│ Streamlit scenario controls  │
│ rainfall / blockage / traffic│
│ intervention selection       │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Rule-based scenario engine   │
│ transparent illustrative     │
│ equations; scores 0–1         │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ NetworkX dependency graph    │
│ hazards → impacts → services │
│ downstream reach heuristic   │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Comparison and explanation   │
│ baseline vs intervention     │
│ risk table / recommendations │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Streamlit dashboard          │
│ graph / metrics / limitations│
└──────────────────────────────┘
```

## v2 live layer
```text
Open-Meteo (60 s cache) ─┐
Incident CSV (live read) ├─► live fragment (auto-refresh) ──► map / chart / feed
Browser GPS (optional)  ─┘            │
                                      └─ data signature changed? → full re-run → engine.simulate()
```
`engine.py` holds the pure logic (model, weather parsing, haversine, incident store); `app.py` is UI only.

## Future validated architecture
Permitted data ingestion → quality checks and timestamp alignment → spatial/dependency graph → baseline model and ML model → calibration and uncertainty evaluation → human-reviewed recommendations → monitoring and audit log. Keep the rule-based baseline for comparison. No automated public warnings until validation and operational governance are in place.
