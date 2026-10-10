# Related systems and differentiation notes

These are useful starting points for desk research. Verify current capabilities and licensing from the official pages before citing specifics in a judged presentation. EchoMind should not claim that cascading-risk analysis or flood simulation is new.

## Comparable areas / examples

1. **FEMA Hazus** — https://www.fema.gov/flood-maps/products-tools/hazus  
   Hazus is a risk-modeling methodology/toolset for estimating potential losses from hazards. It is broader and more formal than this small interactive prototype.

2. **Delft-FEWS** — https://www.deltares.nl/en/software-and-data/products/delft-fews  
   A flood forecasting and warning system framework used to integrate data and forecasting workflows. It is not the same as this toy graph simulator.

3. **Copernicus Emergency Management Service** — https://emergency.copernicus.eu/  
   Provides mapping and geospatial information for emergencies. Relevant to emergency awareness and impact assessment.

4. **UNDRR / disaster risk reduction resources** — https://www.undrr.org/  
   Useful background for multi-hazard risk, early warning, and disaster-risk governance.

5. **NetworkX** — https://networkx.org/  
   Python library for graphs and networks. It is a technical building block, not itself a prediction system.

6. **Streamlit** — https://streamlit.io/  
   Python framework for interactive data apps, suitable for rapid prototyping.

## How to frame the differentiation honestly

Do not say: “No one has ever done this before,” “we predict disasters accurately,” or “our AI prevents floods.”

Say instead:
> “EchoMind is a hackathon-scale, explainable cascade-risk prototype. Its specific contribution is combining an upstream ‘First Domino’ prioritization heuristic, an explicit dependency graph, and an intervention-aware before/after comparison in one lightweight dashboard. These are our design choices, not a claim that the underlying concepts are globally unprecedented.”

## Practical feature differentiation candidates

- **First Domino ranking:** rank candidate initial hazards using their simulated risk and weighted downstream reach.
- **Intervention comparison:** compare one intervention at a time against the same scenario baseline.
- **Explainable paths:** show the chain from initiating hazard to affected service.
- **Resource-aware actions:** later, rank actions by estimated cost, lead time, and benefit using locally validated data.
- **Uncertainty display:** distinguish observed data, assumptions, and model output.
- **Equity/accessibility check:** later, track whether a cascade affects clinics, schools, or vulnerable communities.

The current MVP implements the graph, heuristic, and intervention comparison in a simplified form. It does not implement live data, geographic routing, cost optimization, equity analysis, or calibrated uncertainty.

## Honest ML roadmap
A trained model requires labeled historical examples. For instance, a row might contain rainfall intensity, drain blockage, recent water level, and road context, with a label such as “road flooded within 60 minutes.” Use a time-aware train/test split and compare a simple baseline against scikit-learn models. Evaluate precision/recall, false alarms, missed events, calibration, and performance across locations. Do not use synthetic labels as evidence of real-world accuracy.
