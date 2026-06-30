# Airline Disruption Recovery Optimization Report

## Optimization Goal

The recovery optimizer selects a limited number of disrupted flights to prioritize in order to maximize recovered delay minutes while respecting operational capacity and fairness constraints.

## Optimization Summary

- Solver status: Optimal
- Candidate flights: 6,224
- Max recovery actions allowed: 120
- Recovery actions used: 120
- Primary actions used: 48
- Downstream actions used: 72
- Simulated total positive delay: 302,982.00 minutes
- Optimized total positive delay: 296,934.00 minutes
- Total recovered delay: 6,048.00 minutes
- Delay reduction: 2.0%

## Impact by Scenario Stage

| scenario_stage             |   candidate_flights |   recovery_actions |   recovered_delay |   remaining_delay |
|:---------------------------|--------------------:|-------------------:|------------------:|------------------:|
| downstream_propagation     |                5867 |                 72 |              3024 |            264499 |
| primary_airport_disruption |                 357 |                 48 |              3024 |             32435 |

## Recovery Actions by Carrier

| carrier   |   recovery_actions |   recovered_delay |
|:----------|-------------------:|------------------:|
| UA        |                 32 |              1911 |
| WN        |                 29 |              1491 |
| AA        |                 28 |              1218 |
| DL        |                 25 |              1113 |
| F9        |                  2 |               126 |
| B6        |                  1 |                63 |
| AS        |                  1 |                42 |
| G4        |                  1 |                42 |
| OO        |                  1 |                42 |

## Top Flights Selected for Recovery

| carrier   |   flight_num | origin   | dest   | scenario_stage             |   simulated_positive_delay |   delay_increase |   optimized_recovered_delay |   priority_score |
|:----------|-------------:|:---------|:-------|:---------------------------|---------------------------:|-----------------:|----------------------------:|-----------------:|
| AA        |          395 | DEN      | MIA    | primary_airport_disruption |                         95 |               90 |                          63 |            74.49 |
| UA        |          470 | DEN      | SRQ    | primary_airport_disruption |                         93 |               90 |                          63 |            74.1  |
| UA        |          424 | DEN      | RSW    | primary_airport_disruption |                         90 |               90 |                          63 |            74.3  |
| UA        |          384 | DEN      | HNL    | primary_airport_disruption |                         90 |               90 |                          63 |            75.57 |
| UA        |          350 | DEN      | TPA    | primary_airport_disruption |                         90 |               90 |                          63 |            74.04 |
| UA        |          283 | DEN      | FLL    | primary_airport_disruption |                         90 |               90 |                          63 |            74.48 |
| WN        |         1941 | DEN      | ALB    | primary_airport_disruption |                         95 |               90 |                          63 |            74.32 |
| WN        |         3473 | DEN      | BOS    | primary_airport_disruption |                         92 |               90 |                          63 |            74.63 |
| WN        |         3515 | DEN      | BOS    | primary_airport_disruption |                        144 |               90 |                          63 |            74.63 |
| WN        |          496 | DEN      | BWI    | primary_airport_disruption |                         90 |               90 |                          63 |            74    |
| WN        |         2701 | DEN      | FLL    | primary_airport_disruption |                         90 |               90 |                          63 |            74.48 |
| WN        |          651 | DEN      | LGA    | primary_airport_disruption |                         90 |               90 |                          63 |            74.34 |
| WN        |         3367 | DEN      | LGA    | primary_airport_disruption |                         90 |               90 |                          63 |            74.34 |
| WN        |          440 | DEN      | MCO    | primary_airport_disruption |                         90 |               90 |                          63 |            74.12 |
| WN        |          671 | DEN      | MCO    | primary_airport_disruption |                         90 |               90 |                          63 |            74.12 |
| WN        |         6391 | DEN      | MCO    | primary_airport_disruption |                         90 |               90 |                          63 |            74.12 |
| WN        |         1387 | DEN      | SRQ    | primary_airport_disruption |                         90 |               90 |                          63 |            74.1  |
| WN        |         2727 | DEN      | TPA    | primary_airport_disruption |                         90 |               90 |                          63 |            74.04 |
| DL        |          751 | DEN      | LGA    | primary_airport_disruption |                         90 |               90 |                          63 |            74.34 |
| DL        |         2537 | DEN      | BOS    | primary_airport_disruption |                         90 |               90 |                          63 |            74.63 |

## Interpretation

This model represents a first optimization layer for airline disruption recovery. It does not yet model full aircraft rotations, crew legality, or gate constraints. However, it establishes the central decision logic: when recovery capacity is limited, prioritize the flights that produce the largest system-level delay reduction while avoiding excessive concentration by carrier or airport. Later versions can extend this into mixed-integer aircraft recovery, passenger reaccommodation, and robust optimization.
