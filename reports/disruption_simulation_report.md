# Airport Disruption Simulation Report

## Scenario

- Airport disrupted: DEN
- Date: 2025-01-02
- Disruption window: 7:00-16:00
- Primary added delay: 120 minutes
- Propagation window: 8 hours

## Impact Summary

- Primary impacted flights: 478
- Downstream impacted flights: 6,150
- Total impacted flights: 6,628
- Baseline total positive delay: 100,735.00 minutes
- Simulated total positive delay: 422,787.00 minutes
- Total delay increase: 322,052.00 minutes
- Average delay increase per impacted flight: 48.59 minutes

## Impact by Stage

| scenario_stage             |   impacted_flights |   total_added_delay |   avg_added_delay |   total_delay_increase |
|:---------------------------|-------------------:|--------------------:|------------------:|-----------------------:|
| downstream_propagation     |               6150 |              264692 |           43.0393 |                 264692 |
| primary_airport_disruption |                478 |               57360 |          120      |                  57360 |

## Top Routes Affected

| route      |   impacted_flights |   total_delay_increase |   avg_delay_increase |
|:-----------|-------------------:|-----------------------:|---------------------:|
| DEN -> PHX |                 14 |                   1680 |                  120 |
| DEN -> DFW |                 11 |                   1320 |                  120 |
| DEN -> SLC |                 10 |                   1200 |                  120 |
| DEN -> LAX |                 10 |                   1200 |                  120 |
| DEN -> LAS |                 10 |                   1200 |                  120 |
| DEN -> SFO |                  9 |                   1080 |                  120 |
| DEN -> SAN |                  9 |                   1080 |                  120 |
| DEN -> ORD |                  9 |                   1080 |                  120 |
| DEN -> LGA |                  8 |                    960 |                  120 |
| DEN -> MSP |                  8 |                    960 |                  120 |
| DEN -> SEA |                  8 |                    960 |                  120 |
| DEN -> ATL |                  8 |                    960 |                  120 |
| DEN -> AUS |                  7 |                    840 |                  120 |
| DEN -> MCO |                  7 |                    840 |                  120 |
| DEN -> IAH |                  7 |                    840 |                  120 |
| DEN -> BNA |                  7 |                    840 |                  120 |
| DEN -> BOS |                  7 |                    840 |                  120 |
| LAX -> LAS |                 13 |                    780 |                   60 |
| LAX -> SFO |                 13 |                    780 |                   60 |
| DEN -> ABQ |                  6 |                    720 |                  120 |

## Interpretation

This simulation approximates how a localized airport disruption can create both direct delays and downstream propagation. The primary disruption affects departures from the disrupted airport during the selected time window. Downstream propagation is estimated using delayed inbound pressure at connected destination airports. Later optimization steps will use this simulated impact to test recovery decisions such as delaying, prioritizing, or canceling flights.
