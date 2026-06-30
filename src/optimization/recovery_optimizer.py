from pathlib import Path
import argparse
import json
import math
import shutil

import pandas as pd
import matplotlib.pyplot as plt
import pulp


SIMULATION_PATH = Path("data/processed/disruption_simulation_results.parquet")

PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")
FIGURES_DIR = Path("figures")

PLAN_PATH = PROCESSED_DIR / "optimized_recovery_plan.parquet"
METRICS_PATH = REPORTS_DIR / "recovery_optimization_metrics.json"
REPORT_PATH = REPORTS_DIR / "recovery_optimization_report.md"


def percentile_rank(series: pd.Series) -> pd.Series:
    return series.rank(pct=True).fillna(0)


def prepare_candidates(df: pd.DataFrame, recovery_effectiveness: float) -> pd.DataFrame:
    df = df.copy()

    required_cols = [
        "flight_date",
        "carrier",
        "flight_num",
        "origin",
        "dest",
        "scenario_stage",
        "baseline_positive_delay",
        "simulated_positive_delay",
        "delay_increase",
        "simulated_added_delay",
        "distance",
    ]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required simulation columns: {missing}")

    df = df[df["delay_increase"] > 0].copy()

    if df.empty:
        raise ValueError("No candidate flights with positive delay increase found.")

    df = df.reset_index(drop=True)
    df["candidate_id"] = df.index.astype(str)

    df["distance"] = pd.to_numeric(df["distance"], errors="coerce").fillna(
        df["distance"].median()
    )

    df["delay_increase"] = pd.to_numeric(
        df["delay_increase"], errors="coerce"
    ).fillna(0)

    df["simulated_positive_delay"] = pd.to_numeric(
        df["simulated_positive_delay"], errors="coerce"
    ).fillna(0)

    # Recovery benefit is the amount of delay we can reduce if this flight is prioritized.
    df["recoverable_delay"] = df["delay_increase"] * recovery_effectiveness

    # Add a light route/passenger proxy: longer flights often carry more operational and passenger impact.
    df["distance_rank"] = percentile_rank(df["distance"])

    df["priority_score"] = (
        df["recoverable_delay"] * (1 + 0.20 * df["distance_rank"])
    ).round(4)

    df["route"] = df["origin"] + " -> " + df["dest"]

    return df


def optimize_recovery(
    candidates: pd.DataFrame,
    max_actions: int,
    primary_actions: int,
    downstream_actions: int,
    carrier_share_limit: float,
    airport_share_limit: float,
) -> tuple[pd.DataFrame, dict]:
    max_actions = min(max_actions, len(candidates))

    problem = pulp.LpProblem(
        "Airline_Disruption_Recovery_Optimizer",
        pulp.LpMaximize,
    )

    x = {
        row.candidate_id: pulp.LpVariable(
            f"x_{row.candidate_id}",
            lowBound=0,
            upBound=1,
            cat="Binary",
        )
        for row in candidates.itertuples(index=False)
    }

    benefit = {
        row.candidate_id: row.priority_score
        for row in candidates.itertuples(index=False)
    }

    # Objective: maximize weighted recoverable delay.
    problem += pulp.lpSum(x[i] * benefit[i] for i in x)

    # Total recovery capacity.
    problem += pulp.lpSum(x[i] for i in x) <= max_actions, "total_recovery_actions"

    # Stage-specific capacity.
    primary_ids = candidates[
        candidates["scenario_stage"] == "primary_airport_disruption"
    ]["candidate_id"].tolist()

    downstream_ids = candidates[
        candidates["scenario_stage"] == "downstream_propagation"
    ]["candidate_id"].tolist()

    if primary_ids:
        problem += (
            pulp.lpSum(x[i] for i in primary_ids) <= min(primary_actions, len(primary_ids)),
            "primary_recovery_actions",
        )

    if downstream_ids:
        problem += (
            pulp.lpSum(x[i] for i in downstream_ids)
            <= min(downstream_actions, len(downstream_ids)),
            "downstream_recovery_actions",
        )

    # Fairness/concentration: avoid all recovery resources going to one carrier.
    carrier_limit = max(1, math.ceil(max_actions * carrier_share_limit))

    for carrier, group in candidates.groupby("carrier"):
        ids = group["candidate_id"].tolist()
        problem += (
            pulp.lpSum(x[i] for i in ids) <= carrier_limit,
            f"carrier_limit_{carrier}",
        )

    # Avoid concentrating every recovery action at one origin airport.
    airport_limit = max(1, math.ceil(max_actions * airport_share_limit))

    for airport, group in candidates.groupby("origin"):
        ids = group["candidate_id"].tolist()
        problem += (
            pulp.lpSum(x[i] for i in ids) <= airport_limit,
            f"airport_limit_{airport}",
        )

    cbc_path = shutil.which("cbc")

    if cbc_path:
        solver = pulp.COIN_CMD(path=cbc_path, msg=False)
    else:
        solver = pulp.PULP_CBC_CMD(msg=False)

    status = problem.solve(solver)

    status_name = pulp.LpStatus[status]

    candidates = candidates.copy()
    candidates["optimized_recovery_action"] = candidates["candidate_id"].apply(
        lambda i: int(round(pulp.value(x[i]) or 0))
    )

    candidates["optimized_recovered_delay"] = (
        candidates["optimized_recovery_action"] * candidates["recoverable_delay"]
    )

    candidates["optimized_positive_delay"] = (
        candidates["simulated_positive_delay"] - candidates["optimized_recovered_delay"]
    ).clip(lower=0)

    candidates["optimization_status"] = status_name

    metrics = {
        "optimization_status": status_name,
        "candidate_flights": int(len(candidates)),
        "max_recovery_actions": int(max_actions),
        "recovery_actions_used": int(candidates["optimized_recovery_action"].sum()),
        "primary_actions_used": int(
            candidates[
                candidates["scenario_stage"] == "primary_airport_disruption"
            ]["optimized_recovery_action"].sum()
        ),
        "downstream_actions_used": int(
            candidates[
                candidates["scenario_stage"] == "downstream_propagation"
            ]["optimized_recovery_action"].sum()
        ),
        "simulated_total_positive_delay_minutes": round(
            float(candidates["simulated_positive_delay"].sum()), 2
        ),
        "optimized_total_positive_delay_minutes": round(
            float(candidates["optimized_positive_delay"].sum()), 2
        ),
        "total_recovered_delay_minutes": round(
            float(candidates["optimized_recovered_delay"].sum()), 2
        ),
        "delay_reduction_pct": round(
            float(
                candidates["optimized_recovered_delay"].sum()
                / candidates["simulated_positive_delay"].sum()
                * 100
            ),
            2,
        ),
        "carrier_share_limit": carrier_share_limit,
        "airport_share_limit": airport_share_limit,
    }

    return candidates, metrics


