# Recovery Strategy Comparison Report

## Objective

This report compares the optimized recovery plan against simple operational heuristics. The goal is to evaluate whether the optimization model provides better recovery value than baseline rules such as random selection, highest-delay-first, primary-impact-first, and network-criticality-first recovery.

## Input Files

- Simulation input: `data/processed/disruption_simulation_results.parquet`
- Optimized recovery input: `data/processed/optimized_recovery_plan.parquet`
- Recovery actions compared per strategy: `2426`

## Strategy Summary

| strategy                  |   selected_actions |   recovered_delay_minutes |   remaining_delay_minutes |   recovery_rate |   avg_recovery_per_action |   carriers_affected |   origin_airports_affected |   dest_airports_affected |   primary_actions |   downstream_actions |
|:--------------------------|-------------------:|--------------------------:|--------------------------:|----------------:|--------------------------:|--------------------:|---------------------------:|-------------------------:|------------------:|---------------------:|
| Random Recovery           |               2426 |                     80284 |                         0 |               1 |                   33.0932 |                  14 |                        119 |                      205 |               115 |                 2311 |
| Highest Delay First       |               2426 |                     80284 |                         0 |               1 |                   33.0932 |                  14 |                        119 |                      205 |               115 |                 2311 |
| Primary Impact First      |               2426 |                     80284 |                         0 |               1 |                   33.0932 |                  14 |                        119 |                      205 |               115 |                 2311 |
| Network Criticality First |               2426 |                     80284 |                         0 |               1 |                   33.0932 |                  14 |                        119 |                      205 |               115 |                 2311 |
| Hybrid Delay + Network    |               2426 |                     80284 |                         0 |               1 |                   33.0932 |                  14 |                        119 |                      205 |               115 |                 2311 |
| Optimized Recovery Plan   |               2426 |                     80284 |                         0 |               1 |                   33.0932 |                  14 |                        119 |                      205 |               115 |                 2311 |
| No Recovery               |                  0 |                         0 |                     80284 |               0 |                    0      |                   0 |                          0 |                        0 |                 0 |                    0 |

## Key Result

The best-performing strategy was **Random Recovery**, recovering **80284 delay minutes** with a recovery rate of **100.00%**.

## Interpretation

This benchmark makes the recovery optimizer more credible because it is no longer evaluated in isolation. It is compared against practical baseline rules that an operations team might use during a disruption. If the optimized recovery plan outperforms these baselines, it provides stronger evidence that the optimization model adds decision value.
