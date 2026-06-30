from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


DATA_PATH = Path("data/processed/flights_clean.parquet")
FIGURES_DIR = Path("figures")
REPORTS_DIR = Path("reports")
REPORT_PATH = REPORTS_DIR / "eda_summary.md"


def pct(series: pd.Series) -> float:
    return round(series.mean() * 100, 2)


def save_table_md(title: str, df: pd.DataFrame) -> str:
    return f"\n## {title}\n\n{df.to_markdown(index=False)}\n"


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Processed data not found. Run: python src/data/clean_bts_on_time.py"
        )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(DATA_PATH)

    print(f"Loaded {len(df):,} rows and {len(df.columns)} columns")

    required = ["arrival_delay_15", "cancelled"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Basic summary
    summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "date_min": str(df["flight_date"].min()) if "flight_date" in df.columns else "N/A",
        "date_max": str(df["flight_date"].max()) if "flight_date" in df.columns else "N/A",
        "arrival_delay_15_rate_pct": pct(df["arrival_delay_15"]),
        "arrival_delay_60_rate_pct": pct(df["arrival_delay_60"]) if "arrival_delay_60" in df.columns else None,
        "cancellation_rate_pct": pct(df["cancelled"]),
        "diversion_rate_pct": pct(df["diverted"]) if "diverted" in df.columns else None,
    }

    summary_df = pd.DataFrame(
        [{"metric": key, "value": value} for key, value in summary.items()]
    )

    report = "# Airline Delay EDA Summary\n"
    report += save_table_md("Dataset Summary", summary_df)

    # Carrier performance
    if "carrier" in df.columns:
        carrier_summary = (
            df.groupby("carrier")
            .agg(
                flights=("carrier", "size"),
                arrival_delay_15_rate=("arrival_delay_15", "mean"),
                cancellation_rate=("cancelled", "mean"),
                avg_arrival_delay=("arr_delay", "mean"),
            )
            .reset_index()
        )

        carrier_summary["arrival_delay_15_rate"] = (
            carrier_summary["arrival_delay_15_rate"] * 100
        ).round(2)
        carrier_summary["cancellation_rate"] = (
            carrier_summary["cancellation_rate"] * 100
        ).round(2)
        carrier_summary["avg_arrival_delay"] = carrier_summary["avg_arrival_delay"].round(2)

        carrier_summary = carrier_summary.sort_values(
            "arrival_delay_15_rate", ascending=False
        )

        report += save_table_md("Carrier Delay Summary", carrier_summary)

        plt.figure(figsize=(10, 6))
        plot_df = carrier_summary.sort_values("arrival_delay_15_rate", ascending=True)
        plt.barh(plot_df["carrier"], plot_df["arrival_delay_15_rate"])
        plt.xlabel("Arrival Delay >= 15 Minutes Rate (%)")
        plt.ylabel("Carrier")
        plt.title("Arrival Delay Rate by Carrier")
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "carrier_delay_rate.png", dpi=200)
        plt.close()

    # Origin airport performance
    if "origin" in df.columns:
        airport_summary = (
            df.groupby("origin")
            .agg(
                flights=("origin", "size"),
                arrival_delay_15_rate=("arrival_delay_15", "mean"),
                cancellation_rate=("cancelled", "mean"),
                avg_arrival_delay=("arr_delay", "mean"),
            )
            .reset_index()
        )

        airport_summary = airport_summary[airport_summary["flights"] >= 1000].copy()
        airport_summary["arrival_delay_15_rate"] = (
            airport_summary["arrival_delay_15_rate"] * 100
        ).round(2)
        airport_summary["cancellation_rate"] = (
            airport_summary["cancellation_rate"] * 100
        ).round(2)
        airport_summary["avg_arrival_delay"] = airport_summary["avg_arrival_delay"].round(2)

        airport_summary = airport_summary.sort_values(
            "arrival_delay_15_rate", ascending=False
        )

        report += save_table_md(
            "Top Origin Airports by Arrival Delay Rate",
            airport_summary.head(20),
        )

        plt.figure(figsize=(10, 7))
        plot_df = airport_summary.head(15).sort_values(
            "arrival_delay_15_rate", ascending=True
        )
        plt.barh(plot_df["origin"], plot_df["arrival_delay_15_rate"])
        plt.xlabel("Arrival Delay >= 15 Minutes Rate (%)")
        plt.ylabel("Origin Airport")
        plt.title("Top Origin Airports by Arrival Delay Rate")
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "top_origin_airports_by_delay_rate.png", dpi=200)
        plt.close()

    # Route performance
    if {"origin", "dest"}.issubset(df.columns):
        route_summary = (
            df.groupby(["origin", "dest"])
            .agg(
                flights=("origin", "size"),
                arrival_delay_15_rate=("arrival_delay_15", "mean"),
                cancellation_rate=("cancelled", "mean"),
                avg_arrival_delay=("arr_delay", "mean"),
            )
            .reset_index()
        )

        route_summary = route_summary[route_summary["flights"] >= 100].copy()
        route_summary["arrival_delay_15_rate"] = (
            route_summary["arrival_delay_15_rate"] * 100
        ).round(2)
        route_summary["cancellation_rate"] = (
            route_summary["cancellation_rate"] * 100
        ).round(2)
        route_summary["avg_arrival_delay"] = route_summary["avg_arrival_delay"].round(2)

        route_summary = route_summary.sort_values(
            "arrival_delay_15_rate", ascending=False
        )

        report += save_table_md(
            "Top Routes by Arrival Delay Rate",
            route_summary.head(20),
        )

    # Day of week pattern
    if "day_of_week" in df.columns:
        dow_map = {
            0: "Mon",
            1: "Tue",
            2: "Wed",
            3: "Thu",
            4: "Fri",
            5: "Sat",
            6: "Sun",
        }

        dow_summary = (
            df.groupby("day_of_week")
            .agg(
                flights=("day_of_week", "size"),
                arrival_delay_15_rate=("arrival_delay_15", "mean"),
                cancellation_rate=("cancelled", "mean"),
            )
            .reset_index()
        )

        dow_summary["day"] = dow_summary["day_of_week"].map(dow_map)
        dow_summary["arrival_delay_15_rate"] = (
            dow_summary["arrival_delay_15_rate"] * 100
        ).round(2)
        dow_summary["cancellation_rate"] = (
            dow_summary["cancellation_rate"] * 100
        ).round(2)

        report += save_table_md(
            "Delay Pattern by Day of Week",
            dow_summary[["day", "flights", "arrival_delay_15_rate", "cancellation_rate"]],
        )

        plt.figure(figsize=(8, 5))
        plt.bar(dow_summary["day"], dow_summary["arrival_delay_15_rate"])
        plt.xlabel("Day of Week")
        plt.ylabel("Arrival Delay >= 15 Minutes Rate (%)")
        plt.title("Arrival Delay Rate by Day of Week")
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "day_of_week_delay_rate.png", dpi=200)
        plt.close()

    # Delay distribution
    if "arr_delay" in df.columns:
        delay_data = df["arr_delay"].dropna().clip(lower=-60, upper=180)

        plt.figure(figsize=(10, 6))
        plt.hist(delay_data, bins=60)
        plt.xlabel("Arrival Delay Minutes")
        plt.ylabel("Number of Flights")
        plt.title("Arrival Delay Distribution")
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "arrival_delay_distribution.png", dpi=200)
        plt.close()

    REPORT_PATH.write_text(report)

    print("\nEDA complete.")
    print(f"Saved report: {REPORT_PATH}")
    print(f"Saved figures in: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
