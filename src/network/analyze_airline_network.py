from pathlib import Path
import math

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt


DATA_PATH = Path("data/processed/flights_clean.parquet")

PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")
FIGURES_DIR = Path("figures")

AIRPORT_METRICS_PATH = PROCESSED_DIR / "airport_network_metrics.parquet"
ROUTE_METRICS_PATH = PROCESSED_DIR / "route_network_metrics.parquet"

REPORT_PATH = REPORTS_DIR / "network_analysis_report.md"


def pct(series: pd.Series) -> float:
    return round(series.mean() * 100, 2)


def percentile_rank(series: pd.Series) -> pd.Series:
    return series.rank(pct=True).fillna(0)


def save_table_md(title: str, df: pd.DataFrame) -> str:
    return f"\n## {title}\n\n{df.to_markdown(index=False)}\n"


def build_route_metrics(df: pd.DataFrame) -> pd.DataFrame:
    route_metrics = (
        df.groupby(["origin", "dest"])
        .agg(
            flights=("origin", "size"),
            arrival_delay_15_rate=("arrival_delay_15", "mean"),
            arrival_delay_60_rate=("arrival_delay_60", "mean"),
            cancellation_rate=("cancelled", "mean"),
            avg_arrival_delay=("arr_delay", "mean"),
            avg_distance=("distance", "mean"),
        )
        .reset_index()
    )

    route_metrics["arrival_delay_15_rate"] = (
        route_metrics["arrival_delay_15_rate"] * 100
    ).round(2)

    route_metrics["arrival_delay_60_rate"] = (
        route_metrics["arrival_delay_60_rate"] * 100
    ).round(2)

    route_metrics["cancellation_rate"] = (
        route_metrics["cancellation_rate"] * 100
    ).round(2)

    route_metrics["avg_arrival_delay"] = route_metrics["avg_arrival_delay"].round(2)
    route_metrics["avg_distance"] = route_metrics["avg_distance"].round(2)

    route_metrics["route"] = route_metrics["origin"] + " -> " + route_metrics["dest"]

    # A simple disruption-risk score:
    # high delay rate matters, but high-volume routes matter more operationally.
    route_metrics["route_delay_risk_score"] = (
        route_metrics["arrival_delay_15_rate"] * route_metrics["flights"].apply(math.log1p)
    ).round(2)

    route_metrics = route_metrics.sort_values(
        "route_delay_risk_score", ascending=False
    )

    return route_metrics


def build_airport_origin_metrics(df: pd.DataFrame) -> pd.DataFrame:
    airport_metrics = (
        df.groupby("origin")
        .agg(
            departing_flights=("origin", "size"),
            arrival_delay_15_rate=("arrival_delay_15", "mean"),
            arrival_delay_60_rate=("arrival_delay_60", "mean"),
            cancellation_rate=("cancelled", "mean"),
            avg_arrival_delay=("arr_delay", "mean"),
        )
        .reset_index()
        .rename(columns={"origin": "airport"})
    )

    airport_metrics["arrival_delay_15_rate"] = (
        airport_metrics["arrival_delay_15_rate"] * 100
    ).round(2)

    airport_metrics["arrival_delay_60_rate"] = (
        airport_metrics["arrival_delay_60_rate"] * 100
    ).round(2)

    airport_metrics["cancellation_rate"] = (
        airport_metrics["cancellation_rate"] * 100
    ).round(2)

    airport_metrics["avg_arrival_delay"] = airport_metrics["avg_arrival_delay"].round(2)

    return airport_metrics


def build_graph(route_metrics: pd.DataFrame) -> nx.DiGraph:
    graph = nx.DiGraph()

    for row in route_metrics.itertuples(index=False):
        graph.add_edge(
            row.origin,
            row.dest,
            flights=row.flights,
            arrival_delay_15_rate=row.arrival_delay_15_rate,
            cancellation_rate=row.cancellation_rate,
            avg_arrival_delay=row.avg_arrival_delay,
            route_delay_risk_score=row.route_delay_risk_score,
        )

    return graph


