from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")
FIGURES_DIR = Path("figures")
CONFIG_PATH = Path("configs/weather_scenarios.json")

PASSENGER_IMPACT_PATH = PROCESSED_DIR / "passenger_impact_simulation.parquet"

FALLBACK_CANDIDATES = [
    PROCESSED_DIR / "disruption_simulation_results.parquet",
    PROCESSED_DIR / "disruption_simulation_results.csv",
]

OUTPUT_PLAN = PROCESSED_DIR / "robust_weather_recovery_plan.csv"
OUTPUT_SUMMARY = REPORTS_DIR / "robust_weather_recovery_summary.csv"
OUTPUT_SCENARIO_MATRIX = REPORTS_DIR / "robust_weather_scenario_matrix.csv"
OUTPUT_REPORT = REPORTS_DIR / "robust_weather_recovery_report.md"

FIG_EXPECTED = FIGURES_DIR / "robust_strategy_expected_passenger_cost.png"
FIG_WORST = FIGURES_DIR / "robust_strategy_worst_case_recovery.png"
FIG_HEATMAP = FIGURES_DIR / "robust_weather_scenario_heatmap.png"
FIG_TRADEOFF = FIGURES_DIR / "robust_expected_vs_worst_case_tradeoff.png"


def read_table(path):
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported file format: {path}")


def read_first_existing(paths):
    for path in paths:
        if path.exists():
            return read_table(path), path

    raise FileNotFoundError(
        "Could not find passenger impact or disruption simulation data. Run:\n"
        "PYTHONPATH=. python src/simulation/disruption_simulator.py\n"
        "PYTHONPATH=. python src/simulation/passenger_impact_simulator.py"
    )


def find_column(df, candidates):
    normalized = {str(c).lower().strip(): c for c in df.columns}

    for candidate in candidates:
        key = candidate.lower().strip()
        if key in normalized:
            return normalized[key]

    for col in df.columns:
        col_lower = str(col).lower()
        if any(candidate.lower() in col_lower for candidate in candidates):
            return col

    return None


def rank_pct(series):
    values = pd.to_numeric(series, errors="coerce").fillna(0)

    if values.nunique() <= 1:
        return pd.Series(0.5, index=series.index)

    return values.rank(pct=True)


def load_recovery_base_data():
    if PASSENGER_IMPACT_PATH.exists():
        df = pd.read_parquet(PASSENGER_IMPACT_PATH)
        input_path = PASSENGER_IMPACT_PATH
    else:
        df, input_path = read_first_existing(FALLBACK_CANDIDATES)

    df = standardize_base_data(df)

    return df, input_path


