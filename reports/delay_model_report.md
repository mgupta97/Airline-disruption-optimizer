# Baseline Flight Delay Prediction Model

## Objective

Predict whether an operated, non-diverted flight will arrive 15 or more minutes late using only pre-departure schedule information.

## Model Setup

- Model: SGDClassifier logistic baseline
- Target: arrival_delay_15
- Time-based split date: 2025-01-25 00:00:00
- Training rows: 418,765
- Test rows: 103,504
- Test delay rate: 11.19%

## Test Performance

- Accuracy: 0.5472
- Precision: 0.1319
- Recall: 0.546
- F1 Score: 0.2125
- ROC AUC: 0.5587
- Average Precision: 0.1331

## Notes

This is a first baseline model. It intentionally avoids using actual departure delay, arrival delay, or delay-cause fields to prevent leakage. Later versions will add airport congestion, weather, inbound aircraft delay, and network propagation features.
