from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")
FIGURES_DIR = Path("figures")

PASSENGER_IMPACT_PATH = PROCESSED_DIR / "passenger_impact_simulation.parquet"

OPTIMIZED_CANDIDATES = [
    PROCESSED_DIR / "optimized_recovery_plan.parquet",
    PROCESSED_DIR / "optimized_recovery_plan.csv",
]

OUTPUT_SUMMARY = REPORTS_DIR / "passenger_aware_recovery_comparison.csv"
OUTPUT_REPORT = REPORTS_DIR / "passenger_aware_recovery_comparison_report.md"

FIG_COST = FIGURES_DIR / "passenger_aware_recovery_comparison.png"
FIG_DELAY = FIGURES_DIR / "passenger_aware_delay_recovery_comparison.png"
FIG_TRADEOFF = FIGURES_DIR / "passenger_aware_recovery_tradeoff.png"


def read_first_existing(paths):
    for path in paths:
        if path.exists():
            if path.suffix == ".parquet":
                return pd.read_parquet(path), path
            if path.suffix == ".csv":
                return pd.read_csv(path), path

    return None, None


def rank_pct(series):
    values = pd.to_numeric(series, errors="coerce").fillna(0)

    if values.nunique() <= 1:
        return pd.Series(0.5, index=series.index)

    return values.rank(pct=True)


def get_action_count(passenger_df):
    optimized_df, _ = read_first_existing(OPTIMIZED_CANDIDATES)

    population_size = len(passenger_df)

    if population_size == 0:
        return 0

    if optimized_df is not None and len(optimized_df) > 0:
        return min(len(optimized_df), population_size)

    default_count = min(50, max(10, int(population_size * 0.05)))

    return min(default_count, population_size)


