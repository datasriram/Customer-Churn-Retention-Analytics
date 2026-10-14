
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent
OUT = BASE / "outputs" / "v2"

st.set_page_config(
    page_title="Customer Churn Intelligence",
    page_icon="📊",
    layout="wide"
)

@st.cache_resource
def load_model():
    model = joblib.load(OUT / "churn_model.joblib")
    metadata = json.loads(
        (OUT / "model_metadata.json").read_text(
            encoding="utf-8"
        )
    )
    return model, metadata

model, metadata = load_model()
features = metadata["features"]
threshold = metadata["threshold"]

st.title("Customer Churn & Retention Intelligence")
st.caption(
    "XGBoost-based customer risk ranking and "
    "retention decision-support system"
)

with st.sidebar:
    st.header("Model Information")
    st.write("Algorithm:", metadata["model"])
    st.write("Classification threshold:", round(threshold, 3))
    st.write("Selection metric:", metadata["selection_metric"])
    st.info(
        "Trained on a static educational banking dataset. "
        "Predictions are illustrative and are not validated "
        "for use with real banking customers."
    )

tab1, tab2, tab3 = st.tabs([
    "Risk Prediction",
    "Model Evaluation",
    "About the Project"
])

with tab1:
    st.subheader("Upload Customer Data")
    st.write(
        "Upload customer records in CSV format. "
        "The app generates estimated churn risk scores "
        "and retention targeting priorities."
    )

    template = pd.read_csv(
        BASE / "data" / "processed" /
        "customer_churn_clean.csv",
        nrows=0
    )
    template = template.drop(
        columns=["exited"], errors="ignore"
    )

    st.download_button(
        "Download CSV Template",
        data=template.to_csv(index=False),
        file_name="customer_template.csv",
        mime="text/csv"
    )

    uploaded = st.file_uploader(
        "Choose customer CSV",
        type=["csv"]
    )

    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)

            if df.empty:
                st.error("The uploaded file has no customers.")
                st.stop()

            missing = [
                c for c in features if c not in df.columns
            ]

            if missing:
                st.error(f"Missing required columns: {missing}")
                st.stop()

            if df[features].isna().all(axis=1).any():
                st.error(
                    "At least one customer has all predictor "
                    "values missing."
                )
                st.stop()

            numeric_cols = [
                "credit_score", "age", "tenure", "balance",
                "num_of_products", "has_cr_card",
                "is_active_member", "estimated_salary",
                "satisfaction_score", "points_earned"
            ]

            for col in numeric_cols:
                if col in features:
                    values = pd.to_numeric(
                        df[col], errors="coerce"
                    )
                    invalid = (
                        df[col].notna() & values.isna()
                    )
                    if invalid.any():
                        raise ValueError(
                            f"Invalid numeric values in {col}"
                        )
                    df[col] = values

            if df[features].isna().any().any():
                st.warning(
                    "Some values are missing. The trained "
                    "pipeline will impute them."
                )

            scores = model.predict_proba(
                df[features]
            )[:, 1]

            results = df.copy()
            results = results.drop(
                columns=["exited", "actual_exited",
                         "Complain"],
                errors="ignore"
            )

            results["churn_probability"] = scores
            results["predicted_churn"] = (
                scores >= threshold
            ).astype(int)

            results["risk_segment"] = pd.cut(
                scores,
                bins=[-0.001, 0.30, 0.60, 1.001],
                labels=["Low", "Medium", "High"]
            ).astype(str)

            results = results.sort_values(
                "churn_probability",
                ascending=False
            ).reset_index(drop=True)

            st.divider()
            st.subheader("Prediction Overview")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Customers", len(results))
            c2.metric(
                "Predicted churners",
                int(results["predicted_churn"].sum())
            )
            c3.metric(
                "Average risk",
                f"{scores.mean():.1%}"
            )
            c4.metric(
                "High-risk customers",
                int((scores >= 0.60).sum())
            )

            st.subheader("Customer Risk Distribution")
            st.bar_chart(
                results["risk_segment"]
                .value_counts()
                .reindex(
                    ["Low", "Medium", "High"],
                    fill_value=0
                )
            )

            st.subheader("Retention Targeting")

            capacity = st.slider(
                "Percentage of customers to contact",
                min_value=5,
                max_value=100,
                value=10,
                step=5
            )

            k = max(
                1, int(np.ceil(len(results) * capacity / 100))
            )

            results["outreach_priority"] = (
                ["Contact"] * k
                + ["Not selected"] * (len(results) - k)
            )

            st.write(
                f"**{k} highest-risk customers selected** "
                "for the proposed outreach campaign."
            )

            st.subheader("Illustrative Campaign Economics")
            st.caption(
                "Assumptions only — not actual campaign "
                "performance or measured treatment effects."
            )

            e1, e2, e3 = st.columns(3)
            with e1:
                contact_cost = st.number_input(
                    "Cost per contact",
                    min_value=0.0,
                    value=100.0
                )
            with e2:
                retained_value = st.number_input(
                    "Value per customer retained",
                    min_value=0.0,
                    value=5000.0
                )
            with e3:
                effectiveness = st.slider(
                    "Assumed campaign effectiveness (%)",
                    0, 100, 10
                ) / 100

            expected_at_risk = results.head(k)[
                "churn_probability"
            ].sum()

            expected_saved = (
                expected_at_risk * effectiveness
            )

            expected_net = (
                expected_saved * retained_value
                - k * contact_cost
            )

            e4, e5, e6 = st.columns(3)
            e4.metric(
                "Estimated would-be churners",
                f"{expected_at_risk:.1f}"
            )
            e5.metric(
                "Hypothetical customers retained",
                f"{expected_saved:.1f}"
            )
            e6.metric(
                "Hypothetical net value",
                f"{expected_net:,.0f}"
            )

            st.caption(
                "This calculation assumes risk probabilities "
                "are calibrated for the uploaded population "
                "and campaign effectiveness is a causal "
                "reduction in churn. Neither assumption has "
                "been validated for uploaded customers."
            )

            st.subheader("Prioritized Customers")
            st.dataframe(results, use_container_width=True)

            st.download_button(
                "Download Predictions and Priorities",
                data=results.to_csv(index=False),
                file_name="churn_predictions.csv",
                mime="text/csv"
            )

        except Exception as exc:
            st.error(f"Unable to process CSV: {exc}")