def standardize_base_data(df):
    df = df.copy()

    origin_col = find_column(df, ["origin_std", "origin", "origin_airport"])
    dest_col = find_column(df, ["dest_std", "dest", "destination", "dest_airport"])
    carrier_col = find_column(df, ["carrier_std", "carrier", "airline", "op_unique_carrier"])
    route_col = find_column(df, ["route"])
    stage_col = find_column(df, ["stage_std", "impact_stage", "stage", "disruption_stage"])

    delay_col = find_column(
        df,
        [
            "delay_minutes_std",
            "added_delay_minutes",
            "recoverable_delay_minutes",
            "positive_delay_minutes",
            "total_added_delay",
            "arrival_delay",
            "arr_delay",
            "delay_minutes",
            "simulated_delay"
        ],
    )

    passenger_col = find_column(df, ["estimated_passengers", "passengers"])
    cost_col = find_column(df, ["passenger_disruption_cost"])
    missed_col = find_column(df, ["estimated_missed_connection_risk", "missed_connection"])
    connection_col = find_column(df, ["connection_risk_score", "connection_risk"])

    if delay_col is None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            raise ValueError("No numeric delay column found.")
        delay_col = numeric_cols[0]

    df["origin_std"] = df[origin_col].astype(str) if origin_col else "Unknown"
    df["dest_std"] = df[dest_col].astype(str) if dest_col else "Unknown"
    df["carrier_std"] = df[carrier_col].astype(str) if carrier_col else "Unknown"
    df["stage_std"] = df[stage_col].astype(str) if stage_col else "Unknown"

    if route_col:
        df["route"] = df[route_col].astype(str)
    else:
        df["route"] = df["origin_std"] + "-" + df["dest_std"]

    df["delay_minutes"] = pd.to_numeric(df[delay_col], errors="coerce").fillna(0).clip(lower=0)

    if passenger_col:
        df["estimated_passengers"] = pd.to_numeric(df[passenger_col], errors="coerce").fillna(100)
    else:
        route_frequency = df.groupby("route")["delay_minutes"].transform("count")
        df["estimated_passengers"] = 70 + 130 * rank_pct(route_frequency)

    if connection_col:
        df["connection_risk_score"] = pd.to_numeric(df[connection_col], errors="coerce").fillna(50)
    else:
        hub_proxy = (
            df.groupby("origin_std")["delay_minutes"].transform("count")
            + df.groupby("dest_std")["delay_minutes"].transform("count")
        )
        df["connection_risk_score"] = 100 * rank_pct(hub_proxy)

    if missed_col:
        df["missed_connection_risk"] = pd.to_numeric(df[missed_col], errors="coerce").fillna(0)
    else:
        df["missed_connection_risk"] = (
            df["estimated_passengers"]
            * df["connection_risk_score"] / 100
            * (df["delay_minutes"] / 90).clip(0, 1.5)
        )

    if cost_col:
        df["passenger_disruption_cost"] = pd.to_numeric(df[cost_col], errors="coerce").fillna(0)
    else:
        df["passenger_disruption_cost"] = (
            df["estimated_passengers"]
            * df["delay_minutes"]
            * (1 + df["connection_risk_score"] / 100)
        )

    df = df[
        (df["delay_minutes"] > 0)
        & (df["passenger_disruption_cost"] > 0)
    ].copy()

    df = df.reset_index(drop=True)
    df["action_id"] = np.arange(len(df))

    return df


def load_scenarios():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")

    with CONFIG_PATH.open("r") as f:
        scenarios = json.load(f)

    total_probability = sum(float(v.get("scenario_probability", 0)) for v in scenarios.values())

    if total_probability <= 0:
        equal_probability = 1 / len(scenarios)
        for scenario in scenarios.values():
            scenario["scenario_probability"] = equal_probability
    else:
        for scenario in scenarios.values():
            scenario["scenario_probability"] = float(scenario.get("scenario_probability", 0)) / total_probability

    return scenarios


