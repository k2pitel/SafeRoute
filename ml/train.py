"""Train the segment safety-scoring model.

Usage:
    python train.py --data path/to/training_data.csv --out model.joblib

NOTE: stub pipeline using synthetic data so the script is runnable end to
end. Replace `load_training_data` with a real query/export of historical
segment features + a labeled/derived safety outcome.
"""
import argparse

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

FEATURE_COLUMNS = [
    "recent_incidents_7d",
    "recent_incidents_30d",
    "incident_severity_avg",
    "street_lighting",
    "pedestrian_density",
    "hour_of_day",
    "day_of_week",
    "community_reports_7d",
    "news_mentions_7d",
]


def load_training_data(path: str | None) -> pd.DataFrame:
    if path:
        return pd.read_csv(path)

    # Synthetic fallback so `python train.py` works with no arguments.
    rng = np.random.default_rng(42)
    n = 2000
    df = pd.DataFrame(
        {
            "recent_incidents_7d": rng.poisson(2, n),
            "recent_incidents_30d": rng.poisson(8, n),
            "incident_severity_avg": rng.uniform(0, 1, n),
            "street_lighting": rng.integers(0, 3, n),
            "pedestrian_density": rng.uniform(0, 1, n),
            "hour_of_day": rng.integers(0, 24, n),
            "day_of_week": rng.integers(0, 7, n),
            "community_reports_7d": rng.poisson(1, n),
            "news_mentions_7d": rng.poisson(0.5, n),
        }
    )
    # Synthetic label: safer with more lighting/density, riskier with more
    # incidents, worse at night — purely for a runnable demo, not real signal.
    night_penalty = ((df["hour_of_day"] < 6) | (df["hour_of_day"] > 21)).astype(int) * 1.5
    df["safety_score"] = (
        10
        - df["recent_incidents_7d"] * 0.4
        - df["incident_severity_avg"] * 2
        + df["street_lighting"] * 0.8
        + df["pedestrian_density"] * 1.2
        - night_penalty
        - df["community_reports_7d"] * 0.3
    ).clip(1, 10)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=None, help="CSV of features + safety_score label")
    parser.add_argument("--out", default="model.joblib")
    args = parser.parse_args()

    df = load_training_data(args.data)
    X, y = df[FEATURE_COLUMNS], df["safety_score"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingRegressor(random_state=42)
    model.fit(X_train, y_train)

    mae = mean_absolute_error(y_test, model.predict(X_test))
    print(f"Validation MAE: {mae:.3f}")

    joblib.dump(model, args.out)
    print(f"Model saved to {args.out}")


if __name__ == "__main__":
    main()
