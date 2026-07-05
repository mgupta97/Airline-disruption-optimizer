# Airline Disruption Recovery Optimizer V2 Methodology

## Objective

This project models airline disruption recovery as a decision-support problem using machine learning, simulation, passenger-impact modeling, aircraft rotation logic, and robust scenario analysis.

The V2 upgrade expands the original project from delay prediction and disruption simulation into a more realistic airline recovery system.

## V2 Workflow

1. Simulate an airport disruption.
2. Optimize recovery actions.
3. Compare recovery strategies against baselines.
4. Estimate passenger impact.
5. Evaluate passenger-aware recovery strategies.
6. Model aircraft rotation delay propagation.
7. Test robust recovery under multiple weather scenarios.
8. Generate reports, figures, and dashboard views.

## Core Modules

| Module | Purpose |
|---|---|
| Disruption Simulation | Simulates primary and downstream delay propagation |
| Recovery Optimization | Selects recovery actions using constrained optimization |
| Recovery Strategy Benchmark | Compares optimized recovery against baseline rules |
| Passenger Impact Simulation | Estimates passengers affected, missed-connection risk, and passenger disruption cost |
| Passenger-Aware Recovery | Compares strategies using operational and customer-impact metrics |
| Aircraft Rotation Recovery | Estimates downstream risk from aircraft rotation chains |
| Robust Weather Recovery | Tests recovery strategies across multiple weather scenarios |
| V2 Dashboard | Presents all V2 outputs in an interactive Streamlit interface |

## Recovery Benchmarking

The project compares the optimizer against practical baselines:

- No recovery
- Random recovery
- Highest-delay-first recovery
- Primary-impact-first recovery
- Network-criticality-first recovery
- Hybrid delay and network recovery
- Optimized recovery plan

This makes the optimizer more credible because it is evaluated against simple rules that could be used in real operations.

## Passenger Impact Modeling

Passenger impact is estimated using proxy features:

- Estimated passengers affected
- Route frequency
- Airport hub exposure
- Delay severity
- Connection-bank timing
- Missed-connection risk
- Passenger disruption cost proxy

This helps evaluate recovery actions beyond delay minutes alone.

## Aircraft Rotation Propagation

The aircraft rotation module links flights by aircraft identifier and flight date. It estimates:

- Ground time between aircraft legs
- Turnaround slack
- Downstream delay pressure
- Rotation risk score
- Top aircraft chains by delay propagation risk

This improves realism because a delayed inbound aircraft can delay later flights in the same aircraft chain.

## Robust Weather Recovery

The robust optimizer evaluates recovery strategies across multiple weather scenarios:

- ORD thunderstorm ground delay
- DEN winter storm
- ATL ground stop
- Northeast severe weather
- West Coast low visibility
- Systemwide moderate disruption

Each strategy is scored by:

- Expected passenger cost reduction
- Worst-case passenger cost reduction
- Expected delay recovery
- Worst-case delay recovery
- Scenario variability
- Passenger protection

## Limitations

This is a research and analytics prototype. It does not yet include:

- Real passenger itineraries
- Crew legality constraints
- Gate assignment
- Maintenance constraints
- Aircraft swap feasibility
- Live weather feeds
- Full multi-day recovery
- Integrated aircraft-crew-passenger mixed-integer optimization

## Future Improvements

Potential future upgrades include:

- Crew recovery optimization
- Gate reassignment optimization
- Real-time weather API integration
- Passenger itinerary simulation
- Aircraft swap feasibility
- Stochastic optimization
- Multi-day disruption recovery
- Full time-space network recovery model
