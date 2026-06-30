from pathlib import Path
import json
import subprocess
import sys

import pandas as pd
import streamlit as st


DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = Path("reports")
FIGURES_DIR = Path("figures")

FLIGHTS_PATH = PROCESSED_DIR / "flights_clean.parquet"
AIRPORT_METRICS_PATH = PROCESSED_DIR / "airport_network_metrics.parquet"
ROUTE_METRICS_PATH = PROCESSED_DIR / "route_network_metrics.parquet"
SIM_RESULTS_PATH = PROCESSED_DIR / "disruption_simulation_results.parquet"
RECOVERY_PLAN_PATH = PROCESSED_DIR / "optimized_recovery_plan.parquet"


st.set_page_config(
    page_title="Airline Disruption Recovery Optimizer",
    page_icon="✈️",
    layout="wide",
)


@st.cache_data
def load_parquet(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_parquet(path)


@st.cache_data
def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


@st.cache_data
def load_markdown(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text()


def show_image(path: Path, caption: str | None = None) -> None:
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.warning(f"Missing figure: {path}")


def show_markdown_report(path: Path) -> None:
    report = load_markdown(path)
    if report:
        st.markdown(report)
    else:
        st.warning(f"Missing report: {path}")


def run_command(command: list[str]) -> tuple[bool, str]:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        output += "\nSTDERR:\n" + result.stderr

    return result.returncode == 0, output


def metric_card(label: str, value) -> None:
    st.metric(label, value)


def overview_page() -> None:
    st.title("✈️ Airline Disruption Recovery Optimizer")

    st.markdown(
        """
        This project combines **machine learning**, **network analysis**, 
        **simulation**, and **operations research optimization** to study airline 
        disruption recovery.

        The current version uses BTS airline on-time performance data for January 2025.
        """
    )

    flights = load_parquet(FLIGHTS_PATH)

    if flights is None:
        st.error("Processed flight data not found. Run `python src/data/clean_bts_on_time.py`.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("Flights", f"{len(flights):,}")

    with col2:
        airports = flights["origin"].nunique() if "origin" in flights.columns else "N/A"
        metric_card("Origin Airports", airports)

    with col3:
        delay_rate = flights["arrival_delay_15"].mean() * 100
        metric_card("Arrival Delay ≥15 Min", f"{delay_rate:.2f}%")

    with col4:
        cancel_rate = flights["cancelled"].mean() * 100
        metric_card("Cancellation Rate", f"{cancel_rate:.2f}%")

    st.divider()

    st.subheader("Project Pipeline")

    st.markdown(
        """
        1. **Data Pipeline** — clean BTS airline on-time performance data  
        2. **EDA** — understand delay patterns by carrier, airport, route, and day  
        3. **ML Model** — predict 15+ minute arrival delay risk  
        4. **Network Analysis** — identify critical airports and risky routes  
        5. **Simulation** — simulate airport disruption and downstream propagation  
        6. **Optimization** — prioritize recovery actions under limited capacity  
        """
    )

    st.divider()

    st.subheader("Key EDA Figures")

    col1, col2 = st.columns(2)

    with col1:
        show_image(
            FIGURES_DIR / "arrival_delay_distribution.png",
            "Arrival Delay Distribution",
        )

    with col2:
        show_image(
            FIGURES_DIR / "carrier_delay_rate.png",
            "Arrival Delay Rate by Carrier",
        )

    col3, col4 = st.columns(2)

    with col3:
        show_image(
            FIGURES_DIR / "top_origin_airports_by_delay_rate.png",
            "Top Origin Airports by Delay Rate",
        )

    with col4:
        show_image(
            FIGURES_DIR / "day_of_week_delay_rate.png",
            "Delay Rate by Day of Week",
        )


def eda_page() -> None:
    st.title("📊 Exploratory Airline Delay Analysis")

    show_markdown_report(REPORTS_DIR / "eda_summary.md")

    st.divider()

    st.subheader("EDA Charts")

    col1, col2 = st.columns(2)

    with col1:
        show_image(FIGURES_DIR / "arrival_delay_distribution.png")

    with col2:
        show_image(FIGURES_DIR / "carrier_delay_rate.png")

    col3, col4 = st.columns(2)

    with col3:
        show_image(FIGURES_DIR / "top_origin_airports_by_delay_rate.png")

    with col4:
        show_image(FIGURES_DIR / "day_of_week_delay_rate.png")


def delay_model_page() -> None:
    st.title("🤖 Delay Prediction Model")

    metrics = load_json(REPORTS_DIR / "delay_model_metrics.json")

    if metrics:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            metric_card("ROC AUC", metrics.get("roc_auc", "N/A"))

        with col2:
            metric_card("F1 Score", metrics.get("f1", "N/A"))

        with col3:
            metric_card("Recall", metrics.get("recall", "N/A"))

        with col4:
            metric_card("Test Delay Rate", f"{metrics.get('test_delay_rate_pct', 'N/A')}%")

        st.json(metrics, expanded=False)
    else:
        st.warning("Delay model metrics not found.")

    st.divider()

    show_markdown_report(REPORTS_DIR / "delay_model_report.md")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        show_image(FIGURES_DIR / "delay_model_confusion_matrix.png")

    with col2:
        show_image(FIGURES_DIR / "delay_model_roc_curve.png")


def network_page() -> None:
    st.title("🕸️ Airline Network Risk Analysis")

    airport_metrics = load_parquet(AIRPORT_METRICS_PATH)
    route_metrics = load_parquet(ROUTE_METRICS_PATH)

    if airport_metrics is not None:
        st.subheader("Top Airports by Disruption Risk")

        display_cols = [
            "airport",
            "departing_flights",
            "arrival_delay_15_rate",
            "cancellation_rate",
            "network_criticality_score",
            "airport_disruption_risk_score",
        ]

        available_cols = [col for col in display_cols if col in airport_metrics.columns]
        st.dataframe(
            airport_metrics[available_cols].head(20),
            use_container_width=True,
        )
    else:
        st.warning("Airport network metrics not found.")

    if route_metrics is not None:
        st.subheader("Top Routes by Delay Risk")

        display_cols = [
            "route",
            "flights",
            "arrival_delay_15_rate",
            "arrival_delay_60_rate",
            "cancellation_rate",
            "avg_arrival_delay",
            "route_delay_risk_score",
        ]

        available_cols = [col for col in display_cols if col in route_metrics.columns]
        st.dataframe(
            route_metrics[available_cols].head(20),
            use_container_width=True,
        )
    else:
        st.warning("Route network metrics not found.")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        show_image(FIGURES_DIR / "airport_disruption_risk_score.png")

    with col2:
        show_image(FIGURES_DIR / "route_delay_risk_score.png")

    show_image(FIGURES_DIR / "airline_route_network_top_routes.png")

    st.divider()

    show_markdown_report(REPORTS_DIR / "network_analysis_report.md")


def simulator_page() -> None:
    st.title("🌩️ Airport Disruption Simulator")

    st.markdown(
        """
        Simulate a disruption at a selected airport and estimate direct and downstream delay propagation.
        """
    )

    with st.sidebar:
        st.subheader("Simulation Settings")

        airport = st.selectbox(
            "Disrupted Airport",
            ["DEN", "ORD", "ATL", "DFW", "JFK", "LAX", "DCA", "SFO"],
            index=0,
        )

        date = st.text_input(
            "Date",
            value="",
            help="Leave blank to automatically use the busiest date for the selected airport.",
        )

        start_hour = st.slider("Start Hour", 0, 23, 8)
        end_hour = st.slider("End Hour", 1, 24, 14)
        primary_delay = st.slider("Primary Added Delay Minutes", 15, 240, 90, step=15)
        propagation_window = st.slider("Propagation Window Hours", 1, 12, 6)
        propagation_factor = st.slider("Propagation Factor", 1.0, 20.0, 8.0, step=0.5)
        max_propagated_delay = st.slider("Max Propagated Delay", 15, 180, 60, step=15)

        run_simulation = st.button("Run Disruption Simulation")

    if run_simulation:
        command = [
            sys.executable,
            "src/simulation/disruption_simulator.py",
            "--airport",
            airport,
            "--start-hour",
            str(start_hour),
            "--end-hour",
            str(end_hour),
            "--primary-delay",
            str(primary_delay),
            "--propagation-window",
            str(propagation_window),
            "--propagation-factor",
            str(propagation_factor),
            "--max-propagated-delay",
            str(max_propagated_delay),
        ]

        if date.strip():
            command.extend(["--date", date.strip()])

        with st.spinner("Running disruption simulation..."):
            success, output = run_command(command)

        st.cache_data.clear()

        if success:
            st.success("Simulation completed.")
        else:
            st.error("Simulation failed.")

        st.code(output)

    metrics = load_json(REPORTS_DIR / "disruption_simulation_metrics.json")
    sim_df = load_parquet(SIM_RESULTS_PATH)

    if metrics:
        st.subheader("Latest Simulation Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            metric_card("Airport", metrics.get("airport", "N/A"))

        with col2:
            metric_card("Impacted Flights", f"{metrics.get('total_impacted_flights', 0):,}")

        with col3:
            metric_card(
                "Delay Increase",
                f"{metrics.get('total_delay_increase_minutes', 0):,.0f} min",
            )

        with col4:
            metric_card(
                "Avg Delay Increase",
                f"{metrics.get('average_delay_increase_minutes', 0):,.2f} min",
            )

        st.json(metrics, expanded=False)
    else:
        st.warning("Simulation metrics not found. Run the simulator first.")

    if sim_df is not None:
        st.subheader("Latest Impacted Flights")
        st.dataframe(sim_df.head(100), use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        show_image(FIGURES_DIR / "disruption_impact_by_stage.png")

    with col2:
        show_image(FIGURES_DIR / "disruption_top_affected_airports.png")

    st.divider()

    show_markdown_report(REPORTS_DIR / "disruption_simulation_report.md")


def optimizer_page() -> None:
    st.title("🧮 Recovery Optimizer")

    st.markdown(
        """
        Prioritize disrupted flights for recovery under limited operational capacity.
        """
    )

    with st.sidebar:
        st.subheader("Optimization Settings")

        max_actions = st.slider("Max Recovery Actions", 10, 300, 120, step=10)
        primary_actions = st.slider("Max Primary Actions", 10, 250, 80, step=10)
        downstream_actions = st.slider("Max Downstream Actions", 10, 250, 100, step=10)
        recovery_effectiveness = st.slider("Recovery Effectiveness", 0.10, 1.00, 0.70, step=0.05)
        carrier_share_limit = st.slider("Carrier Share Limit", 0.10, 1.00, 0.35, step=0.05)
        airport_share_limit = st.slider("Airport Share Limit", 0.10, 1.00, 0.40, step=0.05)

        run_optimizer = st.button("Run Recovery Optimizer")

    if run_optimizer:
        command = [
            sys.executable,
            "src/optimization/recovery_optimizer.py",
            "--max-actions",
            str(max_actions),
            "--primary-actions",
            str(primary_actions),
            "--downstream-actions",
            str(downstream_actions),
            "--recovery-effectiveness",
            str(recovery_effectiveness),
            "--carrier-share-limit",
            str(carrier_share_limit),
            "--airport-share-limit",
            str(airport_share_limit),
        ]

        with st.spinner("Running recovery optimizer..."):
            success, output = run_command(command)

        st.cache_data.clear()

        if success:
            st.success("Optimization completed.")
        else:
            st.error("Optimization failed.")

        st.code(output)

    metrics = load_json(REPORTS_DIR / "recovery_optimization_metrics.json")
    plan = load_parquet(RECOVERY_PLAN_PATH)

    if metrics:
        st.subheader("Latest Optimization Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            metric_card("Status", metrics.get("optimization_status", "N/A"))

        with col2:
            metric_card("Actions Used", metrics.get("recovery_actions_used", "N/A"))

        with col3:
            metric_card(
                "Recovered Delay",
                f"{metrics.get('total_recovered_delay_minutes', 0):,.0f} min",
            )

        with col4:
            metric_card(
                "Delay Reduction",
                f"{metrics.get('delay_reduction_pct', 0):.2f}%",
            )

        st.json(metrics, expanded=False)
    else:
        st.warning("Optimization metrics not found. Run the optimizer first.")

    if plan is not None:
        selected = plan[plan["optimized_recovery_action"] == 1].copy()

        st.subheader("Selected Recovery Actions")
        st.dataframe(
            selected.sort_values("optimized_recovered_delay", ascending=False).head(100),
            use_container_width=True,
        )

        st.subheader("All Candidate Flights")
        st.dataframe(plan.head(100), use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        show_image(FIGURES_DIR / "optimized_vs_simulated_delay.png")

    with col2:
        show_image(FIGURES_DIR / "recovered_delay_by_stage.png")

    show_image(FIGURES_DIR / "top_optimized_recovery_routes.png")

    st.divider()

    show_markdown_report(REPORTS_DIR / "recovery_optimization_report.md")


def project_summary_page() -> None:
    st.title("🎓 PhD Research Positioning")

    st.markdown(
        """
        ## Research Theme

        **Learning-Augmented Optimization for Airline Disruption Recovery Under Network Uncertainty**

        This project demonstrates how predictive modeling, network science, simulation, and 
        mathematical optimization can be combined to support real-time airline recovery decisions.

        ## Why this matters for Operations Research

        Airline disruption recovery is a classic large-scale OR problem because it involves:

        - limited operational capacity
        - aircraft and route dependencies
        - cascading network delays
        - uncertain weather and airport conditions
        - tradeoffs between delay reduction, fairness, and feasibility

        ## Current contribution

        This version builds an end-to-end research prototype:

        1. Clean flight-level airline operations data  
        2. Identify delay and cancellation patterns  
        3. Predict arrival delay risk  
        4. Convert flights into an airport-route network  
        5. Simulate disruption propagation  
        6. Optimize recovery prioritization under constraints  

        ## Future research extensions

        - robust optimization under weather uncertainty
        - aircraft rotation recovery
        - passenger reaccommodation optimization
        - crew and gate constraint integration
        - stochastic programming for disruption scenarios
        - fairness-aware recovery policies
        """
    )


def main() -> None:
    st.sidebar.title("Airline Recovery System")

    page = st.sidebar.radio(
        "Navigate",
        [
            "Overview",
            "EDA",
            "Delay Model",
            "Network Analysis",
            "Disruption Simulator",
            "Recovery Optimizer",
            "PhD Research Summary",
        ],
    )

    if page == "Overview":
        overview_page()
    elif page == "EDA":
        eda_page()
    elif page == "Delay Model":
        delay_model_page()
    elif page == "Network Analysis":
        network_page()
    elif page == "Disruption Simulator":
        simulator_page()
    elif page == "Recovery Optimizer":
        optimizer_page()
    elif page == "PhD Research Summary":
        project_summary_page()


if __name__ == "__main__":
    main()
