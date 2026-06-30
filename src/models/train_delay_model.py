from pathlib import Path
import json

import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DATA_PATH = Path("data/processed/flights_clean.parquet")
ARTIFACTS_DIR = Path("artifacts")
FIGURES_DIR = Path("figures")
REPORTS_DIR = Path("reports")

MODEL_PATH = ARTIFACTS_DIR / "delay_prediction_baseline.joblib"
METRICS_JSON_PATH = REPORTS_DIR / "delay_model_metrics.json"
METRICS_MD_PATH = REPORTS_DIR / "delay_model_report.md"


def hhmm_to_hour(value):
    if pd.isna(value):
        return None

    try:
        value = int(value)
    except ValueError:
        return None

    hour = value // 100

    if hour < 0 or hour > 24:
        return None

    if hour == 24:
        return 0

    return hour


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # We train only on operated, non-diverted flights for this first delay model.
    if "cancelled" in df.columns:
        df = df[df["cancelled"] == 0].copy()

    if "diverted" in df.columns:
        df = df[df["diverted"] == 0].copy()

    df["crs_dep_hour"] = df["crs_dep_time"].apply(hhmm_to_hour)
    df["crs_arr_hour"] = df["crs_arr_time"].apply(hhmm_to_hour)

    required_cols = [
        "flight_date",
        "carrier",
        "origin",
        "dest",
        "crs_dep_hour",
        "crs_arr_hour",
        "day_of_week",
        "month",
        "distance",
        "scheduled_elapsed_time",
        "arrival_delay_15",
    ]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df[required_cols].dropna().copy()
    df["arrival_delay_15"] = df["arrival_delay_15"].astype(int)

    return df


def time_based_split(df: pd.DataFrame):
    df = df.sort_values("flight_date").copy()

    split_date = df["flight_date"].quantile(0.8)

    train_df = df[df["flight_date"] <= split_date].copy()
    test_df = df[df["flight_date"] > split_date].copy()

    return train_df, test_df, split_date


def save_confusion_matrix(cm):
    labels = ["On time", "Delayed"]

    plt.figure(figsize=(6, 5))
    plt.imshow(cm)
    plt.title("Confusion Matrix - Baseline Delay Model")
    plt.xticks([0, 1], labels)
    plt.yticks([0, 1], labels)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")

    for i in range(2):
        for j in range(2):
            plt.text(j, i, str(cm[i, j]), ha="center", va="center")

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "delay_model_confusion_matrix.png", dpi=200)
    plt.close()


def save_roc_curve(y_test, y_proba, auc):
    fpr, tpr, _ = roc_curve(y_test, y_proba)

    plt.figure(figsize=(7, 5))
    plt.plot(fpr, tpr, label=f"AUC = {auc:.3f}")
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve - Baseline Delay Model")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "delay_model_roc_curve.png", dpi=200)
    plt.close()


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Processed data not found. Run: python src/data/clean_bts_on_time.py"
        )

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    raw_df = pd.read_parquet(DATA_PATH)
    df = prepare_data(raw_df)

    train_df, test_df, split_date = time_based_split(df)

    categorical_features = ["carrier", "origin", "dest"]
    numeric_features = [
        "crs_dep_hour",
        "crs_arr_hour",
        "day_of_week",
        "month",
        "distance",
        "scheduled_elapsed_time",
    ]

    X_train = train_df[categorical_features + numeric_features]
    y_train = train_df["arrival_delay_15"]

    X_test = test_df[categorical_features + numeric_features]
    y_test = test_df["arrival_delay_15"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ("num", StandardScaler(), numeric_features),
        ]
    )

    model = SGDClassifier(
        loss="log_loss",
        class_weight="balanced",
        max_iter=1000,
        random_state=42,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    print("Training baseline delay model...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_proba)
    avg_precision = average_precision_score(y_test, y_proba)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    metrics = {
        "model": "SGDClassifier logistic baseline",
        "target": "arrival_delay_15",
        "split_date": str(split_date),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "test_delay_rate_pct": round(float(y_test.mean() * 100), 2),
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "roc_auc": round(float(auc), 4),
        "average_precision": round(float(avg_precision), 4),
        "confusion_matrix": cm.tolist(),
        "features": categorical_features + numeric_features,
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    METRICS_JSON_PATH.write_text(json.dumps(metrics, indent=2))

    report = "# Baseline Flight Delay Prediction Model\n\n"
    report += "## Objective\n\n"
    report += (
        "Predict whether an operated, non-diverted flight will arrive "
        "15 or more minutes late using only pre-departure schedule information.\n\n"
    )

    report += "## Model Setup\n\n"
    report += f"- Model: {metrics['model']}\n"
    report += f"- Target: {metrics['target']}\n"
    report += f"- Time-based split date: {metrics['split_date']}\n"
    report += f"- Training rows: {metrics['train_rows']:,}\n"
    report += f"- Test rows: {metrics['test_rows']:,}\n"
    report += f"- Test delay rate: {metrics['test_delay_rate_pct']}%\n\n"

    report += "## Test Performance\n\n"
    report += f"- Accuracy: {metrics['accuracy']}\n"
    report += f"- Precision: {metrics['precision']}\n"
    report += f"- Recall: {metrics['recall']}\n"
    report += f"- F1 Score: {metrics['f1']}\n"
    report += f"- ROC AUC: {metrics['roc_auc']}\n"
    report += f"- Average Precision: {metrics['average_precision']}\n\n"

    report += "## Notes\n\n"
    report += (
        "This is a first baseline model. It intentionally avoids using actual "
        "departure delay, arrival delay, or delay-cause fields to prevent leakage. "
        "Later versions will add airport congestion, weather, inbound aircraft delay, "
        "and network propagation features.\n"
    )

    METRICS_MD_PATH.write_text(report)

    save_confusion_matrix(cm)
    save_roc_curve(y_test, y_proba, auc)

    print("\nModel training complete.")
    print(json.dumps(metrics, indent=2))
    print(f"\nSaved model: {MODEL_PATH}")
    print(f"Saved metrics: {METRICS_JSON_PATH}")
    print(f"Saved report: {METRICS_MD_PATH}")


if __name__ == "__main__":
    main()
