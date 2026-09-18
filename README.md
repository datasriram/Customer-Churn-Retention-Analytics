# Customer Churn & Retention Analytics

A banking customer analytics project combining SQL, Python, machine learning, customer risk segmentation, retention prioritization, and Tableau reporting.

## Live Dashboards

- [Customer Churn Overview](https://public.tableau.com/app/profile/tummala.sriram/viz/Book1_17896808760300/CustomerChurnOverview)
- [Churn Risk & Retention Prioritization](https://public.tableau.com/app/profile/tummala.sriram/viz/Book2_17896999140930/ChurnRiskRetentionPrioritization)

## Business Problem

The objective of this project is to understand customer churn patterns, identify customers with elevated churn risk, and prioritize retention outreach using interpretable customer segments.

## Dataset

The dataset contains 10,000 banking customers. The target variable is `Exited`, and the overall churn rate is 20.38%.

Customer identifiers such as `CustomerId` were excluded from model training. `Complain` was also excluded because it showed an unusually strong relationship with the target and was treated as a potential leakage-risk variable.

## Project Workflow

Raw Data -> SQL Analysis -> Python EDA -> Feature Preparation -> Model Comparison -> Threshold Analysis -> Risk Segmentation -> Retention Prioritization -> Tableau

## SQL Analytics

The full 10,000-customer dataset was loaded into SQLite for descriptive analysis. The SQL layer demonstrates `GROUP BY` aggregate analysis, `CASE WHEN`, CTEs, `HAVING`, `NTILE()`, and `DENSE_RANK()`.

Representative observed patterns:

- Overall churn rate: 20.38%
- Germany observed churn rate: 32.44%
- Inactive customers observed churn rate: 26.87%
- Active customers observed churn rate: 14.27%
- Age 50-59 observed churn rate: 56.04%

These are descriptive segment differences, not causal effects.

## Model Development

The modeling process compared Logistic Regression, Random Forest, and XGBoost using 5-fold stratified cross-validation on the training data.

For Random Forest, imbalance-handling strategies were also compared:

- Standard Random Forest
- `class_weight='balanced'`
- SMOTE

The balanced Random Forest was selected as the strongest candidate based on the cross-validation trade-off, especially recall, F1, and PR-AUC.

## Threshold Selection

The classification threshold was selected using out-of-fold training probabilities, not the held-out test set.

The operating threshold was set to `0.43` based on the training-only F1 analysis. The test set was evaluated only after the threshold was fixed.

## Final Test Results

| Metric | Result |
|---|---:|
| Accuracy | 82.90% |
| Precision | 56.71% |
| Recall | 68.38% |
| F1 | 62.00% |
| ROC-AUC | 0.8640 |
| PR-AUC | 0.6869 |

At the selected threshold, 279 of 408 actual churners were identified.

## Feature Importance

The most influential Random Forest features included:

- Age
- NumOfProducts
- Balance
- EstimatedSalary
- Point Earned
- CreditScore

Feature importance reflects how the model used the available variables. It does not establish causality.

## Customer Risk Segmentation

Model-based risk segmentation was performed only on the 2,000 held-out test customers. The full training population was not presented as independent model-scored customers.

| Risk Segment | Customers | Observed Churn Rate |
|---|---:|---:|
| High | 492 | 56.71% |
| Medium | 411 | 16.30% |
| Low | 1,097 | 5.65% |

## Retention Prioritization

Retention priorities were created from modeled risk and customer attributes:

- Priority 1: high risk + high-value customer
- Priority 2: high risk + inactive customer
- Priority 3: remaining high-risk customers
- Watchlist: medium risk
- Routine: low risk

Priority 1 + Priority 2 contained 370 customers and represented 226 of the 408 actual churners in post-hoc evaluation.

`ActualExited` was not used to create retention priorities, recommended actions, or action reasons. The suggested actions are business responses based on modeled risk and customer attributes, not proven treatments that reduce churn.

## Tableau Dashboards

### Customer Churn Overview

Uses all 10,000 customers for descriptive churn analytics.

### Churn Risk & Retention Prioritization

Uses only the 2,000 held-out scored customers for model-risk and retention analysis.

The dashboards include interactive filters and a customer-level action table for the retention-priority view.

## Repository Structure

```text
Customer-Churn-Retention-Analytics/
|-- data/
|   |-- raw/
|   `-- processed/
|-- notebooks/
|   `-- customer_churn_analysis.ipynb
|-- sql/
|   |-- build_database.py
|   `-- customer_churn_analysis.sql
|-- dashboard/
|   |-- prepare_tableau_data.py
|   |-- data_dictionary.md
|   `-- tableau_build_guide.md
|-- outputs/
|-- images/
|-- requirements.txt
`-- README.md
```

## How to Run

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Build the SQLite database:

```bash
python sql/build_database.py
```

Prepare the Tableau datasets:

```bash
python dashboard/prepare_tableau_data.py
```

The main analysis notebook is:

```text
notebooks/customer_churn_analysis.ipynb
```

## Tools

Python | Pandas | scikit-learn | XGBoost | SQL | SQLite | Tableau
