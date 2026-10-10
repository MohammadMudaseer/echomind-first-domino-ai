# 7-slide presentation outline

## Slide 1 — EchoMind: First Domino AI
- Team BEST OF FOUR; Open Innovation
- Predict and explain possible cascades, then compare preventive actions

## Slide 2 — The problem
- Urban systems depend on one another
- A drainage issue can become a transport and emergency-access issue
- Single-hazard monitoring may not communicate downstream impacts

## Slide 3 — Our solution
- Model dependencies as a directed graph
- Score scenario risk transparently
- Identify a high-impact starting hazard
- Compare interventions before and after

## Slide 4 — Live MVP
- Scenario controls
- Failure graph
- Affected locations and index table
- Intervention comparison and recommended actions

## Slide 5 — Differentiation
- Explainable chain, not only a hazard score
- “First Domino” ranks candidate upstream hazards by downstream reach and current simulated risk
- Intervention-aware before/after scenario
- Human-readable reasons and explicit uncertainty/limitations

## Slide 6 — Technical feasibility and responsible AI
- Streamlit, Python, NetworkX, pandas, Matplotlib
- Simulated data, no API keys
- Rule-based baseline; no unsupported ML claims
- Future: validated local data, calibrated models, expert review

## Slide 7 — Impact, roadmap, ask
- Start with one neighborhood and one cascade
- Expand only after validation
- Ask: feedback on local data access, realistic dependencies, and evaluation criteria
