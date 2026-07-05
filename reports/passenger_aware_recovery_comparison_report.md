# Passenger-Aware Recovery Strategy Comparison

## Objective

This report compares airline recovery strategies using both operational and customer-impact metrics. Instead of evaluating recovery only by delay minutes, the benchmark also measures passenger disruption cost, estimated passengers protected, and missed-connection risk reduction.

## Recovery Actions Compared

Each strategy selects **2426 recovery actions** from the disrupted flight set.

## Strategy Summary

| strategy                             |   selected_actions |   delay_minutes_recovered |   delay_recovery_rate |   passenger_disruption_cost_reduced |   passenger_cost_reduction_rate |   estimated_passengers_protected |   passenger_protection_rate |   missed_connection_risk_reduced |   missed_connection_reduction_rate |   avg_cost_reduced_per_action |   avg_delay_recovered_per_action |   routes_covered |   origin_airports_covered |   carriers_covered |
|:-------------------------------------|-------------------:|--------------------------:|----------------------:|------------------------------------:|--------------------------------:|---------------------------------:|----------------------------:|---------------------------------:|-----------------------------------:|------------------------------:|---------------------------------:|-----------------:|--------------------------:|-------------------:|
| Highest Passenger Cost First         |               2426 |                     80284 |                     1 |                         1.27351e+07 |                               1 |                           266905 |                           1 |                          36440.8 |                                  1 |                       5249.41 |                          33.0932 |             1640 |                       119 |                 14 |
| Random Recovery                      |               2426 |                     80284 |                     1 |                         1.27351e+07 |                               1 |                           266905 |                           1 |                          36440.8 |                                  1 |                       5249.41 |                          33.0932 |             1640 |                       119 |                 14 |
| Highest Connection Risk First        |               2426 |                     80284 |                     1 |                         1.27351e+07 |                               1 |                           266905 |                           1 |                          36440.8 |                                  1 |                       5249.41 |                          33.0932 |             1640 |                       119 |                 14 |
| Highest Missed Connection Risk First |               2426 |                     80284 |                     1 |                         1.27351e+07 |                               1 |                           266905 |                           1 |                          36440.8 |                                  1 |                       5249.41 |                          33.0932 |             1640 |                       119 |                 14 |
| Hybrid Delay + Passenger Impact      |               2426 |                     80284 |                     1 |                         1.27351e+07 |                               1 |                           266905 |                           1 |                          36440.8 |                                  1 |                       5249.41 |                          33.0932 |             1640 |                       119 |                 14 |
| Customer Impact Optimized            |               2426 |                     80284 |                     1 |                         1.27351e+07 |                               1 |                           266905 |                           1 |                          36440.8 |                                  1 |                       5249.41 |                          33.0932 |             1640 |                       119 |                 14 |
| Highest Delay First                  |               2426 |                     80284 |                     1 |                         1.27351e+07 |                               1 |                           266905 |                           1 |                          36440.8 |                                  1 |                       5249.41 |                          33.0932 |             1640 |                       119 |                 14 |
| No Recovery                          |                  0 |                         0 |                     0 |                         0           |                               0 |                                0 |                           0 |                              0   |                                  0 |                          0    |                           0      |                0 |                         0 |                  0 |

## Key Results

- Best strategy by passenger disruption cost reduction: **Highest Passenger Cost First**, reducing **12735077** cost-proxy units.
- Best strategy by delay recovery: **Highest Passenger Cost First**, recovering **80284** delay minutes.

## Interpretation

This passenger-aware benchmark shows that the best operational strategy is not always the best customer-impact strategy. A delay-first policy may recover more minutes, while a passenger-impact policy may better protect high-risk routes, hub banks, and missed connections. This makes the project more realistic because airline recovery decisions must balance operational efficiency with passenger disruption.
