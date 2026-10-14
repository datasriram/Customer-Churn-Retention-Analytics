
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap
import xgboost as xgb
from scipy.special import expit

BASE = Path(__file__).resolve().parent
OUT = BASE / "outputs" / "v2"

# Load existing trained pipeline
pipeline = joblib.load(OUT / "churn_model.joblib")

metadata = json.loads(
    (OUT / "model_metadata.json").read_text(
        encoding="utf-8"
    )
)

df = pd.read_csv(OUT / "test_predictions.csv")

# Use a reproducible sample for explanation plots
sample = df.sample(
    n=min(300, len(df)),
    random_state=42
).copy()

X = sample[metadata["features"]]

preprocessor = pipeline.named_steps["preprocess"]
model = pipeline.named_steps["model"]

X_transformed = preprocessor.transform(X)

if hasattr(X_transformed, "toarray"):
    X_transformed = X_transformed.toarray()

feature_names = preprocessor.get_feature_names_out()

# XGBoost computes native TreeSHAP contributions.
# Last column is the expected/base contribution.
booster = model.get_booster()

dmatrix = xgb.DMatrix(
    X_transformed,
    feature_names=list(feature_names)
)

contributions = booster.predict(
    dmatrix,
    pred_contribs=True
)

shap_values = contributions[:, :-1]
base_values = contributions[:, -1]

# Validate SHAP additivity on the log-odds scale.
reconstructed = expit(
    base_values + shap_values.sum(axis=1)
)

original = pipeline.predict_proba(X)[:, 1]

max_error = np.max(
    np.abs(reconstructed - original)
)

print(
    "Maximum SHAP reconstruction error:",
    max_error
)

if max_error > 1e-4:
    raise ValueError(
        "SHAP contributions do not reproduce "
        "model predictions."
    )

explanation = shap.Explanation(
    values=shap_values,
    base_values=base_values,
    data=X_transformed,
    feature_names=list(feature_names)
)

# 1. Beeswarm plot
shap.plots.beeswarm(
    explanation,
    max_display=15,
    show=False
)

plt.tight_layout()
plt.savefig(
    OUT / "shap_beeswarm.png",
    dpi=170,
    bbox_inches="tight"
)
plt.close("all")

# 2. Global importance
shap.plots.bar(
    explanation,
    max_display=15,
    show=False
)

plt.tight_layout()
plt.savefig(
    OUT / "shap_importance.png",
    dpi=170,
    bbox_inches="tight"
)
plt.close("all")

# 3. Individual waterfall explanation
# Select the highest-risk customer in the sample.
risk_scores = pipeline.predict_proba(X)[:, 1]
highest_risk_index = int(np.argmax(risk_scores))

shap.plots.waterfall(
    explanation[highest_risk_index],
    max_display=15,
    show=False
)

plt.tight_layout()
plt.savefig(
    OUT / "shap_waterfall.png",
    dpi=170,
    bbox_inches="tight"
)
plt.close("all")

# 4. Dependence plots
for feature in [
    "num__age",
    "num__num_of_products"
]:
    if feature in feature_names:
        shap.plots.scatter(
            explanation[:, feature],
            show=False
        )

        plt.tight_layout()

        filename = (
            "shap_dependence_"
            + feature.replace("num__", "")
            + ".png"
        )

        plt.savefig(
            OUT / filename,
            dpi=170,
            bbox_inches="tight"
        )
        plt.close("all")

# 5. Export global importance
importance = pd.DataFrame({
    "feature": feature_names,
    "mean_absolute_shap": np.abs(
        shap_values
    ).mean(axis=0)
}).sort_values(
    "mean_absolute_shap",
    ascending=False
)

importance.to_csv(
    OUT / "shap_feature_importance.csv",
    index=False
)

print("\n=== TOP SHAP FEATURES ===")
print(
    importance.head(15).round(4).to_string(
        index=False
    )
)

print("\n=== HIGH-RISK CUSTOMER EXPLANATION ===")
print(
    "Customer ID:",
    sample.iloc[highest_risk_index]["customer_id"]
)
print(
    "Predicted churn probability:",
    round(float(risk_scores[highest_risk_index]), 4)
)

print("\nSHAP charts saved to outputs/v2/")
print("STEP 7 COMPLETE")