def apply_weather_scenarios(df, scenarios):
    df = df.copy()

    scenario_value_cols = []
    scenario_delay_cols = []

    for scenario_name, config in scenarios.items():
        impacted_airports = set(config.get("impacted_airports", []))
        capacity_reduction = float(config.get("capacity_reduction", 0.20))
        delay_multiplier = float(config.get("delay_multiplier", 1.25))
        passenger_cost_multiplier = float(config.get("passenger_cost_multiplier", 1.20))
        connection_risk_multiplier = float(config.get("connection_risk_multiplier", 1.15))

        if impacted_airports:
            impacted = (
                df["origin_std"].isin(impacted_airports)
                | df["dest_std"].isin(impacted_airports)
            )
        else:
            impacted = pd.Series(True, index=df.index)

        route_frequency = df.groupby("route")["delay_minutes"].transform("count")
        airport_frequency = (
            df.groupby("origin_std")["delay_minutes"].transform("count")
            + df.groupby("dest_std")["delay_minutes"].transform("count")
        )

        route_pressure = rank_pct(route_frequency)
        airport_pressure = rank_pct(airport_frequency)

        baseline_factor = 1 + 0.15 * capacity_reduction
        impacted_factor = np.where(
            impacted,
            delay_multiplier * (1 + capacity_reduction),
            baseline_factor
        )

        passenger_factor = np.where(
            impacted,
            passenger_cost_multiplier * (1 + 0.35 * capacity_reduction),
            1 + 0.10 * capacity_reduction
        )

        connection_factor = np.where(
            impacted,
            connection_risk_multiplier,
            1 + 0.05 * capacity_reduction
        )

        scenario_delay_col = f"{safe_name(scenario_name)}_delay_value"
        scenario_cost_col = f"{safe_name(scenario_name)}_passenger_cost_value"

        df[scenario_delay_col] = (
            df["delay_minutes"]
            * impacted_factor
            * (1 + 0.10 * route_pressure + 0.10 * airport_pressure)
        )

        df[scenario_cost_col] = (
            df["passenger_disruption_cost"]
            * passenger_factor
            * connection_factor
            * (1 + 0.10 * airport_pressure)
        )

        scenario_delay_cols.append(scenario_delay_col)
        scenario_value_cols.append(scenario_cost_col)

    probabilities = np.array([
        scenarios[name]["scenario_probability"]
        for name in scenarios.keys()
    ])

    value_matrix = df[scenario_value_cols].to_numpy()
    delay_matrix = df[scenario_delay_cols].to_numpy()

    df["expected_passenger_cost_reduction"] = value_matrix.dot(probabilities)
    df["expected_delay_recovery"] = delay_matrix.dot(probabilities)
    df["worst_case_passenger_cost_reduction"] = value_matrix.min(axis=1)
    df["worst_case_delay_recovery"] = delay_matrix.min(axis=1)
    df["scenario_value_std"] = value_matrix.std(axis=1)
    df["scenario_delay_std"] = delay_matrix.std(axis=1)

    df["robust_recovery_score"] = (
        0.55 * rank_pct(df["expected_passenger_cost_reduction"])
        + 0.30 * rank_pct(df["worst_case_passenger_cost_reduction"])
        + 0.15 * rank_pct(df["expected_delay_recovery"])
        - 0.10 * rank_pct(df["scenario_value_std"])
    )

    df["worst_case_recovery_score"] = (
        0.70 * rank_pct(df["worst_case_passenger_cost_reduction"])
        + 0.20 * rank_pct(df["worst_case_delay_recovery"])
        - 0.10 * rank_pct(df["scenario_value_std"])
    )

    df["expected_value_score"] = (
        0.70 * rank_pct(df["expected_passenger_cost_reduction"])
        + 0.30 * rank_pct(df["expected_delay_recovery"])
    )

    return df, scenario_value_cols, scenario_delay_cols


