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

OUTPUT_DATA = PROCESSED_DIR / "passenger_impact_simulation.parquet"
OUTPUT_SUMMARY = REPORTS_DIR / "passenger_impact_summary.csv"
OUTPUT_REPORT = REPORTS_DIR / "passenger_impact_report.md"

FIG_ROUTE_COST = FIGURES_DIR / "passenger_disruption_cost_by_route.png"
FIG_AIRPORT_RISK = FIGURES_DIR / "top_connection_risk_airports.png"
FIG_STAGE_IMPACT = FIGURES_DIR / "passenger_impact_by_stage.png"


def read_first_existing(paths):
    for path in paths:
        if path.exists():
            if path.suffix == ".parquet":
                return pd.read_parquet(path), path
            if path.suffix == ".csv":
                return pd.read_csv(path), path

    raise FileNotFoundError(
        "Could not find disruption simulation output. Run:\n"
        "PYTHONPATH=. python src/simulation/disruption_simulator.py\n\n"
        "Expected one of:\n"
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


def rank_pct(series):
    values = pd.to_numeric(series, errors="coerce").fillna(0)

    if values.nunique() <= 1:
        return pd.Series(0.5, index=series.index)

    return values.rank(pct=True)


def standardize_columns(df):
    df = df.copy()

    delay_col = find_column(
        df,
        [
            "added_delay_minutes",
            "recoverable_delay_minutes",
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
            raise ValueError("No numeric delay-like column found in simulation output.")
        delay_col = numeric_cols[0]

    carrier_col = find_column(df, ["carrier", "airline", "op_unique_carrier"])
    origin_col = find_column(df, ["origin", "origin_airport"])
    dest_col = find_column(df, ["dest", "destination", "dest_airport"])
    stage_col = find_column(df, ["impact_stage", "stage", "disruption_stage"])

    dep_hour_col = find_column(df, ["dep_hour", "departure_hour", "scheduled_dep_hour"])
    arr_hour_col = find_column(df, ["arr_hour", "arrival_hour", "scheduled_arr_hour"])

    df["delay_minutes_std"] = pd.to_numeric(df[delay_col], errors="coerce").fillna(0).clip(lower=0)
    df["carrier_std"] = df[carrier_col].astype(str) if carrier_col else "Unknown"
    df["origin_std"] = df[origin_col].astype(str) if origin_col else "Unknown"
    df["dest_std"] = df[dest_col].astype(str) if dest_col else "Unknown"
    df["stage_std"] = df[stage_col].astype(str) if stage_col else "Unknown"

    if dep_hour_col:
        df["dep_hour_std"] = pd.to_numeric(df[dep_hour_col], errors="coerce")
    else:
        df["dep_hour_std"] = np.nan

    if arr_hour_col:
        df["arr_hour_std"] = pd.to_numeric(df[arr_hour_col], errors="coerce")
    else:
        df["arr_hour_std"] = np.nan

    df = df[df["delay_minutes_std"] > 0].copy()
    df = df.reset_index(drop=True)

    return df


def add_passenger_impact_features(df):
    df = df.copy()

    route_key = df["origin_std"] + "-" + df["dest_std"]

    route_frequency = df.groupby(route_key)["delay_minutes_std"].transform("count")
    carrier_frequency = df.groupby("carrier_std")["delay_minutes_std"].transform("count")

    origin_volume = df.groupby("origin_std")["delay_minutes_std"].transform("count")
    dest_volume = df.groupby("dest_std")["delay_minutes_std"].transform("count")
    airport_volume_proxy = origin_volume + dest_volume

    route_score = rank_pct(route_frequency)
    carrier_score = rank_pct(carrier_frequency)
    hub_score = rank_pct(airport_volume_proxy)

    stage_text = df["stage_std"].str.lower()

    primary_multiplier = np.where(stage_text.str.contains("primary"), 1.00, 0.80)
    downstream_multiplier = np.where(stage_text.str.contains("downstream"), 0.90, 1.00)

    # Passenger count proxy:
    # Larger route frequency + carrier scale suggests higher passenger exposure.
    df["estimated_passengers"] = (
        70
        + 120 * route_score
        + 40 * carrier_score
    ) * primary_multiplier * downstream_multiplier

    df["estimated_passengers"] = df["estimated_passengers"].clip(50, 260).round()

    delay_risk = (df["delay_minutes_std"] / 120).clip(0, 1)

    # If hour data exists, morning/evening banks receive a higher connection-risk weight.
    dep_hour = pd.to_numeric(df["dep_hour_std"], errors="coerce")
    arr_hour = pd.to_numeric(df["arr_hour_std"], errors="coerce")

    bank_hour_risk = (
        dep_hour.between(6, 10).astype(float)
        + dep_hour.between(16, 20).astype(float)
        + arr_hour.between(6, 10).astype(float)
        + arr_hour.between(16, 20).astype(float)
    ) / 4

    bank_hour_risk = bank_hour_risk.fillna(0.5)

    df["connection_risk_score"] = (
        100
        * (
            0.45 * hub_score
            + 0.35 * delay_risk
            + 0.20 * bank_hour_risk
        )
    ).clip(0, 100).round(2)

    df["estimated_missed_connection_risk"] = (
        df["connection_risk_score"] / 100
        * df["estimated_passengers"]
        * (df["delay_minutes_std"] / 90).clip(0, 1.5)
    ).round(2)

    df["passenger_disruption_cost"] = (
        df["estimated_passengers"]
        * df["delay_minutes_std"]
        * (1 + df["connection_risk_score"] / 100)
    ).round(2)

    df["route"] = route_key

    return df


def build_summary(df):
    summary = {
        "disrupted_records": len(df),
        "total_delay_minutes": df["delay_minutes_std"].sum(),
        "estimated_passengers_affected": df["estimated_passengers"].sum(),
        "estimated_missed_connection_risk": df["estimated_missed_connection_risk"].sum(),
        "total_passenger_disruption_cost": df["passenger_disruption_cost"].sum(),
        "avg_connection_risk_score": df["connection_risk_score"].mean(),
        "top_origin_airport_by_cost": df.groupby("origin_std")["passenger_disruption_cost"].sum().idxmax(),
        "top_route_by_cost": df.groupby("route")["passenger_disruption_cost"].sum().idxmax(),
    }

    return pd.DataFrame([summary])


def markdown_table(df):
    try:
        return df.to_markdown(index=False)
    except Exception:
        return "```\n" + df.to_string(index=False) + "\n```"


def build_report(df, summary_df, input_path):
    top_routes = (
        df.groupby("route")
        .agg(
            records=("route", "size"),
            delay_minutes=("delay_minutes_std", "sum"),
            estimated_passengers=("estimated_passengers", "sum"),
            missed_connection_risk=("estimated_missed_connection_risk", "sum"),
            passenger_disruption_cost=("passenger_disruption_cost", "sum"),
        )
        .reset_index()
        .sort_values("passenger_disruption_cost", ascending=False)
        .head(15)
    )

    top_airports = (
        df.groupby("origin_std")
        .agg(
            records=("origin_std", "size"),
            delay_minutes=("delay_minutes_std", "sum"),
            estimated_passengers=("estimated_passengers", "sum"),
            avg_connection_risk=("connection_risk_score", "mean"),
            passenger_disruption_cost=("passenger_disruption_cost", "sum"),
        )
        .reset_index()
        .rename(columns={"origin_std": "origin_airport"})
        .sort_values("passenger_disruption_cost", ascending=False)
        .head(15)
    )

    stage_summary = (
        df.groupby("stage_std")
        .agg(
            records=("stage_std", "size"),
            delay_minutes=("delay_minutes_std", "sum"),
            estimated_passengers=("estimated_passengers", "sum"),
            missed_connection_risk=("estimated_missed_connection_risk", "sum"),
            passenger_disruption_cost=("passenger_disruption_cost", "sum"),
        )
        .reset_index()
        .sort_values("passenger_disruption_cost", ascending=False)
    )

    report = "# Passenger Impact Simulation Report\n\n"

    report += "## Objective\n\n"
    report += (
        "This module estimates the passenger-level impact of an airline disruption using "
        "proxy features derived from route frequency, carrier scale, airport hub exposure, "
        "delay severity, and connection-bank timing. The purpose is to move beyond delay "
        "minutes alone and estimate which disrupted flights, routes, and airports create "
        "the highest customer impact.\n\n"
    )

    report += "## Input\n\n"
    report += f"- Disruption simulation file: `{input_path}`\n\n"

    report += "## Overall Summary\n\n"
    report += markdown_table(summary_df)
    report += "\n\n"

    report += "## Top Routes by Passenger Disruption Cost\n\n"
    report += markdown_table(top_routes)
    report += "\n\n"

    report += "## Top Origin Airports by Passenger Disruption Cost\n\n"
    report += markdown_table(top_airports)
    report += "\n\n"

    report += "## Impact by Disruption Stage\n\n"
    report += markdown_table(stage_summary)
    report += "\n\n"

    report += "## Interpretation\n\n"
    report += (
        "Passenger disruption cost is a proxy metric, not a true accounting cost. It combines "
        "estimated passengers, delay minutes, and missed-connection risk. This helps prioritize "
        "recovery actions that may matter more from a customer-impact perspective, not just from "
        "an operational delay-minimization perspective.\n"
    )

    return report


def save_figures(df):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    route_cost = (
        df.groupby("route")["passenger_disruption_cost"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )

    plt.figure(figsize=(12, 6))
    plt.bar(route_cost.index, route_cost.values)
    plt.title("Top Routes by Passenger Disruption Cost")
    plt.ylabel("Passenger Disruption Cost Proxy")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_ROUTE_COST, dpi=200)
    plt.close()

    airport_risk = (
        df.groupby("origin_std")["connection_risk_score"]
        .mean()
        .sort_values(ascending=False)
        .head(15)
    )

    plt.figure(figsize=(12, 6))
    plt.bar(airport_risk.index, airport_risk.values)
    plt.title("Top Origin Airports by Average Connection Risk")
    plt.ylabel("Average Connection Risk Score")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_AIRPORT_RISK, dpi=200)
    plt.close()

    stage_cost = (
        df.groupby("stage_std")["passenger_disruption_cost"]
        .sum()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(10, 5))
    plt.bar(stage_cost.index.astype(str), stage_cost.values)
    plt.title("Passenger Impact by Disruption Stage")
    plt.ylabel("Passenger Disruption Cost Proxy")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_STAGE_IMPACT, dpi=200)
    plt.close()


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    raw_df, input_path = read_first_existing(SIMULATION_CANDIDATES)

    df = standardize_columns(raw_df)
    df = add_passenger_impact_features(df)

    summary_df = build_summary(df)

    df.to_parquet(OUTPUT_DATA, index=False)
    summary_df.to_csv(OUTPUT_SUMMARY, index=False)

    report = build_report(df, summary_df, input_path)
    OUTPUT_REPORT.write_text(report)

    save_figures(df)

    print("\nPassenger impact simulation complete.")
    print(f"Input file: {input_path}")
    print(f"Rows analyzed: {len(df):,}")
    print(f"Estimated passengers affected: {df['estimated_passengers'].sum():,.0f}")
    print(f"Estimated missed connection risk: {df['estimated_missed_connection_risk'].sum():,.2f}")
    print(f"Passenger disruption cost proxy: {df['passenger_disruption_cost'].sum():,.2f}")
    print(f"Output data: {OUTPUT_DATA}")
    print(f"Summary CSV: {OUTPUT_SUMMARY}")
    print(f"Report: {OUTPUT_REPORT}")
    print(f"Figures:")
    print(f"- {FIG_ROUTE_COST}")
    print(f"- {FIG_AIRPORT_RISK}")
    print(f"- {FIG_STAGE_IMPACT}")


if __name__ == "__main__":
    main()
