from pathlib import Path
import os
import subprocess
import sys
from datetime import datetime


PIPELINE_STEPS = [
    {
        "name": "Disruption Simulation",
        "command": [sys.executable, "src/simulation/disruption_simulator.py"],
        "required": True,
    },
    {
        "name": "Recovery Optimization",
        "command": [sys.executable, "src/optimization/recovery_optimizer.py"],
        "required": True,
    },
    {
        "name": "Recovery Strategy Benchmark",
        "command": [sys.executable, "src/analysis/recovery_strategy_comparison.py"],
        "required": True,
    },
    {
        "name": "Passenger Impact Simulation",
        "command": [sys.executable, "src/simulation/passenger_impact_simulator.py"],
        "required": True,
    },
    {
        "name": "Passenger-Aware Recovery Benchmark",
        "command": [sys.executable, "src/analysis/passenger_aware_recovery_comparison.py"],
        "required": True,
    },
    {
        "name": "Aircraft Rotation Recovery",
        "command": [sys.executable, "src/optimization/aircraft_rotation_recovery.py"],
        "required": True,
    },
    {
        "name": "Robust Weather Recovery Optimizer",
        "command": [sys.executable, "src/optimization/robust_weather_recovery_optimizer.py"],
        "required": True,
    },
]


EXPECTED_OUTPUTS = [
    "reports/recovery_strategy_comparison_report.md",
    "figures/recovery_strategy_comparison.png",

    "reports/passenger_impact_report.md",
    "reports/passenger_impact_summary.csv",
    "figures/passenger_disruption_cost_by_route.png",
    "figures/top_connection_risk_airports.png",
    "figures/passenger_impact_by_stage.png",

    "reports/passenger_aware_recovery_comparison_report.md",
    "figures/passenger_aware_recovery_comparison.png",
    "figures/passenger_aware_delay_recovery_comparison.png",
    "figures/passenger_aware_recovery_tradeoff.png",

    "reports/aircraft_rotation_recovery_report.md",
    "figures/aircraft_rotation_delay_chain.png",
    "figures/top_aircraft_rotation_risk.png",
    "figures/rotation_downstream_delay_by_carrier.png",

    "reports/robust_weather_recovery_report.md",
    "reports/robust_weather_recovery_summary.csv",
    "reports/robust_weather_scenario_matrix.csv",
    "figures/robust_strategy_expected_passenger_cost.png",
    "figures/robust_strategy_worst_case_recovery.png",
    "figures/robust_weather_scenario_heatmap.png",
    "figures/robust_expected_vs_worst_case_tradeoff.png",
]


def ensure_directories():
    for folder in ["data/processed", "reports", "figures", "configs"]:
        Path(folder).mkdir(parents=True, exist_ok=True)


def run_step(step):
    script_path = Path(step["command"][-1])

    if not script_path.exists():
        message = f"Missing script: {script_path}"
        if step["required"]:
            raise FileNotFoundError(message)
        print(f"Skipping optional step: {message}")
        return False

    print("\n" + "=" * 90)
    print(f"Running: {step['name']}")
    print("=" * 90)

    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    result = subprocess.run(
        step["command"],
        env=env,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Pipeline step failed: {step['name']}")

    return True


def validate_outputs():
    missing = []

    for output in EXPECTED_OUTPUTS:
        path = Path(output)
        if not path.exists():
            missing.append(output)

    return missing


def write_pipeline_summary(results, missing_outputs):
    summary_path = Path("reports/v2_pipeline_run_summary.md")

    lines = []
    lines.append("# Airline Recovery V2 Pipeline Run Summary\n")
    lines.append(f"Run timestamp: `{datetime.now().isoformat(timespec='seconds')}`\n")

    lines.append("## Pipeline Steps\n")
    for name, status in results:
        emoji = "✅" if status else "⚠️"
        lines.append(f"- {emoji} {name}")

    lines.append("\n## Expected Outputs\n")
    for output in EXPECTED_OUTPUTS:
        path = Path(output)
        emoji = "✅" if path.exists() else "❌"
        lines.append(f"- {emoji} `{output}`")

    if missing_outputs:
        lines.append("\n## Missing Outputs\n")
        for output in missing_outputs:
            lines.append(f"- `{output}`")
    else:
        lines.append("\nAll expected V2 outputs were generated successfully.\n")

    summary_path.write_text("\n".join(lines))
    print(f"\nPipeline summary written to: {summary_path}")


def main():
    ensure_directories()

    results = []

    for step in PIPELINE_STEPS:
        status = run_step(step)
        results.append((step["name"], status))

    missing_outputs = validate_outputs()
    write_pipeline_summary(results, missing_outputs)

    if missing_outputs:
        print("\nPipeline completed, but some expected outputs are missing:")
        for output in missing_outputs:
            print(f"- {output}")
        raise SystemExit(1)

    print("\nV2 pipeline completed successfully.")


if __name__ == "__main__":
    main()