def prepare_passenger_data(df):
    df = df.copy()

    required_cols = [
        "delay_minutes_std",
        "estimated_passengers",
        "connection_risk_score",
        "estimated_missed_connection_risk",
        "passenger_disruption_cost",
        "route",
        "origin_std",
        "dest_std",
        "carrier_std",
        "stage_std",
    ]

    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError(
            "Passenger impact data is missing required columns: "
            + ", ".join(missing)
            + ". Rerun PYTHONPATH=. python src/simulation/passenger_impact_simulator.py"
        )

    numeric_cols = [
        "delay_minutes_std",
        "estimated_passengers",
        "connection_risk_score",
        "estimated_missed_connection_risk",
        "passenger_disruption_cost",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df[
        (df["delay_minutes_std"] > 0)
        & (df["passenger_disruption_cost"] > 0)
    ].copy()

    df["delay_score"] = rank_pct(df["delay_minutes_std"])
    df["passenger_cost_score"] = rank_pct(df["passenger_disruption_cost"])
    df["connection_risk_rank"] = rank_pct(df["connection_risk_score"])
    df["missed_connection_rank"] = rank_pct(df["estimated_missed_connection_risk"])

    route_frequency = df.groupby("route")["delay_minutes_std"].transform("count")
    airport_frequency = (
        df.groupby("origin_std")["delay_minutes_std"].transform("count")
        + df.groupby("dest_std")["delay_minutes_std"].transform("count")
    )

    df["route_frequency_score"] = rank_pct(route_frequency)
    df["airport_frequency_score"] = rank_pct(airport_frequency)

    df["hybrid_delay_passenger_score"] = (
        0.50 * df["delay_score"]
        + 0.50 * df["passenger_cost_score"]
    )

    df["connection_priority_score"] = (
        0.45 * df["connection_risk_rank"]
        + 0.35 * df["missed_connection_rank"]
        + 0.20 * df["airport_frequency_score"]
    )

    df["customer_recovery_score"] = (
        0.45 * df["passenger_cost_score"]
        + 0.30 * df["missed_connection_rank"]
        + 0.15 * df["delay_score"]
        + 0.10 * df["airport_frequency_score"]
    )

    return df.reset_index(drop=True)


def select_strategy(df, strategy_name, action_count):
    action_count = min(action_count, len(df))

    if strategy_name == "No Recovery" or action_count == 0:
        return df.iloc[0:0].copy()

    if strategy_name == "Random Recovery":
        return df.sample(n=action_count, random_state=42).copy()

    if strategy_name == "Highest Delay First":
        return df.sort_values("delay_minutes_std", ascending=False).head(action_count).copy()

    if strategy_name == "Highest Passenger Cost First":
        return df.sort_values("passenger_disruption_cost", ascending=False).head(action_count).copy()

    if strategy_name == "Highest Connection Risk First":
        return df.sort_values("connection_priority_score", ascending=False).head(action_count).copy()

    if strategy_name == "Highest Missed Connection Risk First":
        return df.sort_values("estimated_missed_connection_risk", ascending=False).head(action_count).copy()

    if strategy_name == "Hybrid Delay + Passenger Impact":
        return df.sort_values("hybrid_delay_passenger_score", ascending=False).head(action_count).copy()

    if strategy_name == "Customer Impact Optimized":
        return df.sort_values("customer_recovery_score", ascending=False).head(action_count).copy()

    raise ValueError(f"Unknown strategy: {strategy_name}")


def summarize_strategy(strategy_name, selected_df, all_df):
    total_delay = all_df["delay_minutes_std"].sum()
    total_cost = all_df["passenger_disruption_cost"].sum()
    total_passengers = all_df["estimated_passengers"].sum()
    total_missed_connection_risk = all_df["estimated_missed_connection_risk"].sum()

    recovered_delay = selected_df["delay_minutes_std"].sum()
    reduced_cost = selected_df["passenger_disruption_cost"].sum()
    protected_passengers = selected_df["estimated_passengers"].sum()
    reduced_missed_connection_risk = selected_df["estimated_missed_connection_risk"].sum()

    return {
        "strategy": strategy_name,
        "selected_actions": len(selected_df),
        "delay_minutes_recovered": recovered_delay,
        "delay_recovery_rate": recovered_delay / total_delay if total_delay else 0,
        "passenger_disruption_cost_reduced": reduced_cost,
        "passenger_cost_reduction_rate": reduced_cost / total_cost if total_cost else 0,
        "estimated_passengers_protected": protected_passengers,
        "passenger_protection_rate": protected_passengers / total_passengers if total_passengers else 0,
        "missed_connection_risk_reduced": reduced_missed_connection_risk,
        "missed_connection_reduction_rate": (
            reduced_missed_connection_risk / total_missed_connection_risk
            if total_missed_connection_risk else 0
        ),
        "avg_cost_reduced_per_action": reduced_cost / len(selected_df) if len(selected_df) else 0,
        "avg_delay_recovered_per_action": recovered_delay / len(selected_df) if len(selected_df) else 0,
        "routes_covered": selected_df["route"].nunique() if len(selected_df) else 0,
        "origin_airports_covered": selected_df["origin_std"].nunique() if len(selected_df) else 0,
        "carriers_covered": selected_df["carrier_std"].nunique() if len(selected_df) else 0,
    }


def markdown_table(df):
    try:
        return df.to_markdown(index=False)
    except Exception:
        return "```\n" + df.to_string(index=False) + "\n```"


def build_report(summary_df, action_count):
    display = summary_df.copy()
    numeric_cols = display.select_dtypes(include="number").columns
    display[numeric_cols] = display[numeric_cols].round(4)

    best_cost = summary_df.sort_values(
        "passenger_disruption_cost_reduced",
        ascending=False
    ).iloc[0]

    best_delay = summary_df.sort_values(
        "delay_minutes_recovered",
        ascending=False
    ).iloc[0]

    report = "# Passenger-Aware Recovery Strategy Comparison\n\n"

    report += "## Objective\n\n"
    report += (
        "This report compares airline recovery strategies using both operational and "
        "customer-impact metrics. Instead of evaluating recovery only by delay minutes, "
        "the benchmark also measures passenger disruption cost, estimated passengers "
        "protected, and missed-connection risk reduction.\n\n"
    )

    report += "## Recovery Actions Compared\n\n"
    report += f"Each strategy selects **{action_count} recovery actions** from the disrupted flight set.\n\n"

    report += "## Strategy Summary\n\n"
    report += markdown_table(display)
    report += "\n\n"

    report += "## Key Results\n\n"
    report += (
        f"- Best strategy by passenger disruption cost reduction: "
        f"**{best_cost['strategy']}**, reducing "
        f"**{best_cost['passenger_disruption_cost_reduced']:.0f}** cost-proxy units.\n"
    )

    report += (
        f"- Best strategy by delay recovery: "
        f"**{best_delay['strategy']}**, recovering "
        f"**{best_delay['delay_minutes_recovered']:.0f}** delay minutes.\n\n"
    )

    report += "## Interpretation\n\n"
    report += (
        "This passenger-aware benchmark shows that the best operational strategy is not "
        "always the best customer-impact strategy. A delay-first policy may recover more "
        "minutes, while a passenger-impact policy may better protect high-risk routes, hub "
        "banks, and missed connections. This makes the project more realistic because airline "
        "recovery decisions must balance operational efficiency with passenger disruption.\n"
    )

    return report


def save_figures(summary_df):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    plot_df = summary_df.sort_values(
        "passenger_disruption_cost_reduced",
        ascending=False
    )

    plt.figure(figsize=(12, 6))
    plt.bar(plot_df["strategy"], plot_df["passenger_disruption_cost_reduced"])
    plt.title("Passenger Disruption Cost Reduced by Strategy")
    plt.ylabel("Passenger Disruption Cost Reduced")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_COST, dpi=200)
    plt.close()

    plot_df = summary_df.sort_values(
        "delay_minutes_recovered",
        ascending=False
    )

    plt.figure(figsize=(12, 6))
    plt.bar(plot_df["strategy"], plot_df["delay_minutes_recovered"])
    plt.title("Delay Minutes Recovered by Strategy")
    plt.ylabel("Delay Minutes Recovered")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_DELAY, dpi=200)
    plt.close()

    plot_df = summary_df[summary_df["selected_actions"] > 0].copy()

    plt.figure(figsize=(10, 6))
    plt.scatter(
        plot_df["delay_minutes_recovered"],
        plot_df["passenger_disruption_cost_reduced"],
        s=np.maximum(plot_df["estimated_passengers_protected"] / 5, 30),
        alpha=0.7,
    )

    for _, row in plot_df.iterrows():
        plt.annotate(
            row["strategy"],
            (
                row["delay_minutes_recovered"],
                row["passenger_disruption_cost_reduced"],
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )

    plt.title("Passenger Cost Reduction vs Delay Recovery")
    plt.xlabel("Delay Minutes Recovered")
    plt.ylabel("Passenger Disruption Cost Reduced")
    plt.tight_layout()
    plt.savefig(FIG_TRADEOFF, dpi=200)
    plt.close()


def main():
    if not PASSENGER_IMPACT_PATH.exists():
        raise FileNotFoundError(
            f"Missing {PASSENGER_IMPACT_PATH}. Run:\n"
            "PYTHONPATH=. python src/simulation/passenger_impact_simulator.py"
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    passenger_df = pd.read_parquet(PASSENGER_IMPACT_PATH)
    passenger_df = prepare_passenger_data(passenger_df)

    action_count = get_action_count(passenger_df)

    strategies = [
        "No Recovery",
        "Random Recovery",
        "Highest Delay First",
        "Highest Passenger Cost First",
        "Highest Connection Risk First",
        "Highest Missed Connection Risk First",
        "Hybrid Delay + Passenger Impact",
        "Customer Impact Optimized",
    ]

    rows = []

    for strategy in strategies:
        selected = select_strategy(passenger_df, strategy, action_count)
        rows.append(summarize_strategy(strategy, selected, passenger_df))

    summary_df = pd.DataFrame(rows)
    summary_df = summary_df.sort_values(
        "passenger_disruption_cost_reduced",
        ascending=False
    )

    summary_df.to_csv(OUTPUT_SUMMARY, index=False)

    report = build_report(summary_df, action_count)
    OUTPUT_REPORT.write_text(report)

    save_figures(summary_df)

    print("\nPassenger-aware recovery comparison complete.")
    print(f"Passenger impact input: {PASSENGER_IMPACT_PATH}")
    print(f"Rows analyzed: {len(passenger_df):,}")
    print(f"Actions per strategy: {action_count}")
    print(f"Summary: {OUTPUT_SUMMARY}")
    print(f"Report: {OUTPUT_REPORT}")
    print(f"Figures:")
    print(f"- {FIG_COST}")
    print(f"- {FIG_DELAY}")
    print(f"- {FIG_TRADEOFF}")

    print("\nStrategy comparison:")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
