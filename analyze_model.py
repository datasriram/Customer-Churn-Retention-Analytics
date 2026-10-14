
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_score,
    recall_score
)

BASE = Path(__file__).resolve().parent
OUT = BASE / "outputs" / "v2"
OUT.mkdir(parents=True, exist_ok=True)

model = joblib.load(OUT / "churn_model.joblib")
meta = json.loads(
    (OUT / "model_metadata.json").read_text()
)
df = pd.read_csv(OUT / "test_predictions.csv")

features = meta["features"]
X = df[features]
y = df["actual_exited"].astype(int).to_numpy()
scores = df["churn_probability"].to_numpy()
pred = df["predicted_churn"].to_numpy()

# 1. Calibration: evaluate only, do not refit on test.
observed, predicted = calibration_curve(
    y, scores, n_bins=10, strategy="quantile"
)

plt.figure(figsize=(7, 5))
plt.plot([0, 1], [0, 1], "--", label="Perfect calibration")
plt.plot(
    predicted, observed, marker="o",
    label="XGBoost"
)
plt.xlabel("Mean predicted churn probability")
plt.ylabel("Observed churn rate")
plt.title("Probability Calibration")
plt.legend()
plt.tight_layout()
plt.savefig(OUT / "calibration.png", dpi=160)
plt.close()

cal = pd.DataFrame({
    "mean_prediction": predicted,
    "observed_churn_rate": observed
})
cal.to_csv(OUT / "calibration.csv", index=False)

# 2. Precision@K and Recall@K.
ranked = df.sort_values(
    "churn_probability", ascending=False
).reset_index(drop=True)

total_churners = int(ranked["actual_exited"].sum())
k_rows = []

for pct in [5, 10, 15, 20, 25, 30, 40, 50]:
    k = int(np.ceil(len(ranked) * pct / 100))
    actual_churners = int(
        ranked.head(k)["actual_exited"].sum()
    )
    k_rows.append({
        "top_percent": pct,
        "customers_contacted": k,
        "actual_churners_found": actual_churners,
        "precision_at_k": actual_churners / k,
        "recall_at_k": actual_churners / total_churners
    })

topk = pd.DataFrame(k_rows)
topk.to_csv(OUT / "topk_analysis.csv", index=False)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(
    topk["top_percent"], topk["precision_at_k"],
    marker="o", label="Precision@K"
)
ax.plot(
    topk["top_percent"], topk["recall_at_k"],
    marker="s", label="Recall@K"
)
ax.axhline(
    y.mean(), linestyle="--",
    label="Random targeting precision"
)
ax.set_xlabel("Top % of customers contacted")
ax.set_ylabel("Score")
ax.set_title("Retention Targeting Performance")
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "topk_performance.png", dpi=160)
plt.close(fig)

# 3. Permutation feature importance.
print("\nCalculating permutation importance...")

importance = permutation_importance(
    model, X, y,
    scoring="average_precision",
    n_repeats=3,
    random_state=42,
    n_jobs=1
)

imp = pd.DataFrame({
    "feature": features,
    "importance_mean": importance.importances_mean,
    "importance_std": importance.importances_std
}).sort_values("importance_mean", ascending=False)

imp.to_csv(
    OUT / "permutation_importance.csv", index=False
)

plt.figure(figsize=(9, 6))
plot_data = imp.head(12).iloc[::-1]
plt.barh(
    plot_data["feature"],
    plot_data["importance_mean"]
)
plt.xlabel("Drop in Average Precision When Shuffled")
plt.title("Permutation Feature Importance")
plt.tight_layout()
plt.savefig(
    OUT / "permutation_importance.png", dpi=160
)
plt.close()

# 4. Error analysis.
df["error_type"] = np.select(
    [
        (y == 1) & (pred == 1),
        (y == 0) & (pred == 1),
        (y == 1) & (pred == 0)
    ],
    ["TP", "FP", "FN"],
    default="TN"
)

errors = df[df["error_type"].isin(["FP", "FN"])]
errors.to_csv(OUT / "error_analysis.csv", index=False)

segment_rows = []
for feature in ["geography", "gender", "is_active_member",
                "num_of_products"]:
    for group, part in df.groupby(feature, dropna=False):
        truth = part["actual_exited"]
        prediction = part["predicted_churn"]

        segment_rows.append({
            "feature": feature,
            "group": str(group),
            "customers": len(part),
            "actual_churn_rate": truth.mean(),
            "precision": precision_score(
                truth, prediction, zero_division=0
            ),
            "recall": recall_score(
                truth, prediction, zero_division=0
            ),
            "false_negatives": int(
                ((truth == 1) & (prediction == 0)).sum()
            )
        })

segments = pd.DataFrame(segment_rows)
segments.to_csv(
    OUT / "segment_performance.csv", index=False
)

# 5. Illustrative campaign economics.
# Assumptions, NOT real observed treatment effects.
contact_cost = 100
retained_customer_value = 5000
assumed_treatment_effect = 0.10

business = topk.copy()
business["assumed_customers_saved"] = (
    business["actual_churners_found"]
    * assumed_treatment_effect
)
business["contact_cost"] = (
    business["customers_contacted"] * contact_cost
)
business["hypothetical_net_value"] = (
    business["assumed_customers_saved"]
    * retained_customer_value
    - business["contact_cost"]
)
business.to_csv(
    OUT / "retention_economics.csv", index=False
)

print("\n=== TOP-K RESULTS ===")
print(topk.round(4).to_string(index=False))

print("\n=== TOP 10 FEATURES ===")
print(imp.head(10).round(4).to_string(index=False))

print("\n=== CALIBRATION TABLE ===")
print(cal.round(4).to_string(index=False))

print("\n=== ERROR COUNTS ===")
print(df["error_type"].value_counts().to_string())

print("\n=== SEGMENT PERFORMANCE ===")
print(segments.round(3).to_string(index=False))

print("\n=== HYPOTHETICAL CAMPAIGN ECONOMICS ===")
print(
    business[[
        "top_percent",
        "customers_contacted",
        "hypothetical_net_value"
    ]].round(2).to_string(index=False)
)

print("\nSTEP 3 COMPLETE — outputs/v2/")
