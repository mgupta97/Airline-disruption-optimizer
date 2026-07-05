from pathlib import Path
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Airline Recovery Optimizer V2",
    layout="wide",
)

REPORTS_DIR = Path("reports")
FIGURES_DIR = Path("figures")


def read_csv_if_exists(path):
    path = Path(path)
    if path.exists():
        return pd.read_csv(path)
    return None


def read_text_if_exists(path):
    path = Path(path)
    if path.exists():
        return path.read_text()
    return None


def show_image(path, caption=None):
    path = Path(path)
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.warning(f"Missing figure: {path}")


def show_report(path):
    text = read_text_if_exists(path)
    if text:
        st.markdown(text)
    else:
        st.warning(f"Missing report: {path}")


def metric_card(label, value):
    st.metric(label, value)


st.title("Airline Disruption Recovery Optimizer V2")
st.markdown(
    """
This dashboard presents a V2 airline disruption recovery system combining
simulation, optimization, passenger-impact modeling, aircraft rotation risk,
and robust weather scenario analysis.
"""
)

tabs = st.tabs(
    [
        "Overview",
        "Recovery Benchmark",
        "Passenger Impact",
        "Passenger-Aware Recovery",
        "Aircraft Rotations",
        "Robust Weather Recovery",
        "Reports",
    ]
)


with tabs[0]:
    st.header("V2 System Overview")

    summary_path = REPORTS_DIR / "v2_pipeline_run_summary.md"
    summary_text = read_text_if_exists(summary_path)

    if summary_text:
        st.markdown(summary_text)
    else:
        st.info("Run the V2 pipeline to generate the pipeline summary.")
        st.code("PYTHONPATH=. python src/run_v2_pipeline.py")

    st.subheader("V2 Modules")

    modules = pd.DataFrame(
        [
            {
                "Module": "Recovery Strategy Benchmark",
                "Purpose": "Compares optimized recovery against simple operational baselines.",
                "File": "src/analysis/recovery_strategy_comparison.py",
            },
            {
                "Module": "Passenger Impact Simulation",
                "Purpose": "Estimates passengers affected, missed-connection risk, and passenger disruption cost.",
                "File": "src/simulation/passenger_impact_simulator.py",
            },
            {
                "Module": "Passenger-Aware Recovery",
                "Purpose": "Compares strategies using both delay recovery and customer-impact metrics.",
                "File": "src/analysis/passenger_aware_recovery_comparison.py",
            },
            {
                "Module": "Aircraft Rotation Recovery",
                "Purpose": "Models downstream delay propagation across aircraft chains.",
                "File": "src/optimization/aircraft_rotation_recovery.py",
            },
            {
                "Module": "Robust Weather Recovery",
                "Purpose": "Tests recovery plans across multiple weather disruption scenarios.",
                "File": "src/optimization/robust_weather_recovery_optimizer.py",
            },
        ]
    )

    st.dataframe(modules, use_container_width=True, hide_index=True)


with tabs[1]:
    st.header("Recovery Strategy Benchmark")

    df = read_csv_if_exists(REPORTS_DIR / "recovery_strategy_comparison.csv")

    if df is not None:
        col1, col2, col3 = st.columns(3)

        best = df.sort_values("recovered_delay_minutes", ascending=False).iloc[0]

        with col1:
            metric_card("Best Strategy", best["strategy"])
        with col2:
            metric_card("Recovered Delay Minutes", f"{best['recovered_delay_minutes']:,.0f}")
        with col3:
            metric_card("Recovery Rate", f"{best['recovery_rate']:.2%}")

        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("Missing recovery strategy comparison CSV.")

    show_image(
        FIGURES_DIR / "recovery_strategy_comparison.png",
        "Recovered Delay Minutes by Recovery Strategy",
    )


with tabs[2]:
    st.header("Passenger Impact Simulation")

    df = read_csv_if_exists(REPORTS_DIR / "passenger_impact_summary.csv")

    if df is not None and len(df) > 0:
        row = df.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            metric_card("Disrupted Records", f"{row['disrupted_records']:,.0f}")
        with col2:
            metric_card("Passengers Affected", f"{row['estimated_passengers_affected']:,.0f}")
        with col3:
            metric_card("Missed Connection Risk", f"{row['estimated_missed_connection_risk']:,.0f}")
        with col4:
            metric_card("Passenger Cost Proxy", f"{row['total_passenger_disruption_cost']:,.0f}")

        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("Missing passenger impact summary CSV.")

    col1, col2 = st.columns(2)

    with col1:
        show_image(
            FIGURES_DIR / "passenger_disruption_cost_by_route.png",
            "Top Routes by Passenger Disruption Cost",
        )

    with col2:
        show_image(
            FIGURES_DIR / "top_connection_risk_airports.png",
            "Top Airports by Connection Risk",
        )

    show_image(
        FIGURES_DIR / "passenger_impact_by_stage.png",
        "Passenger Impact by Disruption Stage",
    )


