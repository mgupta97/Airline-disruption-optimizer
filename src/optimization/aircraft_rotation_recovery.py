from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")
FIGURES_DIR = Path("figures")

OUTPUT_DATA = PROCESSED_DIR / "aircraft_rotation_recovery.parquet"
OUTPUT_SUMMARY = REPORTS_DIR / "aircraft_rotation_summary.csv"
OUTPUT_REPORT = REPORTS_DIR / "aircraft_rotation_recovery_report.md"

FIG_CHAIN = FIGURES_DIR / "aircraft_rotation_delay_chain.png"
FIG_TOP_AIRCRAFT = FIGURES_DIR / "top_aircraft_rotation_risk.png"
FIG_CARRIER = FIGURES_DIR / "rotation_downstream_delay_by_carrier.png"


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


def read_table(path):
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    return None


def find_schedule_file():
    candidates = list(PROCESSED_DIR.glob("*.parquet")) + list(PROCESSED_DIR.glob("*.csv"))

    best_path = None
    best_score = -1

    required_keywords = {
        "origin": ["origin", "origin_airport"],
        "dest": ["dest", "destination", "dest_airport"],
        "carrier": ["carrier", "airline", "op_unique_carrier"],
        "tail": ["tail_num", "tail_number", "aircraft_id", "tail"],
        "dep": ["crs_dep_time", "dep_time", "departure_time", "dep_hour"],
        "arr": ["crs_arr_time", "arr_time", "arrival_time", "arr_hour"],
    }

    for path in candidates:
        try:
            df = read_table(path)
            if df is None or len(df) == 0:
                continue

            score = 0
            for aliases in required_keywords.values():
                if find_column(df, aliases):
                    score += 1

            # Avoid choosing already-derived small outputs when possible
            if "rotation" in path.name.lower() or "passenger" in path.name.lower():
                score -= 2

            if score > best_score:
                best_score = score
                best_path = path

        except Exception:
            continue

    if best_path is None or best_score < 4:
        raise FileNotFoundError(
            "Could not identify a processed schedule file with enough flight columns. "
            "Run your cleaning script first, then inspect data/processed."
        )

    return best_path


