"""Model inference + SHAP explainability, for use by the backend.

Backend usage (conceptually, in a Celery task or API call):

    from ml.serving import SafetyScorer
    scorer = SafetyScorer("model.joblib")
    score, shap_contribs = scorer.score(features_dict)
"""
import joblib
import numpy as np
import pandas as pd
import shap

from ml.features import SegmentFeatures
from ml.train import FEATURE_COLUMNS


class SafetyScorer:
    def __init__(self, model_path: str = "model.joblib"):
        self.model = joblib.load(model_path)
        self._explainer = None  # lazy-built; needs the model loaded first

    def _explainer_(self):
        if self._explainer is None:
            self._explainer = shap.TreeExplainer(self.model)
        return self._explainer

    def score(self, features: SegmentFeatures) -> tuple[float, list[dict]]:
        """Returns (safety_score, top_shap_contributions)."""
        row = pd.DataFrame([features.to_dict()])[FEATURE_COLUMNS]
        pred = float(np.clip(self.model.predict(row)[0], 1, 10))

        shap_values = self._explainer_().shap_values(row)[0]
        contributions = sorted(
            (
                {"feature": col, "impact": round(float(val), 3)}
                for col, val in zip(FEATURE_COLUMNS, shap_values)
            ),
            key=lambda c: abs(c["impact"]),
            reverse=True,
        )
        return pred, contributions[:5]
