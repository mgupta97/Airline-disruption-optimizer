from pathlib import Path
import argparse
import json

import pandas as pd
import matplotlib.pyplot as plt


DATA_PATH = Path("data/processed/flights_clean.parquet")

PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")
FIGURES_DIR = Path("figures")

RESULTS_PATH = PROCESSED_DIR / "disruption_simulation_results.parquet"
METRICS_PATH = REPORTS_DIR / "disruption_simulation_metrics.json"
REPORT_PATH = REPORTS_DIR / "disruption_simulation_report.md"


def hhmm_to_minutes(value):
    if pd.isna(value):
        return None

    try:
        value = int(value)
    except ValueError:
        return None

    hour = value // 100
    minute = value % 100

    if hour == 24:
        hour = 0

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None

    return hour * 60 + minute


def choose_target_date(df: pd.DataFrame, airport: str) -> pd.Timestamp:
    airport_df = df[df["origin"] == airport].copy()

    if airport_df.empty:
        raise ValueError(f"No flights found for airport: {airport}")

    busiest_date = (
        airport_df.groupby("flight_date")
        .size()
        .sort_values(ascending=False)
        .index[0]
    )

    return pd.to_datetime(busiest_date)


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["flight_date"] = pd.to_datetime(df["flight_date"])
    df["crs_dep_minutes"] = df["crs_dep_time"].apply(hhmm_to_minutes)
    df["crs_arr_minutes"] = df["crs_arr_time"].apply(hhmm_to_minutes)

    if "arr_delay_minutes" in df.columns:
        df["baseline_arrival_delay"] = df["arr_delay_minutes"].fillna(0)
    else:
        df["baseline_arrival_delay"] = df["arr_delay"].fillna(0)

    df["baseline_positive_delay"] = df["baseline_arrival_delay"].clip(lower=0)

    return df