with tab2:
    st.subheader("Held-out Test Performance")

    metrics = metadata["test_metrics"]
    cols = st.columns(4)

    cols[0].metric(
        "ROC-AUC", f"{metrics['roc_auc']:.4f}"
    )
    cols[1].metric(
        "Average Precision",
        f"{metrics['average_precision']:.4f}"
    )
    cols[2].metric(
        "Recall", f"{metrics['recall']:.2%}"
    )
    cols[3].metric(
        "Precision@10%",
        f"{metrics['precision_at_10pct']:.2%}"
    )

    st.caption(
        "Held-out evaluation on the existing static dataset. "
        "The test data was used for diagnostics and is not "
        "an independent future-period validation."
    )

    st.subheader("Model Comparison")
    comparison = pd.read_csv(
        OUT / "model_comparison.csv"
    )
    st.dataframe(comparison, use_container_width=True)

    st.subheader("Calibration")
    st.image(str(OUT / "calibration.png"))

    st.subheader("Top-K Retention Targeting")
    st.image(str(OUT / "topk_performance.png"))

    st.subheader("Feature Importance")
    st.image(str(OUT / "permutation_importance.png"))

    st.subheader("Segment Performance")
    segments = pd.read_csv(
        OUT / "segment_performance.csv"
    )
    st.dataframe(segments, use_container_width=True)

    st.subheader("SHAP Explainability")
    st.caption(
        "SHAP explains how features influence the XGBoost model's churn predictions. "
        "Positive SHAP contributions push predictions toward churn; negative contributions push toward retention."
    )

    st.markdown("**SHAP Summary Plot**")
    st.image(str(OUT / "shap_summary.png"))

    st.markdown("**SHAP Waterfall Plot (Highest-Risk Customer)**")
    st.image(str(OUT / "shap_waterfall_highrisk.png"))

    st.markdown("**SHAP Dependence Plot**")
    st.image(str(OUT / "shap_dependence_age.png"))

with tab3:
    st.header("About This Project")

    st.markdown("""
    ### Objective
    Predict customer churn risk and prioritize
    customers for potential retention outreach.

    ### Model selection
    Logistic Regression, class-weighted Logistic
    Regression, Random Forest, and XGBoost were
    compared using five-fold stratified cross-validation.

    Average precision was the primary model-selection
    metric, with ROC-AUC, Brier score, and top-K
    targeting performance as supporting measures.

    ### Methodology
    - Pipeline-based preprocessing
    - Training-only model selection
    - Separate held-out test evaluation
    - Threshold optimization using training predictions
    - Calibration diagnostics
    - Permutation feature importance
    - Subgroup and error analysis
    - Illustrative retention campaign economics

    ### Limitations
    This project uses static educational data, not a
    temporally validated production banking dataset.

    The model estimates churn risk, not the causal effect
    of retention interventions. Business value
    calculations depend on hypothetical assumptions.

    Uploaded data may differ from the training
    distribution and should not be treated as
    production-validated.
    """)

    st.markdown(
        "[View GitHub Repository]"
        "(https://github.com/datasriram/"
        "Customer-Churn-Retention-Analytics)"
    )