def add_network_metrics(
    airport_metrics: pd.DataFrame,
    graph: nx.DiGraph,
) -> pd.DataFrame:
    weighted_out_degree = dict(graph.out_degree(weight="flights"))
    weighted_in_degree = dict(graph.in_degree(weight="flights"))
    unweighted_out_degree = dict(graph.out_degree())
    unweighted_in_degree = dict(graph.in_degree())

    degree_centrality = nx.degree_centrality(graph)
    betweenness_centrality = nx.betweenness_centrality(graph)

    try:
        pagerank = nx.pagerank(graph, weight="flights")
    except nx.PowerIterationFailedConvergence:
        pagerank = {node: 0 for node in graph.nodes}

    network_df = pd.DataFrame(
        {
            "airport": list(graph.nodes),
            "weighted_out_degree": [
                weighted_out_degree.get(node, 0) for node in graph.nodes
            ],
            "weighted_in_degree": [
                weighted_in_degree.get(node, 0) for node in graph.nodes
            ],
            "route_out_degree": [
                unweighted_out_degree.get(node, 0) for node in graph.nodes
            ],
            "route_in_degree": [
                unweighted_in_degree.get(node, 0) for node in graph.nodes
            ],
            "degree_centrality": [
                degree_centrality.get(node, 0) for node in graph.nodes
            ],
            "betweenness_centrality": [
                betweenness_centrality.get(node, 0) for node in graph.nodes
            ],
            "pagerank": [
                pagerank.get(node, 0) for node in graph.nodes
            ],
        }
    )

    airport_metrics = airport_metrics.merge(network_df, on="airport", how="left")

    airport_metrics["total_weighted_degree"] = (
        airport_metrics["weighted_out_degree"].fillna(0)
        + airport_metrics["weighted_in_degree"].fillna(0)
    )

    airport_metrics["total_route_degree"] = (
        airport_metrics["route_out_degree"].fillna(0)
        + airport_metrics["route_in_degree"].fillna(0)
    )

    airport_metrics["network_criticality_score"] = (
        0.40 * percentile_rank(airport_metrics["total_weighted_degree"])
        + 0.30 * percentile_rank(airport_metrics["pagerank"])
        + 0.30 * percentile_rank(airport_metrics["betweenness_centrality"])
    ).round(4)

    airport_metrics["airport_disruption_risk_score"] = (
        0.45 * percentile_rank(airport_metrics["arrival_delay_15_rate"])
        + 0.25 * percentile_rank(airport_metrics["cancellation_rate"])
        + 0.30 * percentile_rank(airport_metrics["network_criticality_score"])
    ).round(4)

    airport_metrics = airport_metrics.sort_values(
        "airport_disruption_risk_score", ascending=False
    )

    return airport_metrics


def save_top_airport_risk_plot(airport_metrics: pd.DataFrame) -> None:
    plot_df = airport_metrics.head(15).sort_values(
        "airport_disruption_risk_score", ascending=True
    )

    plt.figure(figsize=(10, 7))
    plt.barh(plot_df["airport"], plot_df["airport_disruption_risk_score"])
    plt.xlabel("Airport Disruption Risk Score")
    plt.ylabel("Airport")
    plt.title("Top Airports by Disruption Risk Score")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "airport_disruption_risk_score.png", dpi=200)
    plt.close()


def save_top_route_risk_plot(route_metrics: pd.DataFrame) -> None:
    plot_df = route_metrics.head(15).sort_values(
        "route_delay_risk_score", ascending=True
    )

    plt.figure(figsize=(11, 7))
    plt.barh(plot_df["route"], plot_df["route_delay_risk_score"])
    plt.xlabel("Route Delay Risk Score")
    plt.ylabel("Route")
    plt.title("Top Routes by Delay Risk Score")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "route_delay_risk_score.png", dpi=200)
    plt.close()