def parse_hhmm_to_minutes(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()

    if text.endswith(".0"):
        text = text[:-2]

    text = re.sub(r"[^0-9]", "", text)

    if text == "":
        return np.nan

    try:
        number = int(text)
    except ValueError:
        return np.nan

    if number > 2400:
        return np.nan

    hour = number // 100
    minute = number % 100

    if hour == 24:
        hour = 0

    if hour > 23 or minute > 59:
        return np.nan

    return hour * 60 + minute


def standardize_schedule(df):
    df = df.copy()

    carrier_col = find_column(df, ["carrier", "airline", "op_unique_carrier"])
    tail_col = find_column(df, ["tail_num", "tail_number", "aircraft_id", "tail"])
    origin_col = find_column(df, ["origin", "origin_airport"])
    dest_col = find_column(df, ["dest", "destination", "dest_airport"])
    date_col = find_column(df, ["flight_date", "fl_date", "date"])
    dep_col = find_column(df, ["crs_dep_time", "scheduled_dep_time", "dep_time", "departure_time"])
    arr_col = find_column(df, ["crs_arr_time", "scheduled_arr_time", "arr_time", "arrival_time"])
    dep_hour_col = find_column(df, ["dep_hour", "departure_hour"])
    arr_delay_col = find_column(df, ["arr_delay", "arrival_delay", "arrival_delay_minutes"])
    dep_delay_col = find_column(df, ["dep_delay", "departure_delay", "departure_delay_minutes"])
    cancelled_col = find_column(df, ["cancelled", "canceled", "is_cancelled"])
    flight_num_col = find_column(df, ["flight_number", "flight_num", "op_carrier_fl_num"])

    required = {
        "carrier": carrier_col,
        "origin": origin_col,
        "dest": dest_col,
    }

    missing = [k for k, v in required.items() if v is None]

    if missing:
        raise ValueError(f"Missing required schedule columns: {missing}")

    df["carrier_std"] = df[carrier_col].astype(str)
    df["origin_std"] = df[origin_col].astype(str)
    df["dest_std"] = df[dest_col].astype(str)

    if tail_col:
        df["aircraft_id"] = df[tail_col].astype(str)
    elif flight_num_col:
        df["aircraft_id"] = df["carrier_std"] + "_FLIGHT_" + df[flight_num_col].astype(str)
    else:
        df["aircraft_id"] = df["carrier_std"] + "_PROXY_" + df["origin_std"] + "_" + df["dest_std"]

    if date_col:
        df["flight_date_std"] = pd.to_datetime(df[date_col], errors="coerce").dt.date.astype(str)
    else:
        df["flight_date_std"] = "Unknown"

    if dep_col:
        df["dep_minutes"] = df[dep_col].apply(parse_hhmm_to_minutes)
    elif dep_hour_col:
        df["dep_minutes"] = pd.to_numeric(df[dep_hour_col], errors="coerce") * 60
    else:
        df["dep_minutes"] = np.nan

    if arr_col:
        df["arr_minutes"] = df[arr_col].apply(parse_hhmm_to_minutes)
    else:
        df["arr_minutes"] = df["dep_minutes"] + 120

    # Handle overnight arrivals
    df["arr_minutes_adjusted"] = np.where(
        df["arr_minutes"] < df["dep_minutes"],
        df["arr_minutes"] + 24 * 60,
        df["arr_minutes"],
    )

    if arr_delay_col:
        df["observed_arrival_delay"] = pd.to_numeric(df[arr_delay_col], errors="coerce").fillna(0)
    elif dep_delay_col:
        df["observed_arrival_delay"] = pd.to_numeric(df[dep_delay_col], errors="coerce").fillna(0)
    else:
        df["observed_arrival_delay"] = 0

    df["observed_arrival_delay"] = df["observed_arrival_delay"].clip(lower=0)

    if cancelled_col:
        df["cancelled_std"] = pd.to_numeric(df[cancelled_col], errors="coerce").fillna(0)
    else:
        df["cancelled_std"] = 0

    df = df[
        df["aircraft_id"].notna()
        & df["origin_std"].notna()
        & df["dest_std"].notna()
        & df["dep_minutes"].notna()
        & df["arr_minutes_adjusted"].notna()
    ].copy()

    df = df.reset_index(drop=True)

    return df


def build_rotation_chains(df):
    df = df.copy()

    df = df.sort_values(
        ["aircraft_id", "flight_date_std", "dep_minutes"]
    ).reset_index(drop=True)

    grouped = df.groupby(["aircraft_id", "flight_date_std"], dropna=False)

    df["next_origin"] = grouped["origin_std"].shift(-1)
    df["next_dest"] = grouped["dest_std"].shift(-1)
    df["next_dep_minutes"] = grouped["dep_minutes"].shift(-1)
    df["next_flight_delay"] = grouped["observed_arrival_delay"].shift(-1)

    df["ground_time_minutes"] = df["next_dep_minutes"] - df["arr_minutes_adjusted"]

    df["valid_rotation_connection"] = (
        (df["dest_std"] == df["next_origin"])
        & (df["ground_time_minutes"] >= 0)
        & (df["ground_time_minutes"] <= 480)
    )

    # Standard airline turnaround buffer proxy
    df["minimum_turnaround_minutes"] = np.where(
        df["carrier_std"].isin(["WN", "F9", "NK", "G4"]),
        35,
        45,
    )

    df["turnaround_slack_minutes"] = (
        df["ground_time_minutes"] - df["minimum_turnaround_minutes"]
    )

    df["rotation_delay_pressure"] = (
        df["observed_arrival_delay"] - df["turnaround_slack_minutes"]
    ).clip(lower=0)

    df.loc[~df["valid_rotation_connection"], "rotation_delay_pressure"] = 0

    df["downstream_delay_risk_minutes"] = (
        df["rotation_delay_pressure"] * 0.70
    ).clip(lower=0)

    df["rotation_risk_score"] = (
        df["observed_arrival_delay"]
        + df["downstream_delay_risk_minutes"]
        + np.where(df["valid_rotation_connection"], 20, 0)
        + df["cancelled_std"] * 120
    )

    df["rotation"] = (
        df["aircraft_id"].astype(str)
        + " | "
        + df["origin_std"].astype(str)
        + "-"
        + df["dest_std"].astype(str)
        + " -> "
        + df["next_origin"].fillna("END").astype(str)
        + "-"
        + df["next_dest"].fillna("END").astype(str)
    )

    return df


def build_summary(df):
    aircraft_summary = (
        df.groupby(["aircraft_id", "carrier_std"])
        .agg(
            flights=("aircraft_id", "size"),
            valid_connections=("valid_rotation_connection", "sum"),
            total_observed_delay=("observed_arrival_delay", "sum"),
            total_downstream_delay_risk=("downstream_delay_risk_minutes", "sum"),
            avg_turnaround_slack=("turnaround_slack_minutes", "mean"),
            total_rotation_risk_score=("rotation_risk_score", "sum"),
        )
        .reset_index()
        .sort_values("total_rotation_risk_score", ascending=False)
    )

    aircraft_summary["avg_turnaround_slack"] = aircraft_summary["avg_turnaround_slack"].round(2)

    return aircraft_summary


def markdown_table(df):
    try:
        return df.to_markdown(index=False)
    except Exception:
        return "```\n" + df.to_string(index=False) + "\n```"


def build_report(rotation_df, aircraft_summary, schedule_path):
    top_aircraft = aircraft_summary.head(15)

    chain_cols = [
        "aircraft_id",
        "carrier_std",
        "origin_std",
        "dest_std",
        "next_origin",
        "next_dest",
        "observed_arrival_delay",
        "ground_time_minutes",
        "turnaround_slack_minutes",
        "downstream_delay_risk_minutes",
        "rotation_risk_score",
    ]

    top_chains = (
        rotation_df[
            rotation_df["valid_rotation_connection"]
            & (rotation_df["rotation_risk_score"] > 0)
        ]
        .sort_values("rotation_risk_score", ascending=False)
        .head(15)
        .loc[:, chain_cols]
    )

    carrier_summary = (
        rotation_df.groupby("carrier_std")
        .agg(
            flights=("carrier_std", "size"),
            valid_connections=("valid_rotation_connection", "sum"),
            observed_delay=("observed_arrival_delay", "sum"),
            downstream_delay_risk=("downstream_delay_risk_minutes", "sum"),
            rotation_risk=("rotation_risk_score", "sum"),
        )
        .reset_index()
        .sort_values("rotation_risk", ascending=False)
        .head(15)
    )

    report = "# Aircraft Rotation Recovery Report\n\n"

    report += "## Objective\n\n"
    report += (
        "This module estimates aircraft rotation delay propagation. In real airline "
        "operations, a delayed inbound aircraft can delay its next outbound flight if "
        "there is not enough turnaround slack. This analysis identifies aircraft chains, "
        "routes, and carriers with the highest downstream delay risk.\n\n"
    )

    report += "## Input\n\n"
    report += f"- Schedule file used: `{schedule_path}`\n\n"

    report += "## Methodology\n\n"
    report += (
        "Flights are grouped by aircraft identifier and flight date, sorted by scheduled "
        "departure time, and linked to the next flight in the same aircraft chain. "
        "The model estimates turnaround slack and calculates downstream delay pressure "
        "when the inbound delay exceeds the available slack.\n\n"
    )

    report += "## Top Aircraft by Rotation Risk\n\n"
    report += markdown_table(top_aircraft)
    report += "\n\n"

    report += "## Top Rotation Chains by Downstream Delay Risk\n\n"
    report += markdown_table(top_chains)
    report += "\n\n"

    report += "## Carrier Rotation Risk Summary\n\n"
    report += markdown_table(carrier_summary)
    report += "\n\n"

    report += "## Interpretation\n\n"
    report += (
        "Aircraft rotation risk helps move the recovery model closer to real-world airline "
        "operations. A flight with moderate delay can be more important than a longer delay "
        "if it sits early in an aircraft chain with limited turnaround slack and multiple "
        "downstream flights at risk.\n"
    )

    return report


def save_figures(rotation_df, aircraft_summary):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    top_aircraft = aircraft_summary.head(15)

    plt.figure(figsize=(12, 6))
    plt.bar(top_aircraft["aircraft_id"].astype(str), top_aircraft["total_rotation_risk_score"])
    plt.title("Top Aircraft by Rotation Risk Score")
    plt.ylabel("Rotation Risk Score")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_TOP_AIRCRAFT, dpi=200)
    plt.close()

    top_chains = (
        rotation_df[
            rotation_df["valid_rotation_connection"]
            & (rotation_df["rotation_risk_score"] > 0)
        ]
        .sort_values("rotation_risk_score", ascending=False)
        .head(15)
    )

    plt.figure(figsize=(12, 6))
    plt.bar(top_chains["rotation"].astype(str), top_chains["rotation_risk_score"])
    plt.title("Top Aircraft Rotation Delay Chains")
    plt.ylabel("Rotation Risk Score")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_CHAIN, dpi=200)
    plt.close()

    carrier_summary = (
        rotation_df.groupby("carrier_std")["downstream_delay_risk_minutes"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )

    plt.figure(figsize=(12, 6))
    plt.bar(carrier_summary.index.astype(str), carrier_summary.values)
    plt.title("Downstream Delay Risk by Carrier")
    plt.ylabel("Downstream Delay Risk Minutes")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_CARRIER, dpi=200)
    plt.close()


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    schedule_path = find_schedule_file()
    raw_df = read_table(schedule_path)

    schedule_df = standardize_schedule(raw_df)
    rotation_df = build_rotation_chains(schedule_df)
    aircraft_summary = build_summary(rotation_df)

    rotation_df.to_parquet(OUTPUT_DATA, index=False)
    aircraft_summary.to_csv(OUTPUT_SUMMARY, index=False)

    report = build_report(rotation_df, aircraft_summary, schedule_path)
    OUTPUT_REPORT.write_text(report)

    save_figures(rotation_df, aircraft_summary)

    print("\nAircraft rotation recovery analysis complete.")
    print(f"Schedule file: {schedule_path}")
    print(f"Flights analyzed: {len(rotation_df):,}")
    print(f"Aircraft chains: {rotation_df['aircraft_id'].nunique():,}")
    print(f"Valid rotation connections: {rotation_df['valid_rotation_connection'].sum():,}")
    print(f"Total downstream delay risk minutes: {rotation_df['downstream_delay_risk_minutes'].sum():,.2f}")
    print(f"Output data: {OUTPUT_DATA}")
    print(f"Summary CSV: {OUTPUT_SUMMARY}")
    print(f"Report: {OUTPUT_REPORT}")
    print("Figures:")
    print(f"- {FIG_CHAIN}")
    print(f"- {FIG_TOP_AIRCRAFT}")
    print(f"- {FIG_CARRIER}")


if __name__ == "__main__":
    main()
