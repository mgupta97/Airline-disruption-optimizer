# Robust Weather Recovery Optimizer Report

## Objective

This module evaluates airline recovery strategies across multiple weather disruption scenarios. Instead of optimizing for one disruption case, it compares strategies using expected recovery value, worst-case recovery value, passenger disruption cost reduction, delay recovery, and scenario stability.

## Input

- Recovery base data: `data/processed/passenger_impact_simulation.parquet`
- Weather scenario config: `configs/weather_scenarios.json`
- Recovery actions selected per strategy: `50`

## Weather Scenarios

| scenario                       | impacted_airports                 |   capacity_reduction |   delay_multiplier |   passenger_cost_multiplier |   probability |
|:-------------------------------|:----------------------------------|---------------------:|-------------------:|----------------------------:|--------------:|
| ORD Thunderstorm Ground Delay  | ORD, MDW                          |                 0.45 |               1.65 |                        1.45 |          0.18 |
| DEN Winter Storm               | DEN                               |                 0.4  |               1.75 |                        1.5  |          0.14 |
| ATL Ground Stop                | ATL                               |                 0.5  |               1.85 |                        1.6  |          0.16 |
| Northeast Severe Weather       | JFK, LGA, EWR, BOS, PHL, DCA, IAD |                 0.38 |               1.6  |                        1.42 |          0.2  |
| West Coast Low Visibility      | SFO, LAX, SAN, SEA, PDX           |                 0.3  |               1.45 |                        1.3  |          0.12 |
| Systemwide Moderate Disruption | Systemwide                        |                 0.2  |               1.25 |                        1.2  |          0.2  |

## Strategy Summary

| strategy                    |   selected_actions |   expected_passenger_cost_reduction |   expected_cost_reduction_rate |   expected_delay_recovery |   expected_delay_recovery_rate |   worst_case_passenger_cost_reduction |   worst_case_delay_recovery |   avg_scenario_variability |   estimated_passengers_protected |   routes_covered |   origin_airports_covered |   carriers_covered |   ord_thunderstorm_ground_delay_cost_reduction |   den_winter_storm_cost_reduction |   atl_ground_stop_cost_reduction |   northeast_severe_weather_cost_reduction |   west_coast_low_visibility_cost_reduction |   systemwide_moderate_disruption_cost_reduction |
|:----------------------------|-------------------:|------------------------------------:|-------------------------------:|--------------------------:|-------------------------------:|--------------------------------------:|----------------------------:|---------------------------:|---------------------------------:|-----------------:|--------------------------:|-------------------:|-----------------------------------------------:|----------------------------------:|---------------------------------:|------------------------------------------:|-------------------------------------------:|------------------------------------------------:|
| Expected Scenario Value     |                 50 |                         3.82581e+06 |                         0.2232 |                  21498.8  |                         0.1904 |                           3.15767e+06 |                    17695.7  |                   18550.1  |                             6015 |               49 |                        30 |                  9 |                                    3.65028e+06 |                       3.52389e+06 |                      3.39378e+06 |                               3.98796e+06 |                                3.71279e+06 |                                     4.44643e+06 |
| Highest Base Passenger Cost |                 50 |                         3.81356e+06 |                         0.2225 |                  20999    |                         0.1859 |                           3.17599e+06 |                    17401.4  |                   18025.1  |                             6202 |               48 |                        29 |                  9 |                                    3.58052e+06 |                       3.50806e+06 |                      3.41218e+06 |                               3.93368e+06 |                                3.75762e+06 |                                     4.47168e+06 |
| Robust Balanced Recovery    |                 50 |                         3.81174e+06 |                         0.2224 |                  21458.1  |                         0.19   |                           3.16974e+06 |                    17791.9  |                   17982.5  |                             6011 |               49 |                        29 |                  9 |                                    3.61904e+06 |                       3.50059e+06 |                      3.4062e+06  |                               3.9278e+06  |                                3.72486e+06 |                                     4.46347e+06 |
| Worst-Case Robust           |                 50 |                         3.70954e+06 |                         0.2165 |                  21346.9  |                         0.189  |                           3.12923e+06 |                    17960.6  |                   16380.4  |                             5786 |               48 |                        28 |                  8 |                                    3.53317e+06 |                       3.36606e+06 |                      3.29896e+06 |                               3.75559e+06 |                                3.68435e+06 |                                     4.40626e+06 |
| Highest Base Delay          |                 50 |                         3.60691e+06 |                         0.2105 |                  21874.9  |                         0.1937 |                           3.03055e+06 |                    18343.6  |                   16261.2  |                             5388 |               49 |                        33 |                  9 |                                    3.46517e+06 |                       3.21127e+06 |                      3.19729e+06 |                               3.68448e+06 |                                3.59826e+06 |                                     4.26677e+06 |
| Random Recovery             |                 50 |                    436255           |                         0.0255 |                   2833.79 |                         0.0251 |                      355179           |                     2295.07 |                    2259.87 |                             5423 |               50 |                        29 |                 12 |                               475969           |                  372028           |                 416700           |                          413646           |                           408450           |                                500406           |
| No Recovery                 |                  0 |                         0           |                         0      |                      0    |                         0      |                           0           |                        0    |                       0    |                                0 |                0 |                         0 |                  0 |                                    0           |                       0           |                      0           |                               0           |                                0           |                                     0           |

## Scenario Recovery Matrix

| strategy                    |   ord_thunderstorm_ground_delay_cost_reduction |   den_winter_storm_cost_reduction |   atl_ground_stop_cost_reduction |   northeast_severe_weather_cost_reduction |   west_coast_low_visibility_cost_reduction |   systemwide_moderate_disruption_cost_reduction |
|:----------------------------|-----------------------------------------------:|----------------------------------:|---------------------------------:|------------------------------------------:|-------------------------------------------:|------------------------------------------------:|
| Expected Scenario Value     |                                    3.65028e+06 |                       3.52389e+06 |                      3.39378e+06 |                               3.98796e+06 |                                3.71279e+06 |                                     4.44643e+06 |
| Highest Base Passenger Cost |                                    3.58052e+06 |                       3.50806e+06 |                      3.41218e+06 |                               3.93368e+06 |                                3.75762e+06 |                                     4.47168e+06 |
| Robust Balanced Recovery    |                                    3.61904e+06 |                       3.50059e+06 |                      3.4062e+06  |                               3.9278e+06  |                                3.72486e+06 |                                     4.46347e+06 |
| Worst-Case Robust           |                                    3.53317e+06 |                       3.36606e+06 |                      3.29896e+06 |                               3.75559e+06 |                                3.68435e+06 |                                     4.40626e+06 |
| Highest Base Delay          |                                    3.46517e+06 |                       3.21127e+06 |                      3.19729e+06 |                               3.68448e+06 |                                3.59826e+06 |                                     4.26677e+06 |
| Random Recovery             |                               475969           |                  372028           |                 416700           |                          413646           |                           408450           |                                500406           |
| No Recovery                 |                                    0           |                       0           |                      0           |                               0           |                                0           |                                     0           |

## Key Results

- Best expected-value strategy: **Expected Scenario Value**, with **3825812** expected passenger-cost reduction units.
- Best worst-case strategy: **Highest Base Passenger Cost**, with **3175991** worst-case passenger-cost reduction units.

## Interpretation

The robust recovery optimizer makes the project more realistic by showing how a recovery plan performs across several plausible weather disruptions rather than only one deterministic disruption. This helps compare aggressive expected-value strategies against more stable worst-case strategies.