def save_plots(plan: pd.DataFrame, metrics: dict) -> None:
    # Baseline/simulated/optimized comparison.
    comparison = pd.DataFrame(
        {
            "scenario": ["Simulated disruption", "Optimized recovery"],
            "total_positive_delay": [
                metrics["simulated_total_positive_delay_minutes"],
                metrics["optimized_total_positive_delay_minutes"],
            ],
        }
    )

    plt.figure(figsize=(8, 5))
    plt.bar(comparison["scenario"], comparison["total_positive_delay"])
    plt.ylabel("Total Positive Delay Minutes")
    plt.title("Simulated Disruption vs Optimized Recovery")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "optimized_vs_simulated_delay.png", dpi=200)
    plt.close()

    # Recovery actions by stage.
    stage_actions = (
        plan.groupby("scenario_stage")
        .agg(
            recovery_actions=("optimized_recovery_action", "sum"),
            recovered_delay=("optimized_recovered_delay", "sum"),
        )
        .reset_index()
        .sort_values("recovered_delay")
    )

    plt.figure(figsize=(8, 5))
    plt.barh(stage_actions["scenario_stage"], stage_actions["recovered_delay"])
    plt.xlabel("Recovered Delay Minutes")
    plt.ylabel("Scenario Stage")
    plt.title("Recovered Delay by Scenario Stage")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "recovered_delay_by_stage.png", dpi=200)
    plt.close()

    # Top recovered routes.
    route_plot = (
        plan[plan["optimized_recovery_action"] == 1]
        .groupby("route")
        .agg(recovered_delay=("optimized_recovered_delay", "sum"))
        .reset_index()
        .sort_values("recovered_delay", ascending=False)
        .head(15)
        .sort_values("recovered_delay")
    )

    if not route_plot.empty:
        plt.figure(figsize=(10, 7))
        plt.barh(route_plot["route"], route_plot["recovered_delay"])
        plt.xlabel("Recovered Delay Minutes")
        plt.ylabel("Route")
        plt.title("Top Routes Prioritized by Recovery Optimizer")
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "top_optimized_recovery_routes.png", dpi=200)
        plt.close()


