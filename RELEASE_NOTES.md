# EchoMind release notes — v2 live tracking build

## v3 additions
- Hourly risk forecast with first-ELEVATED/HIGH times, session trend, multi-area live comparison, evidence check, downloadable situation report, demo-report helpers, +4 tests.

## Added (v2)
- Live Open-Meteo rainfall: current conditions + 48 h hourly series; chart with now-marker.
- Auto-refreshing live panel (fragment) with configurable interval; full re-run only when live inputs change.
- Simulation can be driven by live rainfall (past 3 h + next 3 h).
- Optional browser-GPS device tracking: position, accuracy, trail, nearest report/risk point, GPS-filled reports.
- Report IDs, statuses/reviewer tools, time-window filter, marker clustering, report-pressure indicator, optional blending into the flood index.
- All-interventions ranking, risk-band banner, forecast heads-up.
- `engine.py` + unit tests (13) for model, weather parsing, geo maths, incident store.

## Changed / fixed
- Pump-intervention logic simplified (behaviour unchanged).
- Incident CSV writes are atomic; legacy CSVs are migrated automatically.
- Map popup text HTML-escaped.
- Layout split into tabs.

## Limitations
- Weather is model data at the area centre; it does not confirm flooding.
- No drain sensors, live traffic feed, authentication, or moderation workflow.
- Reports are local to the machine running the app.
- GPS requires browser permission and localhost/HTTPS. The GPS and Open-Meteo calls could not be exercised in the build sandbox (no network); engine logic is unit-tested, UI should be smoke-tested on your machine.