def simulate_airport_disruption(
    df: pd.DataFrame,
    airport: str,
    target_date: pd.Timestamp,
    start_hour: int,
    end_hour: int,
    primary_delay_minutes: int,
    propagation_window_hours: int,
    propagation_factor: float,
    max_propagated_delay: int,
) -> tuple[pd.DataFrame, dict]:
    start_minute = start_hour * 60
    end_minute = end_hour * 60
    propagation_end_minute = end_minute + propagation_window_hours * 60

    day_df = df[df["flight_date"] == target_date].copy()

    if day_df.empty:
        raise ValueError(f"No flights found on date: {target_date.date()}")

    operated_df = day_df[
        (day_df["cancelled"] == 0)
        & (day_df["diverted"] == 0)
        & day_df["crs_dep_minutes"].notna()
    ].copy()

    primary_mask = (
        (operated_df["origin"] == airport)
        & (operated_df["crs_dep_minutes"] >= start_minute)
        & (operated_df["crs_dep_minutes"] < end_minute)
    )

    primary_impacted = operated_df[primary_mask].copy()

    if primary_impacted.empty:
        raise ValueError(
            f"No primary impacted flights found for {airport} "
            f"on {target_date.date()} between {start_hour}:00 and {end_hour}:00"
        )

    primary_impacted["scenario_stage"] = "primary_airport_disruption"
    primary_impacted["simulated_added_delay"] = primary_delay_minutes

    destination_pressure = (
        primary_impacted.groupby("dest")
        .agg(
            delayed_inbound_flights=("dest", "size"),
            avg_primary_added_delay=("simulated_added_delay", "mean"),
        )
        .reset_index()
        .rename(columns={"dest": "origin"})
    )

    downstream_candidates = operated_df[
        (operated_df["origin"].isin(destination_pressure["origin"]))
        & (operated_df["crs_dep_minutes"] >= end_minute)
        & (operated_df["crs_dep_minutes"] <= propagation_end_minute)
    ].copy()

    downstream_impacted = downstream_candidates.merge(
        destination_pressure,
        on="origin",
        how="left",
    )

    downstream_impacted["simulated_added_delay"] = (
        downstream_impacted["delayed_inbound_flights"] * propagation_factor
    ).clip(upper=max_propagated_delay)

    downstream_impacted = downstream_impacted[
        downstream_impacted["simulated_added_delay"] > 0
    ].copy()

    downstream_impacted["scenario_stage"] = "downstream_propagation"

    primary_keys = set(
        zip(
            primary_impacted["flight_date"],
            primary_impacted["carrier"],
            primary_impacted["flight_num"],
            primary_impacted["origin"],
            primary_impacted["dest"],
            primary_impacted["crs_dep_time"],
        )
    )

    downstream_impacted["flight_key"] = list(
        zip(
            downstream_impacted["flight_date"],
            downstream_impacted["carrier"],
            downstream_impacted["flight_num"],
            downstream_impacted["origin"],
            downstream_impacted["dest"],
            downstream_impacted["crs_dep_time"],
        )
    )

    downstream_impacted = downstream_impacted[
        ~downstream_impacted["flight_key"].isin(primary_keys)
    ].copy()

    common_cols = [
        "flight_date",
        "carrier",
        "flight_num",
        "tail_num",
        "origin",
        "dest",
        "crs_dep_time",
        "crs_arr_time",
        "distance",
        "baseline_arrival_delay",
        "baseline_positive_delay",
        "scenario_stage",
        "simulated_added_delay",
    ]

    primary_final = primary_impacted[common_cols].copy()
    downstream_final = downstream_impacted[common_cols].copy()

    impacted = pd.concat([primary_final, downstream_final], ignore_index=True)

    impacted["simulated_arrival_delay"] = (
        impacted["baseline_arrival_delay"] + impacted["simulated_added_delay"]
    )

    impacted["simulated_positive_delay"] = impacted[
        "simulated_arrival_delay"
    ].clip(lower=0)

    impacted["delay_increase"] = (
        impacted["simulated_positive_delay"] - impacted["baseline_positive_delay"]
    ).clip(lower=0)

    stage_summary = (
        impacted.groupby("scenario_stage")
        .agg(
            impacted_flights=("scenario_stage", "size"),
            total_added_delay=("simulated_added_delay", "sum"),
            avg_added_delay=("simulated_added_delay", "mean"),
            total_delay_increase=("delay_increase", "sum"),
        )
        .reset_index()
    )

    metrics = {
        "airport": airport,
        "target_date": str(target_date.date()),
        "disruption_window": f"{start_hour}:00-{end_hour}:00",
        "primary_delay_minutes": primary_delay_minutes,
        "propagation_window_hours": propagation_window_hours,
        "primary_impacted_flights": int(len(primary_final)),
        "downstream_impacted_flights": int(len(downstream_final)),
        "total_impacted_flights": int(len(impacted)),
        "baseline_total_positive_delay_minutes": round(
            float(impacted["baseline_positive_delay"].sum()), 2
        ),
        "simulated_total_positive_delay_minutes": round(
            float(impacted["simulated_positive_delay"].sum()), 2
        ),
        "total_delay_increase_minutes": round(
            float(impacted["delay_increase"].sum()), 2
        ),
        "average_delay_increase_minutes": round(
            float(impacted["delay_increase"].mean()), 2
        ),
        "stage_summary": stage_summary.to_dict(orient="records"),
    }

    return impacted, metrics


def save_stage_plot(impacted: pd.DataFrame) -> None:
    stage_plot = (
        impacted.groupby("scenario_stage")
        .agg(total_delay_increase=("delay_increase", "sum"))
        .reset_index()
        .sort_values("total_delay_increase")
    )

    plt.figure(figsize=(8, 5))
    plt.barh(stage_plot["scenario_stage"], stage_plot["total_delay_increase"])
    plt.xlabel("Total Delay Increase Minutes")
    plt.ylabel("Scenario Stage")
    plt.title("Disruption Impact by Stage")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "disruption_impact_by_stage.png", dpi=200)
    plt.close()


def save_top_airports_plot(impacted: pd.DataFrame) -> None:
    airport_plot = (
        impacted.groupby("origin")
        .agg(total_delay_increase=("delay_increase", "sum"))
        .reset_index()
        .sort_values("total_delay_increase", ascending=False)
        .head(15)
        .sort_values("total_delay_increase")
    )

    plt.figure(figsize=(9, 6))
    plt.barh(airport_plot["origin"], airport_plot["total_delay_increase"])
    plt.xlabel("Total Delay Increase Minutes")
    plt.ylabel("Origin Airport")
    plt.title("Top Airports Affected by Simulated Disruption")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "disruption_top_affected_airports.png", dpi=200)
    plt.close()


