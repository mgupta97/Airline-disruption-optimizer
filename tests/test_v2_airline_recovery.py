from pathlib import Path
import json
import pandas as pd
import pytest


def test_v2_scripts_exist():
    required_scripts = [
        "src/analysis/recovery_strategy_comparison.py",
        "src/simulation/passenger_impact_simulator.py",
        "src/analysis/passenger_aware_recovery_comparison.py",
        "src/optimization/aircraft_rotation_recovery.py",
        "src/optimization/robust_weather_recovery_optimizer.py",
        "src/run_v2_pipeline.py",
    ]

    missing = [script for script in required_scripts if not Path(script).exists()]

    assert not missing, f"Missing V2 scripts: {missing}"


def test_weather_scenario_config_is_valid():
    path = Path("configs/weather_scenarios.json")

    assert path.exists(), "Missing configs/weather_scenarios.json"

    scenarios = json.loads(path.read_text())

    assert len(scenarios) >= 3, "Expected at least 3 weather scenarios"

    probability_sum = 0

    for name, scenario in scenarios.items():
        assert "capacity_reduction" in scenario, f"Missing capacity_reduction for {name}"
        assert "delay_multiplier" in scenario, f"Missing delay_multiplier for {name}"
        assert "passenger_cost_multiplier" in scenario, f"Missing passenger_cost_multiplier for {name}"
        assert "connection_risk_multiplier" in scenario, f"Missing connection_risk_multiplier for {name}"
        assert "scenario_probability" in scenario, f"Missing scenario_probability for {name}"

        assert scenario["capacity_reduction"] >= 0
        assert scenario["delay_multiplier"] >= 1
        assert scenario["passenger_cost_multiplier"] >= 1
        assert scenario["connection_risk_multiplier"] >= 1
        assert scenario["scenario_probability"] >= 0

        probability_sum += scenario["scenario_probability"]

    assert 0.99 <= probability_sum <= 1.01, "Scenario probabilities should sum to approximately 1"


def test_passenger_impact_report_exists_after_pipeline():
    path = Path("reports/passenger_impact_report.md")

    if not path.exists():
        pytest.skip("Passenger impact report not generated yet. Run src/run_v2_pipeline.py.")

    text = path.read_text()

    assert "Passenger Impact Simulation Report" in text
    assert "Passenger Disruption Cost" in text or "passenger disruption cost" in text.lower()


def test_robust_weather_summary_schema_after_pipeline():
    path = Path("reports/robust_weather_recovery_summary.csv")

    if not path.exists():
        pytest.skip("Robust weather summary not generated yet. Run src/run_v2_pipeline.py.")

    df = pd.read_csv(path)

    required_cols = [
        "strategy",
        "selected_actions",
        "expected_passenger_cost_reduction",
        "expected_delay_recovery",
        "worst_case_passenger_cost_reduction",
        "worst_case_delay_recovery",
    ]

    missing = [col for col in required_cols if col not in df.columns]

    assert not missing, f"Missing robust recovery summary columns: {missing}"
    assert len(df) >= 3
    assert df["expected_passenger_cost_reduction"].max() >= 0


def test_aircraft_rotation_report_exists_after_pipeline():
    path = Path("reports/aircraft_rotation_recovery_report.md")

    if not path.exists():
        pytest.skip("Aircraft rotation report not generated yet. Run src/run_v2_pipeline.py.")

    text = path.read_text()

    assert "Aircraft Rotation Recovery Report" in text
    assert "Rotation Risk" in text or "rotation risk" in text.lower()
