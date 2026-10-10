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

## Future validated architecture
Permitted data ingestion → quality checks and timestamp alignment → spatial/dependency graph → baseline model and ML model → calibration and uncertainty evaluation → human-reviewed recommendations → monitoring and audit log. Keep the rule-based baseline for comparison. No automated public warnings until validation and operational governance are in place.