def save_report(plan: pd.DataFrame, metrics: dict) -> None:
    selected = plan[plan["optimized_recovery_action"] == 1].copy()

    top_selected = selected.sort_values(
        "optimized_recovered_delay", ascending=False
    ).head(20)

    top_selected_table = top_selected[
        [
            "carrier",
            "flight_num",
            "origin",
            "dest",
            "scenario_stage",
            "simulated_positive_delay",
            "delay_increase",
            "optimized_recovered_delay",
            "priority_score",
        ]
    ].copy()

    for col in [
        "simulated_positive_delay",
        "delay_increase",
        "optimized_recovered_delay",
        "priority_score",
    ]:
        top_selected_table[col] = top_selected_table[col].round(2)

    stage_summary = (
        plan.groupby("scenario_stage")
        .agg(
            candidate_flights=("scenario_stage", "size"),
            recovery_actions=("optimized_recovery_action", "sum"),
            recovered_delay=("optimized_recovered_delay", "sum"),
            remaining_delay=("optimized_positive_delay", "sum"),
        )
        .reset_index()
    )

    stage_summary["recovered_delay"] = stage_summary["recovered_delay"].round(2)
    stage_summary["remaining_delay"] = stage_summary["remaining_delay"].round(2)

    carrier_summary = (
        selected.groupby("carrier")
        .agg(
            recovery_actions=("optimized_recovery_action", "sum"),
            recovered_delay=("optimized_recovered_delay", "sum"),
        )
        .reset_index()
        .sort_values("recovered_delay", ascending=False)
    )

    if not carrier_summary.empty:
        carrier_summary["recovered_delay"] = carrier_summary["recovered_delay"].round(2)

    report = "# Airline Disruption Recovery Optimization Report\n\n"

    report += "## Optimization Goal\n\n"
    report += (
        "The recovery optimizer selects a limited number of disrupted flights to prioritize "
        "in order to maximize recovered delay minutes while respecting operational capacity "
        "and fairness constraints.\n\n"
    )

    report += "## Optimization Summary\n\n"
    report += f"- Solver status: {metrics['optimization_status']}\n"
    report += f"- Candidate flights: {metrics['candidate_flights']:,}\n"
    report += f"- Max recovery actions allowed: {metrics['max_recovery_actions']:,}\n"
    report += f"- Recovery actions used: {metrics['recovery_actions_used']:,}\n"
    report += f"- Primary actions used: {metrics['primary_actions_used']:,}\n"
    report += f"- Downstream actions used: {metrics['downstream_actions_used']:,}\n"
    report += (
        f"- Simulated total positive delay: "
        f"{metrics['simulated_total_positive_delay_minutes']:,.2f} minutes\n"
    )
    report += (
        f"- Optimized total positive delay: "
        f"{metrics['optimized_total_positive_delay_minutes']:,.2f} minutes\n"
    )
    report += (
        f"- Total recovered delay: "
        f"{metrics['total_recovered_delay_minutes']:,.2f} minutes\n"
    )
    report += f"- Delay reduction: {metrics['delay_reduction_pct']}%\n\n"

    report += "## Impact by Scenario Stage\n\n"
    report += stage_summary.to_markdown(index=False)
    report += "\n\n"

    report += "## Recovery Actions by Carrier\n\n"
    if carrier_summary.empty:
        report += "No recovery actions selected.\n\n"
    else:
        report += carrier_summary.to_markdown(index=False)
        report += "\n\n"

    report += "## Top Flights Selected for Recovery\n\n"
    if top_selected_table.empty:
        report += "No flights selected for recovery.\n\n"
    else:
        report += top_selected_table.to_markdown(index=False)
        report += "\n\n"

    report += "## Interpretation\n\n"
    report += (
        "This model represents a first optimization layer for airline disruption recovery. "
        "It does not yet model full aircraft rotations, crew legality, or gate constraints. "
        "However, it establishes the central decision logic: when recovery capacity is limited, "
        "prioritize the flights that produce the largest system-level delay reduction while "
        "avoiding excessive concentration by carrier or airport. Later versions can extend this "
        "into mixed-integer aircraft recovery, passenger reaccommodation, and robust optimization.\n"
    )

    REPORT_PATH.write_text(report)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-actions", type=int, default=120)
    parser.add_argument("--primary-actions", type=int, default=80)
    parser.add_argument("--downstream-actions", type=int, default=100)
    parser.add_argument("--recovery-effectiveness", type=float, default=0.70)
    parser.add_argument("--carrier-share-limit", type=float, default=0.35)
    parser.add_argument("--airport-share-limit", type=float, default=0.40)

    args = parser.parse_args()

    if not SIMULATION_PATH.exists():
        raise FileNotFoundError(
            "Simulation results not found. Run: "
            "python src/simulation/disruption_simulator.py --airport DEN"
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    simulation_df = pd.read_parquet(SIMULATION_PATH)
    candidates = prepare_candidates(
        simulation_df,
        recovery_effectiveness=args.recovery_effectiveness,
    )

    plan, metrics = optimize_recovery(
        candidates=candidates,
        max_actions=args.max_actions,
        primary_actions=args.primary_actions,
        downstream_actions=args.downstream_actions,
        carrier_share_limit=args.carrier_share_limit,
        airport_share_limit=args.airport_share_limit,
    )

    plan.to_parquet(PLAN_PATH, index=False)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    save_plots(plan, metrics)
    save_report(plan, metrics)

    print("\nRecovery optimization complete.")
    print(json.dumps(metrics, indent=2))
    print(f"\nSaved optimized plan: {PLAN_PATH}")
    print(f"Saved metrics: {METRICS_PATH}")
    print(f"Saved report: {REPORT_PATH}")
    print("Saved figures:")
    print("- figures/optimized_vs_simulated_delay.png")
    print("- figures/recovered_delay_by_stage.png")
    print("- figures/top_optimized_recovery_routes.png")


if __name__ == "__main__":
    main()
