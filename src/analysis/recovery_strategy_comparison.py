from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")
FIGURES_DIR = Path("figures")

SIMULATION_CANDIDATES = [
    PROCESSED_DIR / "disruption_simulation_results.parquet",
    PROCESSED_DIR / "disruption_simulation_results.csv",
]

OPTIMIZED_CANDIDATES = [
    PROCESSED_DIR / "optimized_recovery_plan.parquet",
    PROCESSED_DIR / "optimized_recovery_plan.csv",
]

OUTPUT_SUMMARY = REPORTS_DIR / "recovery_strategy_comparison.csv"
OUTPUT_REPORT = REPORTS_DIR / "recovery_strategy_comparison_report.md"
OUTPUT_FIGURE = FIGURES_DIR / "recovery_strategy_comparison.png"


def read_first_existing(paths):
    for path in paths:
        if path.exists():
            if path.suffix == ".parquet":
                return pd.read_parquet(path), path
            if path.suffix == ".csv":
                return pd.read_csv(path), path

    raise FileNotFoundError(
        "Could not find any of these files:\n"
        + "\n".join(str(p) for p in paths)
    )


def find_column(df, candidates):
    normalized = {c.lower().strip(): c for c in df.columns}

    for candidate in candidates:
        key = candidate.lower().strip()
        if key in normalized:
            return normalized[key]

    for col in df.columns:
        col_lower = col.lower()
        if any(candidate.lower() in col_lower for candidate in candidates):
            return col

    return None


def standardize_simulation(df):
    df = df.copy()

    delay_col = find_column(
        df,
        [
            "recoverable_delay_minutes",
            "added_delay_minutes",
            "positive_delay_minutes",
            "total_added_delay",
            "arrival_delay",
            "arr_delay",
            "delay_minutes",
            "simulated_delay",
        ],
    )

    if delay_col is None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            raise ValueError("No numeric columns found to estimate recovery value.")
        delay_col = numeric_cols[0]

    df["recovery_value"] = pd.to_numeric(df[delay_col], errors="coerce").fillna(0)
    df["recovery_value"] = df["recovery_value"].clip(lower=0)

    carrier_col = find_column(df, ["carrier", "airline", "op_unique_carrier"])
    origin_col = find_column(df, ["origin", "origin_airport"])
    dest_col = find_column(df, ["dest", "destination", "dest_airport"])
    stage_col = find_column(df, ["impact_stage", "stage", "disruption_stage"])

    if carrier_col:
        df["carrier_std"] = df[carrier_col].astype(str)
    else:
        df["carrier_std"] = "Unknown"

    if origin_col:
        df["origin_std"] = df[origin_col].astype(str)
    else:
        df["origin_std"] = "Unknown"

    if dest_col:
        df["dest_std"] = df[dest_col].astype(str)
    else:
        df["dest_std"] = "Unknown"

    if stage_col:
        df["stage_std"] = df[stage_col].astype(str)
    else:
        df["stage_std"] = "Unknown"

    network_cols = [
        c for c in df.columns
        if any(k in c.lower() for k in ["pagerank", "centrality", "criticality", "risk_score"])
    ]

    if network_cols:
        score = pd.Series(0.0, index=df.index)
        for col in network_cols:
            values = pd.to_numeric(df[col], errors="coerce")
            if values.notna().sum() > 0:
                values = values.fillna(values.median())
                if values.max() != values.min():
                    values = (values - values.min()) / (values.max() - values.min())
                else:
                    values = values * 0
                score += values
        df["network_priority_score"] = score
    else:
        route_volume_proxy = df.groupby(["origin_std", "dest_std"])["recovery_value"].transform("count")
        df["network_priority_score"] = route_volume_proxy

    df["delay_first_score"] = df["recovery_value"]
    df["network_first_score"] = df["network_priority_score"] * df["recovery_value"]
    df["primary_first_score"] = (
        df["stage_std"].str.lower().str.contains("primary").astype(int) * 100000
        + df["recovery_value"]
    )

    df = df[df["recovery_value"] > 0].copy()
    df = df.reset_index(drop=True)

    return df


def get_action_count(optimized_df, simulation_df):
    population_size = len(simulation_df)

    if population_size == 0:
        return 0

    if optimized_df is not None and len(optimized_df) > 0:
        return min(len(optimized_df), population_size)

    default_count = min(50, max(10, int(population_size * 0.05)))

    return min(default_count, population_size)


def select_strategy(df, strategy_name, action_count):
    action_count = min(action_count, len(df))

    if strategy_name == "No Recovery" or action_count == 0:
        return df.iloc[0:0].copy()

    if strategy_name == "Random Recovery":
        return df.sample(n=action_count, random_state=42).copy()

    if strategy_name == "Highest Delay First":
        return df.sort_values("delay_first_score", ascending=False).head(action_count).copy()

    if strategy_name == "Primary Impact First":
        return df.sort_values("primary_first_score", ascending=False).head(action_count).copy()

    if strategy_name == "Network Criticality First":
        return df.sort_values("network_first_score", ascending=False).head(action_count).copy()

    if strategy_name == "Hybrid Delay + Network":
        temp = df.copy()
        temp["hybrid_score"] = (
            0.70 * rank_pct(temp["recovery_value"])
            + 0.30 * rank_pct(temp["network_priority_score"])
        )
        return temp.sort_values("hybrid_score", ascending=False).head(action_count).copy()

    raise ValueError(f"Unknown strategy: {strategy_name}")


