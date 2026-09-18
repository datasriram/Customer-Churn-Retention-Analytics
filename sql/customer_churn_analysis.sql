-- 1. Overall customer and churn KPIs
SELECT
    COUNT(*) AS total_customers,
    SUM(exited) AS total_churned_customers,
    COUNT(*) - SUM(exited) AS total_retained_customers,
    ROUND(AVG(exited) * 100.0, 2) AS overall_churn_rate_pct,
    ROUND(AVG(balance), 2) AS average_balance
FROM customers;

-- 2. Churn by geography
SELECT
    geography,
    COUNT(*) AS customer_count,
    SUM(exited) AS churn_count,
    ROUND(AVG(exited) * 100.0, 2) AS observed_churn_rate_pct,
    ROUND(AVG(balance), 2) AS average_balance
FROM customers
GROUP BY geography
ORDER BY observed_churn_rate_pct DESC;

-- 3. Churn by gender
SELECT
    gender,
    COUNT(*) AS customer_count,
    SUM(exited) AS churn_count,
    ROUND(AVG(exited) * 100.0, 2) AS observed_churn_rate_pct
FROM customers
GROUP BY gender
ORDER BY observed_churn_rate_pct DESC;

-- 4. Active vs inactive customers
SELECT
    CASE
        WHEN is_active_member = 1 THEN 'Active'
        ELSE 'Inactive'
    END AS activity_status,
    COUNT(*) AS customer_count,
    SUM(exited) AS churn_count,
    ROUND(AVG(exited) * 100.0, 2) AS observed_churn_rate_pct,
    ROUND(AVG(balance), 2) AS average_balance
FROM customers
GROUP BY activity_status
ORDER BY observed_churn_rate_pct DESC;

-- 5. Churn by number of products
SELECT
    num_of_products,
    COUNT(*) AS customer_count,
    SUM(exited) AS churn_count,
    ROUND(AVG(exited) * 100.0, 2) AS observed_churn_rate_pct
FROM customers
GROUP BY num_of_products
ORDER BY num_of_products;

-- 6. Age-band analysis
SELECT
    CASE
        WHEN age < 30 THEN 'Under 30'
        WHEN age BETWEEN 30 AND 39 THEN '30-39'
        WHEN age BETWEEN 40 AND 49 THEN '40-49'
        WHEN age BETWEEN 50 AND 59 THEN '50-59'
        ELSE '60+'
    END AS age_band,
    COUNT(*) AS customer_count,
    SUM(exited) AS churn_count,
    ROUND(AVG(exited) * 100.0, 2) AS observed_churn_rate_pct,
    ROUND(AVG(balance), 2) AS average_balance
FROM customers
GROUP BY age_band
ORDER BY
    CASE age_band
        WHEN 'Under 30' THEN 1
        WHEN '30-39' THEN 2
        WHEN '40-49' THEN 3
        WHEN '50-59' THEN 4
        ELSE 5
    END;

-- 7. Tenure-band analysis
SELECT
    CASE
        WHEN tenure BETWEEN 0 AND 2 THEN '0-2 years'
        WHEN tenure BETWEEN 3 AND 5 THEN '3-5 years'
        WHEN tenure BETWEEN 6 AND 8 THEN '6-8 years'
        ELSE '9-10 years'
    END AS tenure_band,
    COUNT(*) AS customer_count,
    SUM(exited) AS churn_count,
    ROUND(AVG(exited) * 100.0, 2) AS observed_churn_rate_pct
FROM customers
GROUP BY tenure_band
ORDER BY
    CASE tenure_band
        WHEN '0-2 years' THEN 1
        WHEN '3-5 years' THEN 2
        WHEN '6-8 years' THEN 3
        ELSE 4
    END;

-- 8. Balance quartile analysis
WITH balance_quartiles AS (
    SELECT
        customer_id,
        balance,
        exited,
        NTILE(4) OVER (ORDER BY balance) AS balance_quartile
    FROM customers
)
SELECT
    balance_quartile,
    COUNT(*) AS customer_count,
    ROUND(MIN(balance), 2) AS minimum_balance,
    ROUND(MAX(balance), 2) AS maximum_balance,
    SUM(exited) AS churn_count,
    ROUND(AVG(exited) * 100.0, 2) AS observed_churn_rate_pct
FROM balance_quartiles
GROUP BY balance_quartile
ORDER BY balance_quartile;

-- 9. Card type analysis
SELECT
    card_type,
    COUNT(*) AS customer_count,
    SUM(exited) AS churn_count,
    ROUND(AVG(exited) * 100.0, 2) AS observed_churn_rate_pct,
    ROUND(AVG(satisfaction_score), 2) AS average_satisfaction_score
FROM customers
GROUP BY card_type
ORDER BY observed_churn_rate_pct DESC;

-- 10. Satisfaction analysis
SELECT
    satisfaction_score,
    COUNT(*) AS customer_count,
    ROUND(AVG(exited) * 100.0, 2) AS observed_churn_rate_pct,
    ROUND(AVG(balance), 2) AS average_balance
FROM customers
GROUP BY satisfaction_score
ORDER BY satisfaction_score;

-- 11. Combined customer segment analysis
WITH geography_activity_segments AS (
    SELECT
        geography,
        CASE
            WHEN is_active_member = 1 THEN 'Active'
            ELSE 'Inactive'
        END AS activity_status,
        exited
    FROM customers
)
SELECT
    geography,
    activity_status,
    COUNT(*) AS customer_count,
    SUM(exited) AS churn_count,
    ROUND(AVG(exited) * 100.0, 2) AS observed_churn_rate_pct
FROM geography_activity_segments
GROUP BY geography, activity_status
HAVING COUNT(*) >= 50
ORDER BY observed_churn_rate_pct DESC;

-- 12. Rank observed high-churn segments
WITH segment_base AS (
    SELECT
        geography,
        CASE
            WHEN is_active_member = 1 THEN 'Active'
            ELSE 'Inactive'
        END AS activity_status,
        CASE
            WHEN age < 30 THEN 'Under 30'
            WHEN age BETWEEN 30 AND 39 THEN '30-39'
            WHEN age BETWEEN 40 AND 49 THEN '40-49'
            WHEN age BETWEEN 50 AND 59 THEN '50-59'
            ELSE '60+'
        END AS age_band,
        exited
    FROM customers
),
segment_summary AS (
    SELECT
        geography || ' | ' || activity_status || ' | ' || age_band AS segment_label,
        geography,
        activity_status,
        age_band,
        COUNT(*) AS customer_count,
        SUM(exited) AS churn_count,
        AVG(exited) * 100.0 AS observed_churn_rate_pct
    FROM segment_base
    GROUP BY geography, activity_status, age_band
    HAVING COUNT(*) >= 50
),
ranked_segments AS (
    SELECT
        DENSE_RANK() OVER (ORDER BY observed_churn_rate_pct DESC) AS churn_rate_rank,
        segment_label,
        geography,
        activity_status,
        age_band,
        customer_count,
        churn_count,
        ROUND(observed_churn_rate_pct, 2) AS observed_churn_rate_pct
    FROM segment_summary
)
SELECT
    churn_rate_rank,
    segment_label,
    geography,
    activity_status,
    age_band,
    customer_count,
    churn_count,
    observed_churn_rate_pct
FROM ranked_segments
ORDER BY churn_rate_rank, customer_count DESC
LIMIT 10;
