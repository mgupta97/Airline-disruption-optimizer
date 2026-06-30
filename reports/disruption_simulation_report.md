# Airport Disruption Simulation Report

## Scenario

- Airport disrupted: DEN
- Date: 2025-01-02
- Disruption window: 8:00-14:00
- Primary added delay: 90 minutes
- Propagation window: 6 hours

## Impact Summary

- Primary impacted flights: 357
- Downstream impacted flights: 5,867
- Total impacted flights: 6,224
- Baseline total positive delay: 80,284.00 minutes
- Simulated total positive delay: 302,982.00 minutes
- Total delay increase: 222,698.00 minutes
- Average delay increase per impacted flight: 35.78 minutes

## Impact by Stage

| scenario_stage             |   impacted_flights |   total_added_delay |   avg_added_delay |   total_delay_increase |
|:---------------------------|-------------------:|--------------------:|------------------:|-----------------------:|
| downstream_propagation     |               5867 |              190568 |           32.4813 |                 190568 |
| primary_airport_disruption |                357 |               32130 |           90      |                  32130 |

## Top Routes Affected

| route      |   impacted_flights |   total_delay_increase |   avg_delay_increase |
|:-----------|-------------------:|-----------------------:|---------------------:|
| DEN -> PHX |                  9 |                    810 |                   90 |
| DEN -> SLC |                  8 |                    720 |                   90 |
| LAX -> SFO |                 12 |                    672 |                   56 |
| PHX -> DEN |                 11 |                    660 |                   60 |
| DEN -> BOS |                  7 |                    630 |                   90 |
| DEN -> LAX |                  7 |                    630 |                   90 |
| DEN -> DFW |                  7 |                    630 |                   90 |
| LAX -> LAS |                 10 |                    560 |                   56 |
| DEN -> SAN |                  6 |                    540 |                   90 |
| DEN -> BNA |                  6 |                    540 |                   90 |
| DEN -> SEA |                  6 |                    540 |                   90 |
| DEN -> SFO |                  6 |                    540 |                   90 |
| LAX -> PHX |                  9 |                    504 |                   56 |
| PHX -> SEA |                  8 |                    480 |                   60 |
| PHX -> LAX |                  8 |                    480 |                   60 |
| SFO -> LAX |                 10 |                    480 |                   48 |
| DEN -> DAL |                  5 |                    450 |                   90 |
| DEN -> COS |                  5 |                    450 |                   90 |
| DEN -> ASE |                  5 |                    450 |                   90 |
| DEN -> AUS |                  5 |                    450 |                   90 |

## Interpretation

This simulation approximates how a localized airport disruption can create both direct delays and downstream propagation. The primary disruption affects departures from the disrupted airport during the selected time window. Downstream propagation is estimated using delayed inbound pressure at connected destination airports. Later optimization steps will use this simulated impact to test recovery decisions such as delaying, prioritizing, or canceling flights.
