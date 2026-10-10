# EchoMind release notes — incident reporting build

## Included
- Interactive Folium map centered on Warangal, Hyderabad, or New Delhi.
- Optional current weather request from Open-Meteo (requires internet access).
- Scenario controls and rule-based cascading-risk graph.
- Before/after intervention comparison.
- Community incident form for flooding, blocked drains, road disruption, traffic congestion, power interruption, or other hazards.
- Local CSV persistence in `incident_reports.csv`; user-submitted reports appear as purple map pins and in a table.
- CSV download for submitted reports.
- Demo video script, storyboard, recording checklist, and SRT captions.

## Important behavior and limitations
- Reports are saved to the local filesystem of the machine running Streamlit. They are not shared across users, uploaded to a server, or sent to authorities.
- Reports are unverified and should be reviewed by a human before any operational use.
- Map risk pins are illustrative points around the selected city center, not verified infrastructure locations.
- Weather is sourced from Open-Meteo when reachable; weather data does not confirm street flooding or drain blockage.
- The cascade model is hand-authored and illustrative. Scores are not calibrated probabilities, and the project is not an emergency alert or dispatch system.
- No GPS auto-detection, drain sensors, live traffic feed, public incident feed, authentication, or moderation workflow is included.