def rank_pct(series):
    return pd.to_numeric(series, errors="coerce").fillna(0).rank(pct=True)


def summarize_strategy(strategy_name, selected_df, all_df):
    total_delay = all_df["recovery_value"].sum()
    recovered_delay = selected_df["recovery_value"].sum()
    remaining_delay = total_delay - recovered_delay

    row = {
        "strategy": strategy_name,
        "selected_actions": len(selected_df),
        "recovered_delay_minutes": recovered_delay,
        "remaining_delay_minutes": remaining_delay,
        "recovery_rate": recovered_delay / total_delay if total_delay > 0 else 0,
        "avg_recovery_per_action": recovered_delay / len(selected_df) if len(selected_df) > 0 else 0,
        "carriers_affected": selected_df["carrier_std"].nunique() if len(selected_df) else 0,
        "origin_airports_affected": selected_df["origin_std"].nunique() if len(selected_df) else 0,
        "dest_airports_affected": selected_df["dest_std"].nunique() if len(selected_df) else 0,
        "primary_actions": selected_df["stage_std"].str.lower().str.contains("primary").sum() if len(selected_df) else 0,
        "downstream_actions": selected_df["stage_std"].str.lower().str.contains("downstream").sum() if len(selected_df) else 0,
    }

    return row


def summarize_optimized_strategy(optimized_df, all_df):
    opt = standardize_simulation(optimized_df)

    return summarize_strategy("Optimized Recovery Plan", opt, all_df)


def build_report(summary_df, simulation_path, optimized_path, action_count):
    best = summary_df.sort_values("recovered_delay_minutes", ascending=False).iloc[0]

    report = "# Recovery Strategy Comparison Report\n\n"

    report += "## Objective\n\n"
    report += (
        "This report compares the optimized recovery plan against simple operational "
        "heuristics. The goal is to evaluate whether the optimization model provides "
        "better recovery value than baseline rules such as random selection, highest-delay-first, "
        "primary-impact-first, and network-criticality-first recovery.\n\n"
    )

    report += "## Input Files\n\n"
    report += f"- Simulation input: `{simulation_path}`\n"
    report += f"- Optimized recovery input: `{optimized_path if optimized_path else 'Not available'}`\n"
    report += f"- Recovery actions compared per strategy: `{action_count}`\n\n"

    report += "## Strategy Summary\n\n"

    display = summary_df.copy()
    numeric_cols = display.select_dtypes(include="number").columns
    display[numeric_cols] = display[numeric_cols].round(4)

    try:
        report += display.to_markdown(index=False)
    except Exception:
        report += "```\n" + display.to_string(index=False) + "\n```"

    report += "\n\n"

    report += "## Key Result\n\n"
    report += (
        f"The best-performing strategy was **{best['strategy']}**, recovering "
        f"**{best['recovered_delay_minutes']:.0f} delay minutes** with a recovery rate of "
        f"**{best['recovery_rate']:.2%}**.\n\n"
    )

    report += "## Interpretation\n\n"
    report += (
        "This benchmark makes the recovery optimizer more credible because it is no longer "
        "evaluated in isolation. It is compared against practical baseline rules that an "
        "operations team might use during a disruption. If the optimized recovery plan "
        "outperforms these baselines, it provides stronger evidence that the optimization "
        "model adds decision value.\n"
    )

    return report


def save_figure(summary_df):
    plot_df = summary_df.sort_values("recovered_delay_minutes", ascending=False)

    plt.figure(figsize=(12, 6))
    plt.bar(plot_df["strategy"], plot_df["recovered_delay_minutes"])
    plt.title("Recovered Delay Minutes by Recovery Strategy")
    plt.ylabel("Recovered Delay Minutes")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(OUTPUT_FIGURE, dpi=200)
    plt.close()


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    raw_sim_df, simulation_path = read_first_existing(SIMULATION_CANDIDATES)

    try:
        raw_opt_df, optimized_path = read_first_existing(OPTIMIZED_CANDIDATES)
    except FileNotFoundError:
        raw_opt_df = None
        optimized_path = None

    sim_df = standardize_simulation(raw_sim_df)
    action_count = get_action_count(raw_opt_df, sim_df)

    strategies = [
        "No Recovery",
        "Random Recovery",
        "Highest Delay First",
        "Primary Impact First",
        "Network Criticality First",
        "Hybrid Delay + Network",
    ]

    rows = []

    for strategy in strategies:
        selected = select_strategy(sim_df, strategy, action_count)
        rows.append(summarize_strategy(strategy, selected, sim_df))

    if raw_opt_df is not None:
        rows.append(summarize_optimized_strategy(raw_opt_df, sim_df))

    summary_df = pd.DataFrame(rows)
    summary_df = summary_df.sort_values("recovered_delay_minutes", ascending=False)

    summary_df.to_csv(OUTPUT_SUMMARY, index=False)

    report = build_report(summary_df, simulation_path, optimized_path, action_count)
    OUTPUT_REPORT.write_text(report)

    save_figure(summary_df)

    print("\nRecovery strategy comparison complete.")
    print(f"Simulation file: {simulation_path}")
    print(f"Optimized file: {optimized_path if optimized_path else 'Not found'}")
    print(f"Candidate recovery actions: {len(sim_df):,}")
    print(f"Actions per strategy: {action_count}")
    print(f"Summary saved to: {OUTPUT_SUMMARY}")
    print(f"Report saved to: {OUTPUT_REPORT}")
    print(f"Figure saved to: {OUTPUT_FIGURE}")

    print("\nStrategy comparison:")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
