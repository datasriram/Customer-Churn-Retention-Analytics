# Tableau Data Dictionary

## `tableau_customer_data.csv`

Contains all 10,000 customers from `customer_churn_clean.csv`. Use this file for descriptive customer and churn analytics.

Important fields:

- `customer_id`: Unique customer identifier.
- `geography`, `gender`, `age`, `tenure`: Customer profile fields.
- `balance`, `num_of_products`, `estimated_salary`: Customer account fields.
- `is_active_member`: Original active-member flag.
- `exited`: Original churn flag where `1` means churned and `0` means retained.
- `age_band`: Dashboard-friendly age group.
- `tenure_band`: Dashboard-friendly tenure group: `0-2 years`, `3-5 years`, `6-8 years`, `9-10 years`.
- `activity_status`: `Active` or `Inactive`.
- `churn_status`: `Churned` or `Retained`.

This file does not include model probabilities, risk segments, or retention priorities.

## `tableau_retention_data.csv`

Contains only the 2,000 held-out customers with model scores and retention priorities. Use this file for risk and retention analysis.

Important fields:

- `CustomerId`: Unique customer identifier.
- `ChurnProbability`: Held-out model churn probability.
- `RiskSegment`: Low, Medium, or High risk segment from the fixed Phase 3A rules.
- `HighValueCustomer`: Flag based on the training-set balance threshold from Phase 3A.
- `InactiveFlag`: Flag based on inactive membership.
- `RetentionPriority`: Priority group from the Phase 3B rules.
- `RecommendedAction`: Suggested retention response.
- `ActionReason`: Short reason for the priority/action.
- `activity_status`: `Active` or `Inactive`.
- `actual_churn_status`: `Churned` or `Retained`.
- `age_band`: Same age groups used in the overall customer dataset.

`ActualExited` is included only for evaluation in the risk and retention view. It was not used to create retention priorities, recommended actions, or action reasons.