def safe_name(name):
    return (
        name.lower()
        .replace("&", "and")
        .replace("+", "plus")
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def get_action_count(df):
    return min(50, max(10, int(len(df) * 0.05)), len(df))


def constrained_select(df, score_col, action_count):
    if action_count == 0:
        return df.iloc[0:0].copy()

    max_per_origin = max(3, int(action_count * 0.25))
    max_per_carrier = max(3, int(action_count * 0.30))
    max_per_route = max(2, int(action_count * 0.15))

    selected_rows = []
    origin_counts = {}
    carrier_counts = {}
    route_counts = {}

    candidates = df.sort_values(score_col, ascending=False)

    for _, row in candidates.iterrows():
        origin = row["origin_std"]
        carrier = row["carrier_std"]
        route = row["route"]

        if origin_counts.get(origin, 0) >= max_per_origin:
            continue

        if carrier_counts.get(carrier, 0) >= max_per_carrier:
            continue

        if route_counts.get(route, 0) >= max_per_route:
            continue

        selected_rows.append(row)

        origin_counts[origin] = origin_counts.get(origin, 0) + 1
        carrier_counts[carrier] = carrier_counts.get(carrier, 0) + 1
        route_counts[route] = route_counts.get(route, 0) + 1

        if len(selected_rows) >= action_count:
            break

    if len(selected_rows) < action_count:
        selected_ids = {row["action_id"] for row in selected_rows}
        remaining = candidates[~candidates["action_id"].isin(selected_ids)]
        for _, row in remaining.iterrows():
            selected_rows.append(row)
            if len(selected_rows) >= action_count:
                break

    if not selected_rows:
        return df.iloc[0:0].copy()

    return pd.DataFrame(selected_rows).reset_index(drop=True)


def select_strategy(df, strategy_name, action_count):
    if strategy_name == "No Recovery" or action_count == 0:
        return df.iloc[0:0].copy()

    if strategy_name == "Random Recovery":
        return df.sample(n=action_count, random_state=42).copy()

    if strategy_name == "Highest Base Delay":
        return constrained_select(df, "delay_minutes", action_count)

    if strategy_name == "Highest Base Passenger Cost":
        return constrained_select(df, "passenger_disruption_cost", action_count)

    if strategy_name == "Expected Scenario Value":
        return constrained_select(df, "expected_value_score", action_count)

    if strategy_name == "Worst-Case Robust":
        return constrained_select(df, "worst_case_recovery_score", action_count)

    if strategy_name == "Robust Balanced Recovery":
        return constrained_select(df, "robust_recovery_score", action_count)

    raise ValueError(f"Unknown strategy: {strategy_name}")


def summarize_strategy(strategy_name, selected, all_df, scenario_value_cols):
    total_expected_cost = all_df["expected_passenger_cost_reduction"].sum()
    total_expected_delay = all_df["expected_delay_recovery"].sum()

    expected_cost = selected["expected_passenger_cost_reduction"].sum()
    expected_delay = selected["expected_delay_recovery"].sum()

    worst_case_cost = selected["worst_case_passenger_cost_reduction"].sum()
    worst_case_delay = selected["worst_case_delay_recovery"].sum()

    value_std = selected["scenario_value_std"].mean() if len(selected) else 0

    row = {
        "strategy": strategy_name,
        "selected_actions": len(selected),
        "expected_passenger_cost_reduction": expected_cost,
        "expected_cost_reduction_rate": expected_cost / total_expected_cost if total_expected_cost else 0,
        "expected_delay_recovery": expected_delay,
        "expected_delay_recovery_rate": expected_delay / total_expected_delay if total_expected_delay else 0,
        "worst_case_passenger_cost_reduction": worst_case_cost,
        "worst_case_delay_recovery": worst_case_delay,
        "avg_scenario_variability": value_std,
        "estimated_passengers_protected": selected["estimated_passengers"].sum() if len(selected) else 0,
        "routes_covered": selected["route"].nunique() if len(selected) else 0,
        "origin_airports_covered": selected["origin_std"].nunique() if len(selected) else 0,
        "carriers_covered": selected["carrier_std"].nunique() if len(selected) else 0,
    }

    for col in scenario_value_cols:
        scenario_label = col.replace("_passenger_cost_value", "")
        row[f"{scenario_label}_cost_reduction"] = selected[col].sum()

    return row


def build_scenario_matrix(summary_df, scenario_value_cols):
    scenario_cols = [
        col.replace("_passenger_cost_value", "") + "_cost_reduction"
        for col in scenario_value_cols
    ]

    available_cols = ["strategy"] + [col for col in scenario_cols if col in summary_df.columns]

    return summary_df[available_cols].copy()


def markdown_table(df):
    try:
        return df.to_markdown(index=False)
    except Exception:
        return "```\n" + df.to_string(index=False) + "\n```"


def build_report(summary_df, scenario_matrix, input_path, action_count, scenarios):
    display = summary_df.copy()
    numeric_cols = display.select_dtypes(include="number").columns
    display[numeric_cols] = display[numeric_cols].round(4)

    matrix_display = scenario_matrix.copy()
    numeric_matrix_cols = matrix_display.select_dtypes(include="number").columns
    matrix_display[numeric_matrix_cols] = matrix_display[numeric_matrix_cols].round(2)

    best_expected = summary_df.sort_values(
        "expected_passenger_cost_reduction",
        ascending=False
    ).iloc[0]

    best_worst = summary_df.sort_values(
        "worst_case_passenger_cost_reduction",
        ascending=False
    ).iloc[0]

    report = "# Robust Weather Recovery Optimizer Report\n\n"

    report += "## Objective\n\n"
    report += (
        "This module evaluates airline recovery strategies across multiple weather "
        "disruption scenarios. Instead of optimizing for one disruption case, it compares "
        "strategies using expected recovery value, worst-case recovery value, passenger "
        "disruption cost reduction, delay recovery, and scenario stability.\n\n"
    )

    report += "## Input\n\n"
    report += f"- Recovery base data: `{input_path}`\n"
    report += f"- Weather scenario config: `{CONFIG_PATH}`\n"
    report += f"- Recovery actions selected per strategy: `{action_count}`\n\n"

    report += "## Weather Scenarios\n\n"
    scenario_rows = []
    for name, cfg in scenarios.items():
        scenario_rows.append({
            "scenario": name,
            "impacted_airports": ", ".join(cfg.get("impacted_airports", [])) or "Systemwide",
            "capacity_reduction": cfg.get("capacity_reduction"),
            "delay_multiplier": cfg.get("delay_multiplier"),
            "passenger_cost_multiplier": cfg.get("passenger_cost_multiplier"),
            "probability": cfg.get("scenario_probability"),
        })

    report += markdown_table(pd.DataFrame(scenario_rows))
    report += "\n\n"

    report += "## Strategy Summary\n\n"
    report += markdown_table(display)
    report += "\n\n"

    report += "## Scenario Recovery Matrix\n\n"
    report += markdown_table(matrix_display)
    report += "\n\n"

    report += "## Key Results\n\n"
    report += (
        f"- Best expected-value strategy: **{best_expected['strategy']}**, with "
        f"**{best_expected['expected_passenger_cost_reduction']:.0f}** expected "
        f"passenger-cost reduction units.\n"
    )

    report += (
        f"- Best worst-case strategy: **{best_worst['strategy']}**, with "
        f"**{best_worst['worst_case_passenger_cost_reduction']:.0f}** worst-case "
        f"passenger-cost reduction units.\n\n"
    )

    report += "## Interpretation\n\n"
    report += (
        "The robust recovery optimizer makes the project more realistic by showing how "
        "a recovery plan performs across several plausible weather disruptions rather "
        "than only one deterministic disruption. This helps compare aggressive expected-value "
        "strategies against more stable worst-case strategies.\n"
    )

    return report


def save_figures(summary_df, scenario_matrix):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    plot_df = summary_df.sort_values("expected_passenger_cost_reduction", ascending=False)

    plt.figure(figsize=(12, 6))
    plt.bar(plot_df["strategy"], plot_df["expected_passenger_cost_reduction"])
    plt.title("Expected Passenger Cost Reduction by Strategy")
    plt.ylabel("Expected Passenger Cost Reduction")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_EXPECTED, dpi=200)
    plt.close()

    plot_df = summary_df.sort_values("worst_case_passenger_cost_reduction", ascending=False)

    plt.figure(figsize=(12, 6))
    plt.bar(plot_df["strategy"], plot_df["worst_case_passenger_cost_reduction"])
    plt.title("Worst-Case Passenger Cost Reduction by Strategy")
    plt.ylabel("Worst-Case Passenger Cost Reduction")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_WORST, dpi=200)
    plt.close()

    plot_df = summary_df[summary_df["selected_actions"] > 0].copy()

    plt.figure(figsize=(10, 6))
    plt.scatter(
        plot_df["expected_passenger_cost_reduction"],
        plot_df["worst_case_passenger_cost_reduction"],
        s=np.maximum(plot_df["estimated_passengers_protected"] / 5, 30),
        alpha=0.7,
    )

    for _, row in plot_df.iterrows():
        plt.annotate(
            row["strategy"],
            (
                row["expected_passenger_cost_reduction"],
                row["worst_case_passenger_cost_reduction"],
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )

    plt.title("Expected vs Worst-Case Recovery Trade-off")
    plt.xlabel("Expected Passenger Cost Reduction")
    plt.ylabel("Worst-Case Passenger Cost Reduction")
    plt.tight_layout()
    plt.savefig(FIG_TRADEOFF, dpi=200)
    plt.close()

    heatmap_df = scenario_matrix.set_index("strategy")
    heatmap_values = heatmap_df.select_dtypes(include="number")

    if not heatmap_values.empty:
        plt.figure(figsize=(12, 6))
        plt.imshow(heatmap_values.values, aspect="auto")
        plt.colorbar(label="Passenger Cost Reduction")
        plt.xticks(
            ticks=np.arange(len(heatmap_values.columns)),
            labels=[c.replace("_cost_reduction", "") for c in heatmap_values.columns],
            rotation=35,
            ha="right"
        )
        plt.yticks(
            ticks=np.arange(len(heatmap_values.index)),
            labels=heatmap_values.index
        )
        plt.title("Recovery Strategy Performance Across Weather Scenarios")
        plt.tight_layout()
        plt.savefig(FIG_HEATMAP, dpi=200)
        plt.close()


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    scenarios = load_scenarios()
    base_df, input_path = load_recovery_base_data()

    scenario_df, scenario_value_cols, scenario_delay_cols = apply_weather_scenarios(base_df, scenarios)

    action_count = get_action_count(scenario_df)

    strategies = [
        "No Recovery",
        "Random Recovery",
        "Highest Base Delay",
        "Highest Base Passenger Cost",
        "Expected Scenario Value",
        "Worst-Case Robust",
        "Robust Balanced Recovery",
    ]

    rows = []
    selected_plans = []

    for strategy in strategies:
        selected = select_strategy(scenario_df, strategy, action_count)
        rows.append(summarize_strategy(strategy, selected, scenario_df, scenario_value_cols))

        temp = selected.copy()
        temp["strategy"] = strategy
        selected_plans.append(temp)

    summary_df = pd.DataFrame(rows)
    summary_df = summary_df.sort_values("expected_passenger_cost_reduction", ascending=False)

    robust_plan = pd.concat(selected_plans, ignore_index=True) if selected_plans else pd.DataFrame()

    scenario_matrix = build_scenario_matrix(summary_df, scenario_value_cols)

    robust_plan.to_csv(OUTPUT_PLAN, index=False)
    summary_df.to_csv(OUTPUT_SUMMARY, index=False)
    scenario_matrix.to_csv(OUTPUT_SCENARIO_MATRIX, index=False)

    report = build_report(summary_df, scenario_matrix, input_path, action_count, scenarios)
    OUTPUT_REPORT.write_text(report)

    save_figures(summary_df, scenario_matrix)

    print("\nRobust weather recovery optimization complete.")
    print(f"Input data: {input_path}")
    print(f"Weather config: {CONFIG_PATH}")
    print(f"Rows analyzed: {len(scenario_df):,}")
    print(f"Actions per strategy: {action_count}")
    print(f"Recovery plan: {OUTPUT_PLAN}")
    print(f"Summary: {OUTPUT_SUMMARY}")
    print(f"Scenario matrix: {OUTPUT_SCENARIO_MATRIX}")
    print(f"Report: {OUTPUT_REPORT}")
    print("Figures:")
    print(f"- {FIG_EXPECTED}")
    print(f"- {FIG_WORST}")
    print(f"- {FIG_HEATMAP}")
    print(f"- {FIG_TRADEOFF}")

    print("\nStrategy summary:")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
