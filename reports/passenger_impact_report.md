# Passenger Impact Simulation Report

## Objective

This module estimates the passenger-level impact of an airline disruption using proxy features derived from route frequency, carrier scale, airport hub exposure, delay severity, and connection-bank timing. The purpose is to move beyond delay minutes alone and estimate which disrupted flights, routes, and airports create the highest customer impact.

## Input

- Disruption simulation file: `data/processed/disruption_simulation_results.parquet`

## Overall Summary

|   disrupted_records |   total_delay_minutes |   estimated_passengers_affected |   estimated_missed_connection_risk |   total_passenger_disruption_cost |   avg_connection_risk_score | top_origin_airport_by_cost   | top_route_by_cost   |
|--------------------:|----------------------:|--------------------------------:|-----------------------------------:|----------------------------------:|----------------------------:|:-----------------------------|:--------------------|
|                2426 |                 80284 |                          266905 |                            36440.8 |                       1.27351e+07 |                     30.7152 | ORD                          | PHL-DFW             |

## Top Routes by Passenger Disruption Cost

| route   |   records |   delay_minutes |   estimated_passengers |   missed_connection_risk |   passenger_disruption_cost |
|:--------|----------:|----------------:|-----------------------:|-------------------------:|----------------------------:|
| PHL-DFW |         2 |             967 |                    240 |                   125.88 |                    195137   |
| SNA-SEA |         2 |             990 |                    228 |                   136.23 |                    186166   |
| DFW-MIA |         4 |             617 |                    588 |                   414.61 |                    156587   |
| LAX-ASE |         1 |            1074 |                     84 |                    54.78 |                    129442   |
| DEN-ASE |         5 |             380 |                   1025 |                   514.78 |                    124229   |
| EWR-ORD |         3 |             531 |                    384 |                   159.95 |                    115900   |
| ORD-MKE |         4 |             425 |                    572 |                   261.51 |                    103018   |
| ASE-DEN |         4 |             413 |                    572 |                   384.54 |                     97967.9 |
| EWR-FLL |         5 |             427 |                    713 |                   241.84 |                     92310.9 |
| LAX-SFO |         3 |             427 |                    399 |                   238.86 |                     91014.2 |
| ORD-BNA |         2 |             394 |                    244 |                   193.59 |                     87341.1 |
| MCO-RDU |         2 |             433 |                    230 |                   108.28 |                     83790.2 |
| DFW-BNA |         2 |             389 |                    240 |                   151.1  |                     81117   |
| FLL-LGA |         6 |             360 |                    872 |                   281.76 |                     79972.2 |
| DEN-FCA |         2 |             297 |                    314 |                   151.77 |                     76524.3 |

## Top Origin Airports by Passenger Disruption Cost

| origin_airport   |   records |   delay_minutes |   estimated_passengers |   avg_connection_risk |   passenger_disruption_cost |
|:-----------------|----------:|----------------:|-----------------------:|----------------------:|----------------------------:|
| ORD              |       143 |            5426 |                  15949 |               51.0766 |                 1.00175e+06 |
| DFW              |       123 |            4801 |                  13038 |               45.8658 |            881713           |
| DEN              |       115 |            3329 |                  17309 |               41.7962 |            758767           |
| LAX              |        47 |            3644 |                   5114 |               30.8883 |            544282           |
| FLL              |        69 |            2996 |                   7865 |               36.2507 |            524309           |
| EWR              |        55 |            2575 |                   6331 |               35.5447 |            489259           |
| ATL              |       112 |            2544 |                  13352 |               43.0671 |            462364           |
| PHX              |        69 |            2502 |                   8222 |               33.2028 |            421232           |
| MCO              |        84 |            2252 |                  10467 |               39.6295 |            402015           |
| SNA              |        28 |            2006 |                   3189 |               27.5982 |            343006           |
| DTW              |        67 |            1987 |                   7261 |               34.309  |            326080           |
| CLT              |        75 |            2046 |                   8156 |               33.8673 |            311475           |
| PHL              |        40 |            1767 |                   4150 |               26.395  |            308572           |
| ASE              |        12 |            1729 |                   1372 |               54.8817 |            287646           |
| JFK              |        56 |            1674 |                   6511 |               30.8959 |            270043           |

## Impact by Disruption Stage

| stage_std                  |   records |   delay_minutes |   estimated_passengers |   missed_connection_risk |   passenger_disruption_cost |
|:---------------------------|----------:|----------------:|-----------------------:|-------------------------:|----------------------------:|
| downstream_propagation     |      2311 |           76955 |                 249596 |                 33722    |                 1.19763e+07 |
| primary_airport_disruption |       115 |            3329 |                  17309 |                  2718.83 |            758767           |

## Interpretation

Passenger disruption cost is a proxy metric, not a true accounting cost. It combines estimated passengers, delay minutes, and missed-connection risk. This helps prioritize recovery actions that may matter more from a customer-impact perspective, not just from an operational delay-minimization perspective.