def save_network_graph(route_metrics: pd.DataFrame) -> None:
    # Use only the highest-volume routes so the graph remains readable.
    top_routes = route_metrics.sort_values("flights", ascending=False).head(80)

    graph = nx.from_pandas_edgelist(
        top_routes,
        source="origin",
        target="dest",
        edge_attr=["flights", "arrival_delay_15_rate", "route_delay_risk_score"],
        create_using=nx.DiGraph(),
    )

    node_flights = {}
    for row in top_routes.itertuples(index=False):
        node_flights[row.origin] = node_flights.get(row.origin, 0) + row.flights
        node_flights[row.dest] = node_flights.get(row.dest, 0) + row.flights

    node_sizes = [
        100 + 1200 * node_flights.get(node, 0) / max(node_flights.values())
        for node in graph.nodes
    ]

    plt.figure(figsize=(12, 9))
    pos = nx.spring_layout(graph, seed=42, k=0.45)

    nx.draw_networkx_nodes(graph, pos, node_size=node_sizes, alpha=0.85)
    nx.draw_networkx_edges(graph, pos, arrows=True, alpha=0.25, width=1)
    nx.draw_networkx_labels(graph, pos, font_size=8)

    plt.title("Airline Route Network: Top 80 Routes by Flight Volume")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "airline_route_network_top_routes.png", dpi=200)
    plt.close()


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Processed data not found. Run: python src/data/clean_bts_on_time.py"
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(DATA_PATH)

    required_cols = [
        "origin",
        "dest",
        "arrival_delay_15",
        "arrival_delay_60",
        "cancelled",
        "arr_delay",
        "distance",
    ]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. "
            "Rerun the cleaner and make sure origin/dest are included."
        )

    df = df.dropna(subset=["origin", "dest"]).copy()

    route_metrics = build_route_metrics(df)

    # For network centrality, use routes with enough volume to reduce noise.
    network_routes = route_metrics[route_metrics["flights"] >= 50].copy()

    graph = build_graph(network_routes)

    airport_metrics = build_airport_origin_metrics(df)
    airport_metrics = add_network_metrics(airport_metrics, graph)

    airport_metrics.to_parquet(AIRPORT_METRICS_PATH, index=False)
    route_metrics.to_parquet(ROUTE_METRICS_PATH, index=False)

    save_top_airport_risk_plot(airport_metrics)
    save_top_route_risk_plot(route_metrics)
    save_network_graph(route_metrics)

    summary_df = pd.DataFrame(
        [
            {"metric": "flights", "value": f"{len(df):,}"},
            {"metric": "airports", "value": f"{graph.number_of_nodes():,}"},
            {"metric": "routes_used_for_network", "value": f"{graph.number_of_edges():,}"},
            {
                "metric": "average_arrival_delay_15_rate_pct",
                "value": round(df["arrival_delay_15"].mean() * 100, 2),
            },
            {
                "metric": "average_cancellation_rate_pct",
                "value": round(df["cancelled"].mean() * 100, 2),
            },
        ]
    )

    top_airport_risk = airport_metrics[
        [
            "airport",
            "departing_flights",
            "arrival_delay_15_rate",
            "cancellation_rate",
            "network_criticality_score",
            "airport_disruption_risk_score",
        ]
    ].head(20)

    top_network_critical = airport_metrics.sort_values(
        "network_criticality_score", ascending=False
    )[
        [
            "airport",
            "departing_flights",
            "total_weighted_degree",
            "total_route_degree",
            "pagerank",
            "betweenness_centrality",
            "network_criticality_score",
        ]
    ].head(20)

    top_route_risk = route_metrics[
        [
            "route",
            "flights",
            "arrival_delay_15_rate",
            "arrival_delay_60_rate",
            "cancellation_rate",
            "avg_arrival_delay",
            "route_delay_risk_score",
        ]
    ].head(20)

    report = "# Airline Network Analysis Report\n"
    report += "\nThis report converts flight-level data into an airport-route network. "
    report += "Nodes represent airports, directed edges represent origin-destination routes, "
    report += "and risk scores combine delay performance with network importance.\n"

    report += save_table_md("Network Summary", summary_df)
    report += save_table_md("Top Airports by Disruption Risk", top_airport_risk)
    report += save_table_md("Top Airports by Network Criticality", top_network_critical)
    report += save_table_md("Top Routes by Delay Risk", top_route_risk)

    report += "\n## Interpretation\n\n"
    report += (
        "Airports with high disruption-risk scores are not simply delayed airports; "
        "they are airports where delay and cancellation performance interact with "
        "network centrality. These airports are important candidates for disruption "
        "simulation and recovery optimization in later stages of the project.\n\n"
    )
    report += (
        "Routes with high route-delay-risk scores combine high delay rates with "
        "meaningful flight volume. These routes are useful for identifying where "
        "localized disruptions may create larger downstream effects.\n"
    )

    REPORT_PATH.write_text(report)

    print("\nNetwork analysis complete.")
    print(f"Flights analyzed: {len(df):,}")
    print(f"Airports in network: {graph.number_of_nodes():,}")
    print(f"Routes in network: {graph.number_of_edges():,}")
    print(f"Saved airport metrics: {AIRPORT_METRICS_PATH}")
    print(f"Saved route metrics: {ROUTE_METRICS_PATH}")
    print(f"Saved report: {REPORT_PATH}")
    print(f"Saved figures in: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