def save_report(impacted: pd.DataFrame, metrics: dict) -> None:
    top_routes = (
        impacted.groupby(["origin", "dest"])
        .agg(
            impacted_flights=("origin", "size"),
            total_delay_increase=("delay_increase", "sum"),
            avg_delay_increase=("delay_increase", "mean"),
        )
        .reset_index()
        .sort_values("total_delay_increase", ascending=False)
        .head(20)
    )

    top_routes["route"] = top_routes["origin"] + " -> " + top_routes["dest"]
    top_routes["total_delay_increase"] = top_routes["total_delay_increase"].round(2)
    top_routes["avg_delay_increase"] = top_routes["avg_delay_increase"].round(2)

    stage_summary = pd.DataFrame(metrics["stage_summary"])

    report = "# Airport Disruption Simulation Report\n\n"

    report += "## Scenario\n\n"
    report += f"- Airport disrupted: {metrics['airport']}\n"
    report += f"- Date: {metrics['target_date']}\n"
    report += f"- Disruption window: {metrics['disruption_window']}\n"
    report += f"- Primary added delay: {metrics['primary_delay_minutes']} minutes\n"
    report += f"- Propagation window: {metrics['propagation_window_hours']} hours\n\n"

    report += "## Impact Summary\n\n"
    report += f"- Primary impacted flights: {metrics['primary_impacted_flights']:,}\n"
    report += f"- Downstream impacted flights: {metrics['downstream_impacted_flights']:,}\n"
    report += f"- Total impacted flights: {metrics['total_impacted_flights']:,}\n"
    report += (
        f"- Baseline total positive delay: "
        f"{metrics['baseline_total_positive_delay_minutes']:,.2f} minutes\n"
    )
    report += (
        f"- Simulated total positive delay: "
        f"{metrics['simulated_total_positive_delay_minutes']:,.2f} minutes\n"
    )
    report += (
        f"- Total delay increase: "
        f"{metrics['total_delay_increase_minutes']:,.2f} minutes\n"
    )
    report += (
        f"- Average delay increase per impacted flight: "
        f"{metrics['average_delay_increase_minutes']:,.2f} minutes\n\n"
    )

    report += "## Impact by Stage\n\n"
    report += stage_summary.to_markdown(index=False)
    report += "\n\n"

    report += "## Top Routes Affected\n\n"
    report += top_routes[
        ["route", "impacted_flights", "total_delay_increase", "avg_delay_increase"]
    ].to_markdown(index=False)
    report += "\n\n"

    report += "## Interpretation\n\n"
    report += (
        "This simulation approximates how a localized airport disruption can create "
        "both direct delays and downstream propagation. The primary disruption affects "
        "departures from the disrupted airport during the selected time window. "
        "Downstream propagation is estimated using delayed inbound pressure at connected "
        "destination airports. Later optimization steps will use this simulated impact "
        "to test recovery decisions such as delaying, prioritizing, or canceling flights.\n"
    )

    REPORT_PATH.write_text(report)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--airport", default="DEN")
    parser.add_argument("--date", default=None)
    parser.add_argument("--start-hour", type=int, default=8)
    parser.add_argument("--end-hour", type=int, default=14)
    parser.add_argument("--primary-delay", type=int, default=90)
    parser.add_argument("--propagation-window", type=int, default=6)
    parser.add_argument("--propagation-factor", type=float, default=8.0)
    parser.add_argument("--max-propagated-delay", type=int, default=60)

    args = parser.parse_args()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(DATA_PATH)
    df = prepare_data(df)

    airport = args.airport.upper()

    if args.date:
        target_date = pd.to_datetime(args.date)
    else:
        target_date = choose_target_date(df, airport)

    impacted, metrics = simulate_airport_disruption(
        df=df,
        airport=airport,
        target_date=target_date,
        start_hour=args.start_hour,
        end_hour=args.end_hour,
        primary_delay_minutes=args.primary_delay,
        propagation_window_hours=args.propagation_window,
        propagation_factor=args.propagation_factor,
        max_propagated_delay=args.max_propagated_delay,
    )

    impacted.to_parquet(RESULTS_PATH, index=False)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    save_stage_plot(impacted)
    save_top_airports_plot(impacted)
    save_report(impacted, metrics)

    print("\nDisruption simulation complete.")
    print(json.dumps(metrics, indent=2))
    print(f"\nSaved simulation results: {RESULTS_PATH}")
    print(f"Saved metrics: {METRICS_PATH}")
    print(f"Saved report: {REPORT_PATH}")
    print("Saved figures:")
    print("- figures/disruption_impact_by_stage.png")
    print("- figures/disruption_top_affected_airports.png")


if __name__ == "__main__":
    main()
