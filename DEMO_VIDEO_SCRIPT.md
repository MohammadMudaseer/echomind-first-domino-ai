# EchoMind — 2-minute demo video pack

**Project:** EchoMind — First Domino AI  
**Team:** BEST OF FOUR  
**Format:** 16:9 screen recording, 1080p if available, narration + captions  
**Important:** Show the real running Streamlit app. Do not present simulated map pins or scenario indices as verified city data.

## Timed storyboard and narration

### 00:00–00:10 — Hook
**Screen:** Title card, then open EchoMind dashboard.  
**Narration:** “A blocked drain can become more than a drainage problem. During heavy rain, it can trigger street flooding, road disruption, congestion, and delays for emergency vehicles. EchoMind helps us explore that chain before the impacts spread.”

### 00:10–00:28 — Set the scenario
**Screen:** Sidebar controls. Set rainfall around 75 mm, blockage around 85%, traffic load around 65%.  
**Narration:** “This hackathon prototype models a neighborhood with three scenario inputs: rainfall, drain blockage, and traffic load. The scores are transparent, rule-based risk indices—not calibrated probabilities.”

### 00:28–00:43 — Show the map and weather
**Screen:** Scroll to Location & Weather Monitoring. Select Warangal. Show weather values if the API responds; otherwise show the unavailable message. Point to the legend and simulated pins.  
**Narration:** “The map uses OpenStreetMap tiles through Folium. Current weather is requested from Open-Meteo when internet access is available. The colored risk pins are illustrative sample locations, not real flood detections.”

### 00:43–01:02 — Report an incident
**Screen:** Expand “Report a local incident.” Enter a sample blocked-drain report, description, severity, landmark, and coordinates. Save it. Show the purple pin and the submitted report table.  
**Narration:** “A user can submit a flood or blocked-drain observation with a location. Reports are stored locally on the machine running the app and appear as purple map pins. Each is clearly marked unverified; the prototype does not dispatch crews or send reports to government systems.”

### 01:02–01:22 — Reveal the cascade
**Screen:** Show failure-chain graph and risk table.  
**Narration:** “The dependency graph connects rainfall and drainage blockage to flooding, then road disruption, traffic congestion, emergency delay, and possible power interruption. EchoMind highlights a candidate starting hazard using a simple downstream-impact heuristic.”

### 01:22–01:42 — Compare interventions
**Screen:** Select “Clear the critical drain,” then compare baseline and intervention indices. Optionally switch to “Reroute traffic early.”  
**Narration:** “We can test an intervention, such as clearing the critical drain, and compare the model’s before-and-after indices. This helps structure a planning discussion, but the simulated reduction is not evidence that a real intervention will achieve the same result.”

### 01:42–02:00 — Close honestly
**Screen:** Show recommendations and limitations. Finish on project title and team name.  
**Narration:** “EchoMind’s goal is to help teams ask an earlier question: what is the first domino, and what could we do before it falls? Today it is a simulation prototype. The next step is validation with trusted local incident data, drainage information, and city partners. EchoMind — First Domino AI, by BEST OF FOUR.”

## Recording checklist
- Run `streamlit run app.py` and record the browser, not a mockup.
- Use a clean browser window at 100% zoom; hide personal notifications.
- Test the internet connection for optional live weather before recording.
- Submit one clearly fictional demo report; do not enter real people's personal data.
- Keep the “simulated” and “unverified” labels visible when showing the map.
- If weather fails, narrate the fallback honestly—do not fake live values.
- Export MP4, 1920×1080 if possible, 30 fps; keep the video near 2 minutes.

## v2 additions (live tracking) — optional 30 s insert after the map segment
**Screen:** Live monitor tab: status pills, rain chart with red "now" line, toggle GPS, show blue dot; submit a report and watch it appear.  
**Narration:** “Weather is now live and refreshes automatically. The rainfall input can drive the simulation, and we can track our own location and file a report from exactly where we stand. Drain status and traffic are still simulated — no sensors are connected.”