with tabs[3]:
    st.header("Passenger-Aware Recovery Benchmark")

    df = read_csv_if_exists(REPORTS_DIR / "passenger_aware_recovery_comparison.csv")

    if df is not None:
        best_cost = df.sort_values(
            "passenger_disruption_cost_reduced",
            ascending=False,
        ).iloc[0]

        best_delay = df.sort_values(
            "delay_minutes_recovered",
            ascending=False,
        ).iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            metric_card("Best Cost Strategy", best_cost["strategy"])
        with col2:
            metric_card("Cost Reduced", f"{best_cost['passenger_disruption_cost_reduced']:,.0f}")
        with col3:
            metric_card("Best Delay Strategy", best_delay["strategy"])
        with col4:
            metric_card("Delay Recovered", f"{best_delay['delay_minutes_recovered']:,.0f}")

        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("Missing passenger-aware recovery comparison CSV.")

    col1, col2 = st.columns(2)

    with col1:
        show_image(
            FIGURES_DIR / "passenger_aware_recovery_comparison.png",
            "Passenger Cost Reduction by Strategy",
        )

    with col2:
        show_image(
            FIGURES_DIR / "passenger_aware_delay_recovery_comparison.png",
            "Delay Recovery by Strategy",
        )

    show_image(
        FIGURES_DIR / "passenger_aware_recovery_tradeoff.png",
        "Delay Recovery vs Passenger Cost Reduction",
    )


with tabs[4]:
    st.header("Aircraft Rotation Delay Propagation")

    df = read_csv_if_exists(REPORTS_DIR / "aircraft_rotation_summary.csv")

    if df is not None:
        st.dataframe(df.head(25), use_container_width=True, hide_index=True)
    else:
        st.info("Aircraft rotation summary CSV is ignored by Git, but will appear after running the V2 pipeline.")

    col1, col2 = st.columns(2)

    with col1:
        show_image(
            FIGURES_DIR / "top_aircraft_rotation_risk.png",
            "Top Aircraft by Rotation Risk",
        )

    with col2:
        show_image(
            FIGURES_DIR / "rotation_downstream_delay_by_carrier.png",
            "Downstream Delay Risk by Carrier",
        )

    show_image(
        FIGURES_DIR / "aircraft_rotation_delay_chain.png",
        "Top Aircraft Rotation Delay Chains",
    )


with tabs[5]:
    st.header("Robust Weather Recovery Optimizer")

    df = read_csv_if_exists(REPORTS_DIR / "robust_weather_recovery_summary.csv")

    if df is not None:
        best_expected = df.sort_values(
            "expected_passenger_cost_reduction",
            ascending=False,
        ).iloc[0]

        best_worst = df.sort_values(
            "worst_case_passenger_cost_reduction",
            ascending=False,
        ).iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            metric_card("Best Expected Strategy", best_expected["strategy"])
        with col2:
            metric_card("Expected Cost Reduction", f"{best_expected['expected_passenger_cost_reduction']:,.0f}")
        with col3:
            metric_card("Best Worst-Case Strategy", best_worst["strategy"])
        with col4:
            metric_card("Worst-Case Reduction", f"{best_worst['worst_case_passenger_cost_reduction']:,.0f}")

        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("Missing robust weather recovery summary CSV.")

    col1, col2 = st.columns(2)

    with col1:
        show_image(
            FIGURES_DIR / "robust_strategy_expected_passenger_cost.png",
            "Expected Passenger Cost Reduction",
        )

    with col2:
        show_image(
            FIGURES_DIR / "robust_strategy_worst_case_recovery.png",
            "Worst-Case Passenger Cost Reduction",
        )

    show_image(
        FIGURES_DIR / "robust_weather_scenario_heatmap.png",
        "Weather Scenario Recovery Matrix",
    )

    show_image(
        FIGURES_DIR / "robust_expected_vs_worst_case_tradeoff.png",
        "Expected vs Worst-Case Recovery Trade-off",
    )


with tabs[6]:
    st.header("Generated Reports")

    report_options = {
        "Recovery Strategy Comparison": REPORTS_DIR / "recovery_strategy_comparison_report.md",
        "Passenger Impact": REPORTS_DIR / "passenger_impact_report.md",
        "Passenger-Aware Recovery": REPORTS_DIR / "passenger_aware_recovery_comparison_report.md",
        "Aircraft Rotation Recovery": REPORTS_DIR / "aircraft_rotation_recovery_report.md",
        "Robust Weather Recovery": REPORTS_DIR / "robust_weather_recovery_report.md",
        "V2 Pipeline Summary": REPORTS_DIR / "v2_pipeline_run_summary.md",
    }

    selected = st.selectbox("Select report", list(report_options.keys()))
    show_report(report_options[selected])
