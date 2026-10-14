
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import (
    train_test_split, StratifiedKFold, cross_val_predict
)
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score, roc_auc_score,
    precision_score, recall_score, f1_score,
    accuracy_score, brier_score_loss,
    confusion_matrix
)
from xgboost import XGBClassifier

SEED = 42
BASE = Path(__file__).resolve().parent
OUT = BASE / "outputs" / "v2"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(
    BASE / "data" / "processed" / "customer_churn_clean.csv"
)

target = "exited"
drop_cols = ["customer_id", target]

X = df.drop(columns=drop_cols)
y = df[target].astype(int)

assert y.notna().all()
assert set(y.unique()) == {0, 1}

numeric = X.select_dtypes(include=np.number).columns.tolist()
categorical = X.select_dtypes(exclude=np.number).columns.tolist()

preprocessor = ColumnTransformer([
    ("num", Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler())
    ]), numeric),
    ("cat", Pipeline([
        ("impute", SimpleImputer(
            strategy="most_frequent"
        )),
        ("encode", OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False
        ))
    ]), categorical)
])

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.20,
    stratify=y,
    random_state=SEED
)

models = {
    "Logistic Regression": LogisticRegression(
        max_iter=2000, random_state=SEED
    ),
    "Balanced Logistic Regression": LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=SEED
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        min_samples_leaf=2,
        class_weight="balanced",
        n_jobs=-1,
        random_state=SEED
    ),
    "XGBoost": XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        n_jobs=4,
        random_state=SEED
    )
}

cv = StratifiedKFold(
    n_splits=5, shuffle=True, random_state=SEED
)

def top_k_metrics(y_true, scores, fraction=0.10):
    actual = np.asarray(y_true)
    k = max(1, int(np.ceil(len(actual) * fraction)))
    order = np.argsort(-np.asarray(scores), kind="stable")
    hits = actual[order[:k]].sum()

    return {
        "precision_at_10pct": hits / k,
        "recall_at_10pct": hits / actual.sum()
    }

rows = []
oof_predictions = {}

print(f"Dataset: {X.shape}")
print(f"Training rows: {len(X_train)}")
print(f"Test rows: {len(X_test)}")
print(f"Churn prevalence: {y.mean():.4f}")
print(f"Predictors: {X.columns.tolist()}")

for name, model in models.items():
    print(f"\nTraining {name}...", flush=True)

    pipeline = Pipeline([
        ("preprocess", preprocessor),
        ("model", model)
    ])

    oof = cross_val_predict(
        pipeline,
        X_train,
        y_train,
        cv=cv,
        method="predict_proba",
        n_jobs=1
    )[:, 1]

    oof_predictions[name] = oof

    metrics = {
        "model": name,
        "average_precision": average_precision_score(
            y_train, oof
        ),
        "roc_auc": roc_auc_score(y_train, oof),
        "brier_score": brier_score_loss(y_train, oof),
        **top_k_metrics(y_train, oof)
    }
    rows.append(metrics)

results = (
    pd.DataFrame(rows)
    .sort_values("average_precision", ascending=False)
)

print("\n=== OUT-OF-FOLD MODEL COMPARISON ===")
print(results.round(4).to_string(index=False))

results.to_csv(
    OUT / "model_comparison.csv", index=False
)

winner = results.iloc[0]["model"]
print(f"\nSelected by CV average precision: {winner}")

final_pipeline = Pipeline([
    ("preprocess", preprocessor),
    ("model", models[winner])
])
final_pipeline.fit(X_train, y_train)

test_scores = final_pipeline.predict_proba(X_test)[:, 1]

# Select an operating threshold using TRAINING OOF scores,
# never test labels or test scores.
train_scores = oof_predictions[winner]
thresholds = np.linspace(0.05, 0.95, 91)

threshold_results = pd.DataFrame([
    {
        "threshold": float(t),
        "precision": precision_score(
            y_train, train_scores >= t, zero_division=0
        ),
        "recall": recall_score(
            y_train, train_scores >= t, zero_division=0
        ),
        "f1": f1_score(
            y_train, train_scores >= t, zero_division=0
        )
    }
    for t in thresholds
])

best_threshold = float(
    threshold_results.sort_values(
        ["f1", "threshold"], ascending=[False, True]
    ).iloc[0]["threshold"]
)

threshold_results.to_csv(
    OUT / "threshold_analysis.csv", index=False
)

test_pred = (test_scores >= best_threshold).astype(int)

test_metrics = {
    "model": winner,
    "threshold": best_threshold,
    "average_precision": average_precision_score(
        y_test, test_scores
    ),
    "roc_auc": roc_auc_score(y_test, test_scores),
    "brier_score": brier_score_loss(y_test, test_scores),
    "accuracy": accuracy_score(y_test, test_pred),
    "precision": precision_score(
        y_test, test_pred, zero_division=0
    ),
    "recall": recall_score(
        y_test, test_pred, zero_division=0
    ),
    "f1": f1_score(y_test, test_pred),
    **top_k_metrics(y_test, test_scores)
}

print("\n=== FINAL HELD-OUT TEST EVALUATION ===")
for key, value in test_metrics.items():
    print(f"{key}: {value}")

print("\nConfusion matrix [TN FP; FN TP]:")
print(confusion_matrix(y_test, test_pred))

pd.DataFrame([test_metrics]).to_csv(
    OUT / "test_metrics.csv", index=False
)

predictions = X_test.copy()
predictions.insert(0, "customer_id", df.loc[X_test.index, "customer_id"])
predictions["actual_exited"] = y_test.to_numpy()
predictions["churn_probability"] = test_scores
predictions["predicted_churn"] = test_pred
predictions.to_csv(
    OUT / "test_predictions.csv", index=False
)

joblib.dump(final_pipeline, OUT / "churn_model.joblib")

metadata = {
    "model": winner,
    "threshold": best_threshold,
    "features": X.columns.tolist(),
    "training_rows": len(X_train),
    "test_rows": len(X_test),
    "selection_metric": "OOF average precision",
    "dataset": "customer_churn_clean.csv",
    "random_state": SEED,
    "test_metrics": test_metrics
}

(OUT / "model_metadata.json").write_text(
    json.dumps(metadata, indent=2),
    encoding="utf-8"
)

print("\nArtifacts saved to outputs/v2/")
print("STEP 2 COMPLETE")
