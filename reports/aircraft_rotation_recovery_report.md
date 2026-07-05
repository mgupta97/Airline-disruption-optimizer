# Aircraft Rotation Recovery Report

## Objective

This module estimates aircraft rotation delay propagation. In real airline operations, a delayed inbound aircraft can delay its next outbound flight if there is not enough turnaround slack. This analysis identifies aircraft chains, routes, and carriers with the highest downstream delay risk.

## Input

- Schedule file used: `data/processed/disruption_simulation_results.parquet`

## Methodology

Flights are grouped by aircraft identifier and flight date, sorted by scheduled departure time, and linked to the next flight in the same aircraft chain. The model estimates turnaround slack and calculates downstream delay pressure when the inbound delay exceeds the available slack.

## Top Aircraft by Rotation Risk

| aircraft_id   | carrier_std   |   flights |   valid_connections |   total_observed_delay |   total_downstream_delay_risk |   avg_turnaround_slack |   total_rotation_risk_score |
|:--------------|:--------------|----------:|--------------------:|-----------------------:|------------------------------:|-----------------------:|----------------------------:|
| N784SK        | OO            |         2 |                   1 |                   1284 |                         143.5 |                    5   |                      1447.5 |
| N837AN        | AA            |         1 |                   0 |                    961 |                           0   |                  nan   |                       961   |
| N730US        | AA            |         3 |                   1 |                    715 |                         214.9 |                  -34.5 |                       949.9 |
| 250NV         | G4            |         2 |                   1 |                    687 |                         230.3 |                   15   |                       937.3 |
| N116DU        | DL            |         2 |                   0 |                    919 |                           0   |                   21   |                       919   |
| N793SK        | OO            |         3 |                   2 |                    550 |                         231.7 |                   37.5 |                       821.7 |
| N87531        | UA            |         2 |                   1 |                    597 |                         191.8 |                   22   |                       808.8 |
| N856NN        | AA            |         3 |                   1 |                    658 |                         105   |                  -56.5 |                       783   |
| N702NK        | NK            |         3 |                   1 |                    508 |                         151.2 |                  -84.5 |                       679.2 |
| N171SY        | OO            |         3 |                   1 |                    456 |                         172.2 |                   36   |                       648.2 |
| N929AT        | DL            |         3 |                   2 |                    403 |                         184.1 |                   -5.5 |                       627.1 |
| N807AW        | AA            |         4 |                   0 |                    618 |                           0   |                  -99   |                       618   |
| N216WR        | WN            |         3 |                   1 |                    410 |                         149.1 |                  -50   |                       579.1 |
| N788CJ        | MQ            |         3 |                   2 |                    341 |                         183.4 |                  -27   |                       564.4 |
| N959NK        | NK            |         2 |                   0 |                    499 |                           0   |                   -4   |                       499   |

## Top Rotation Chains by Downstream Delay Risk

| aircraft_id   | carrier_std   | origin_std   | dest_std   | next_origin   | next_dest   |   observed_arrival_delay |   ground_time_minutes |   turnaround_slack_minutes |   downstream_delay_risk_minutes |   rotation_risk_score |
|:--------------|:--------------|:-------------|:-----------|:--------------|:------------|-------------------------:|----------------------:|---------------------------:|--------------------------------:|----------------------:|
| 250NV         | G4            | DSM          | AUS        | AUS           | DSM         |                      344 |                    50 |                         15 |                           230.3 |                 594.3 |
| N730US        | AA            | DFW          | TUL        | TUL           | DFW         |                      304 |                    42 |                         -3 |                           214.9 |                 538.9 |
| N87531        | UA            | DEN          | FCA        | FCA           | DEN         |                      296 |                    67 |                         22 |                           191.8 |                 507.8 |
| N702NK        | NK            | EWR          | LAX        | LAX           | DFW         |                      256 |                    75 |                         40 |                           151.2 |                 427.2 |
| N171SY        | OO            | LAX          | SFO        | SFO           | PSP         |                      220 |                    19 |                        -26 |                           172.2 |                 412.2 |
| N793SK        | OO            | LAX          | SBP        | SBP           | SFO         |                      252 |                   118 |                         73 |                           125.3 |                 397.3 |
| N216WR        | WN            | ABQ          | BUR        | BUR           | LAS         |                      218 |                    40 |                          5 |                           149.1 |                 387.1 |
| N784SK        | OO            | ASE          | LAX        | LAX           | ASE         |                      210 |                    50 |                          5 |                           143.5 |                 373.5 |
| N856NN        | AA            | DFW          | ABQ        | ABQ           | DFW         |                      160 |                    55 |                         10 |                           105   |                 285   |
| N793SK        | OO            | SBP          | SFO        | SFO           | FAT         |                      154 |                    47 |                          2 |                           106.4 |                 280.4 |
| N929AT        | DL            | ATL          | BNA        | BNA           | DTW         |                      146 |                    45 |                          0 |                           102.2 |                 268.2 |
| N8528Q        | WN            | BWI          | PBI        | PBI           | BWI         |                      141 |                    45 |                         10 |                            91.7 |                 252.7 |
| N27515        | UA            | SFO          | LAX        | LAX           | IAD         |                      149 |                    81 |                         36 |                            79.1 |                 248.1 |
| N788CJ        | MQ            | DTW          | ORD        | ORD           | COU         |                      116 |                     6 |                        -39 |                           108.5 |                 244.5 |
| N648JB        | B6            | MCO          | LGA        | LGA           | PBI         |                      131 |                    46 |                          1 |                            91   |                 242   |

## Carrier Rotation Risk Summary

| carrier_std   |   flights |   valid_connections |   observed_delay |   downstream_delay_risk |   rotation_risk |
|:--------------|----------:|--------------------:|-----------------:|------------------------:|----------------:|
| WN            |      1322 |                 564 |            13568 |                  2298.1 |         27146.1 |
| OO            |       744 |                 291 |            12917 |                  2865.8 |         21602.8 |
| AA            |       856 |                 248 |            12400 |                  1428   |         18788   |
| DL            |       855 |                 286 |             9973 |                   882.7 |         16575.7 |
| UA            |       721 |                 195 |             7277 |                   630.7 |         11807.7 |
| NK            |       208 |                  68 |             5666 |                   402.5 |          7428.5 |
| B6            |       215 |                  48 |             4536 |                   487.9 |          5983.9 |
| MQ            |       242 |                  93 |             2434 |                  1141   |          5435   |
| YX            |       297 |                 119 |             1974 |                   625.1 |          4979.1 |
| F9            |       214 |                  74 |             2750 |                   147   |          4377   |
| AS            |       207 |                  45 |             2356 |                   158.9 |          3414.9 |
| G4            |        85 |                  17 |             2698 |                   273.7 |          3311.7 |
| OH            |       188 |                  65 |             1350 |                   592.2 |          3242.2 |
| HA            |        70 |                  37 |              385 |                   294.7 |          1419.7 |

## Interpretation

Aircraft rotation risk helps move the recovery model closer to real-world airline operations. A flight with moderate delay can be more important than a longer delay if it sits early in an aircraft chain with limited turnaround slack and multiple downstream flights at risk.
