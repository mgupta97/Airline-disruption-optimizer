# Airline Disruption Recovery Optimization Report

## Optimization Goal

The recovery optimizer selects a limited number of disrupted flights to prioritize in order to maximize recovered delay minutes while respecting operational capacity and fairness constraints.

## Optimization Summary

- Solver status: Optimal
- Candidate flights: 6,628
- Max recovery actions allowed: 120
- Recovery actions used: 120
- Primary actions used: 48
- Downstream actions used: 72
- Simulated total positive delay: 422,787.00 minutes
- Optimized total positive delay: 415,731.00 minutes
- Total recovered delay: 7,056.00 minutes
- Delay reduction: 1.67%

## Impact by Scenario Stage

| scenario_stage             |   candidate_flights |   recovery_actions |   recovered_delay |   remaining_delay |
|:---------------------------|--------------------:|-------------------:|------------------:|------------------:|
| downstream_propagation     |                6150 |                 72 |              3024 |            357441 |
| primary_airport_disruption |                 478 |                 48 |              4032 |             58290 |

## Recovery Actions by Carrier

| carrier   |   recovery_actions |   recovered_delay |
|:----------|-------------------:|------------------:|
| UA        |                 42 |              2772 |
| WN        |                 15 |              1260 |
| AS        |                 20 |               840 |
| DL        |                 16 |               840 |
| B6        |                 13 |               630 |
| AA        |                  9 |               462 |
| HA        |                  3 |               126 |
| F9        |                  1 |                84 |
| NK        |                  1 |                42 |

## Top Flights Selected for Recovery

| carrier   |   flight_num | origin   | dest   | scenario_stage             |   simulated_positive_delay |   delay_increase |   optimized_recovered_delay |   priority_score |
|:----------|-------------:|:---------|:-------|:---------------------------|---------------------------:|-----------------:|----------------------------:|-----------------:|
| AA        |          395 | DEN      | MIA    | primary_airport_disruption |                        125 |              120 |                          84 |            98.97 |
| UA        |          558 | DEN      | BOS    | primary_airport_disruption |                        120 |              120 |                          84 |            99.16 |
| UA        |          424 | DEN      | RSW    | primary_airport_disruption |                        120 |              120 |                          84 |            98.71 |
| UA        |          384 | DEN      | HNL    | primary_airport_disruption |                        120 |              120 |                          84 |           100.75 |
| UA        |          283 | DEN      | FLL    | primary_airport_disruption |                        120 |              120 |                          84 |            98.96 |
| WN        |         1941 | DEN      | ALB    | primary_airport_disruption |                        125 |              120 |                          84 |            98.74 |
| WN        |          368 | DEN      | BDL    | primary_airport_disruption |                        135 |              120 |                          84 |            98.91 |
| WN        |         3473 | DEN      | BOS    | primary_airport_disruption |                        122 |              120 |                          84 |            99.16 |
| WN        |         3515 | DEN      | BOS    | primary_airport_disruption |                        174 |              120 |                          84 |            99.16 |
| WN        |         2701 | DEN      | FLL    | primary_airport_disruption |                        120 |              120 |                          84 |            98.96 |
| WN        |          651 | DEN      | LGA    | primary_airport_disruption |                        120 |              120 |                          84 |            98.78 |
| WN        |         3367 | DEN      | LGA    | primary_airport_disruption |                        120 |              120 |                          84 |            98.78 |
| WN        |          671 | DEN      | MCO    | primary_airport_disruption |                        120 |              120 |                          84 |            98.48 |
| WN        |         1034 | DEN      | MCO    | primary_airport_disruption |                        156 |              120 |                          84 |            98.48 |
| WN        |         6391 | DEN      | MCO    | primary_airport_disruption |                        120 |              120 |                          84 |            98.48 |
| WN        |         1489 | DEN      | ORF    | primary_airport_disruption |                        120 |              120 |                          84 |            98.51 |
| WN        |         2225 | DEN      | PHL    | primary_airport_disruption |                        126 |              120 |                          84 |            98.52 |
| WN        |         2117 | DEN      | PVD    | primary_airport_disruption |                        132 |              120 |                          84 |            99.04 |
| WN        |         1153 | DEN      | RSW    | primary_airport_disruption |                        120 |              120 |                          84 |            98.71 |
| DL        |          751 | DEN      | LGA    | primary_airport_disruption |                        120 |              120 |                          84 |            98.78 |

## Interpretation

This model represents a first optimization layer for airline disruption recovery. It does not yet model full aircraft rotations, crew legality, or gate constraints. However, it establishes the central decision logic: when recovery capacity is limited, prioritize the flights that produce the largest system-level delay reduction while avoiding excessive concentration by carrier or airport. Later versions can extend this into mixed-integer aircraft recovery, passenger reaccommodation, and robust optimization.
