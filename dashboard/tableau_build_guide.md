# Tableau Build Guide

This guide describes how to manually build the Tableau workbook from the prepared CSV files. Use the two datasets separately so the full customer population and the held-out model-scored population are not mixed.

## Data Sources

### Customer Churn Overview

- File: `data/processed/tableau_customer_data.csv`
- Population: 10,000 customers
- Use for descriptive customer and churn analytics.
- Do not add model probabilities, risk segments, or retention-priority fields to this dashboard.

### Risk & Retention Prioritization

- File: `data/processed/tableau_retention_data.csv`
- Population: 2,000 held-out model-scored customers
- Use for model risk and retention-priority analysis.
- `ActualExited` is for post-hoc evaluation only. It was not used to create retention priorities.

## Dashboard 1: Customer Churn Overview

Title: `Customer Churn Overview`

Subtitle: `Descriptive analysis of 10,000 banking customers`

Data source: `tableau_customer_data.csv`

### Calculated Fields

Create `Observed Churn Rate`:

```text
SUM([exited]) / COUNT([customer_id])
```

Format as a percentage with one or two decimal places.

### Sheets

1. **Total Customers KPI**
   - Measure: `COUNTD(customer_id)`

2. **Churned Customers KPI**
   - Count customers where `churn_status = Churned`

3. **Churn Rate KPI**
   - Measure: `Observed Churn Rate`
   - Format as percentage

4. **Average Balance KPI**
   - Measure: `AVG(balance)`
   - Format large values clearly

5. **Churn Rate by Geography**
   - Chart: bar chart
   - Dimension: `geography`
   - Measure: `Observed Churn Rate`
   - Sort descending
   - Tooltip: include customer count

6. **Churn Rate by Age Band**
   - Chart: bar chart
   - Dimension: `age_band`
   - Measure: `Observed Churn Rate`
   - Order: `Under 30`, `30-39`, `40-49`, `50-59`, `60+`

7. **Active vs Inactive Churn**
   - Chart: bar chart
   - Dimension: `activity_status`
   - Measures: `Observed Churn Rate`, customer count in tooltip

8. **Churn by Number of Products**
   - Chart: bar chart
   - Dimension: `num_of_products`
   - Measure: `Observed Churn Rate`

9. **Churn Status Distribution**
   - Chart: simple bar chart preferred
   - Dimension: `churn_status`
   - Measure: customer count

### Filters

Add these filters and apply them to all relevant Dashboard 1 sheets:

- `geography`
- `gender`
- `card_type`

### Layout

- Top row: Total Customers | Churned Customers | Churn Rate | Avg Balance
- Middle: Churn Rate by Geography | Churn Rate by Age Band
- Bottom: Active vs Inactive | Churn by Number of Products | Churn Status Distribution
- Place filters on the right side or top-right.
- Keep the layout simple, professional, and easy to scan.

## Dashboard 2: Risk & Retention Prioritization

Title: `Churn Risk & Retention Prioritization`

Subtitle: `Model-based analysis of 2,000 held-out customers`

Data source: `tableau_retention_data.csv`

### Calculated Fields

Create `Observed Churn Rate - Post-Hoc`:

```text
SUM([ActualExited]) / COUNT([CustomerId])
```

Format as a percentage. Use this only for evaluation views, not as an input to prioritization logic.

Create `Priority 1 + 2 Flag`:

```text
[RetentionPriority] = "Priority 1" OR [RetentionPriority] = "Priority 2"
```

### Sheets

1. **Scored Customers KPI**
   - Measure: `COUNTD(CustomerId)`

2. **High Risk Customers KPI**
   - Count customers where `RiskSegment = High`

3. **Priority 1 + Priority 2 KPI**
   - Count customers where `Priority 1 + 2 Flag` is true

4. **Average Churn Probability KPI**
   - Measure: `AVG(ChurnProbability)`
   - Format as percentage

5. **Risk Segment Distribution**
   - Chart: bar chart
   - Dimension: `RiskSegment`
   - Measure: customer count
   - Order: `High`, `Medium`, `Low`

6. **Retention Priority Distribution**
   - Chart: horizontal bar chart
   - Dimension: `RetentionPriority`
   - Measure: customer count
   - Order: `Priority 1`, `Priority 2`, `Priority 3`, `Watchlist`, `Routine`

7. **Average Churn Probability by Priority**
   - Chart: bar chart
   - Dimension: `RetentionPriority`
   - Measure: `AVG(ChurnProbability)`
   - Format as percentage
   - Use the same logical priority order

8. **Observed Churn Rate by Priority — Post-Hoc Evaluation**
   - Chart: bar chart
   - Dimension: `RetentionPriority`
   - Measure: `Observed Churn Rate - Post-Hoc`
   - This is an evaluation view only. Do not present actual churn as an input to the priority rules.

9. **Customer Action Table**
   - Table fields:
     - `CustomerId`
     - `ChurnProbability`
     - `RiskSegment`
     - `RetentionPriority`
     - `Balance`
     - `activity_status`
     - `RecommendedAction`
   - Sort by `RetentionPriority`, then by `ChurnProbability` descending where practical.

### Filters

Add these filters and apply them only to Dashboard 2 sheets:

- `RiskSegment`
- `RetentionPriority`
- `Geography`
- `activity_status`

### Layout

- Top row: Scored Customers | High Risk | Priority 1 + 2 | Avg Churn Probability
- Middle: Risk Segment Distribution | Retention Priority Distribution | Average Probability by Priority
- Lower section: Observed Churn Rate by Priority — Post-Hoc Evaluation
- Bottom: Customer Action Table
- Make the held-out 2,000-customer population clear in the subtitle.

## Design Guidelines

- Use a simple professional layout.
- Keep colors consistent across both dashboards.
- Avoid many different colors, gradients, decorative icons, animations, and oversized titles.
- Format percentages with one or two decimal places.
- Format balance values so large numbers are readable.
- Avoid long explanatory paragraphs.
- Use descriptive language such as observed churn rate and segment differences.
- Do not use causal language.
- Do not show `Complain`.
- Do not show technical model-training identifiers or fields that a business viewer does not need.

## Final Workbook

The Tableau workbook should contain only:

- Dashboard 1 — Customer Churn Overview
- Dashboard 2 — Risk & Retention Prioritization

Do not create extra dashboards unless the project scope changes.

## Build Checklist

Dashboard 1 sheets:

- [ ] Total Customers KPI
- [ ] Churned Customers KPI
- [ ] Churn Rate KPI
- [ ] Average Balance KPI
- [ ] Churn Rate by Geography
- [ ] Churn Rate by Age Band
- [ ] Active vs Inactive Churn
- [ ] Churn by Number of Products
- [ ] Churn Status Distribution

Dashboard 2 sheets:

- [ ] Scored Customers KPI
- [ ] High Risk Customers KPI
- [ ] Priority 1 + Priority 2 KPI
- [ ] Average Churn Probability KPI
- [ ] Risk Segment Distribution
- [ ] Retention Priority Distribution
- [ ] Average Churn Probability by Priority
- [ ] Observed Churn Rate by Priority — Post-Hoc Evaluation
- [ ] Customer Action Table
