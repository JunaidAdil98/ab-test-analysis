-- =====================================================================
-- analysis_queries.sql  —  A/B experiment metrics in MySQL 8
-- Mirrors analysis.py so SQL and Python can be cross-checked.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. SAMPLE-RATIO MISMATCH (SRM) — counts should be ~50/50
-- ---------------------------------------------------------------------
SELECT
    variant,
    COUNT(*)                                              AS users,
    ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 4)            AS share
FROM experiment
GROUP BY variant;

-- ---------------------------------------------------------------------
-- 2. PRIMARY METRIC — conversion rate, RPU, and the z-statistic in SQL
--    (p-value itself is computed in the analysis layer)
-- ---------------------------------------------------------------------
WITH g AS (
    SELECT
        variant,
        COUNT(*)              AS n,
        SUM(converted)        AS conv,
        AVG(converted)        AS cr,
        AVG(revenue)          AS rpu
    FROM experiment
    GROUP BY variant
),
p AS (
    SELECT
        MAX(CASE WHEN variant='control'   THEN cr   END) AS cr_c,
        MAX(CASE WHEN variant='treatment' THEN cr   END) AS cr_t,
        MAX(CASE WHEN variant='control'   THEN n    END) AS n_c,
        MAX(CASE WHEN variant='treatment' THEN n    END) AS n_t,
        SUM(conv) / SUM(n)                               AS p_pool
    FROM g
)
SELECT
    ROUND(cr_c*100, 3)                                            AS control_cr_pct,
    ROUND(cr_t*100, 3)                                            AS treatment_cr_pct,
    ROUND((cr_t - cr_c)*100, 3)                                   AS abs_lift_pp,
    ROUND((cr_t - cr_c)/cr_c*100, 2)                              AS rel_lift_pct,
    ROUND((cr_t - cr_c) /
          SQRT(p_pool*(1-p_pool)*(1.0/n_c + 1.0/n_t)), 3)         AS z_statistic
FROM p;

-- ---------------------------------------------------------------------
-- 3. SEGMENT (heterogeneous) EFFECTS — conversion lift by device & user_type
-- ---------------------------------------------------------------------
SELECT
    'device' AS dimension, device AS segment,
    ROUND(AVG(CASE WHEN variant='control'   THEN converted END)*100, 2) AS control_cr,
    ROUND(AVG(CASE WHEN variant='treatment' THEN converted END)*100, 2) AS treatment_cr,
    ROUND((AVG(CASE WHEN variant='treatment' THEN converted END)
         - AVG(CASE WHEN variant='control'   THEN converted END))*100, 2) AS abs_lift_pp
FROM experiment GROUP BY device
UNION ALL
SELECT
    'user_type', user_type,
    ROUND(AVG(CASE WHEN variant='control'   THEN converted END)*100, 2),
    ROUND(AVG(CASE WHEN variant='treatment' THEN converted END)*100, 2),
    ROUND((AVG(CASE WHEN variant='treatment' THEN converted END)
         - AVG(CASE WHEN variant='control'   THEN converted END))*100, 2)
FROM experiment GROUP BY user_type
ORDER BY dimension, segment;

-- ---------------------------------------------------------------------
-- 4. CUMULATIVE CONVERSION OVER TIME — window function (peeking check)
-- ---------------------------------------------------------------------
WITH daily AS (
    SELECT variant, visit_date,
           SUM(converted) AS conv, COUNT(*) AS n
    FROM experiment GROUP BY variant, visit_date
)
SELECT
    variant, visit_date,
    ROUND(
        SUM(conv) OVER (PARTITION BY variant ORDER BY visit_date) /
        SUM(n)    OVER (PARTITION BY variant ORDER BY visit_date) * 100, 3
    ) AS cumulative_cr_pct
FROM daily
ORDER BY variant, visit_date;

-- ---------------------------------------------------------------------
-- 5. AVERAGE ORDER VALUE among converters (guardrail: no cannibalization)
-- ---------------------------------------------------------------------
SELECT
    variant,
    COUNT(*)            AS orders,
    ROUND(AVG(revenue), 2) AS avg_order_value
FROM experiment
WHERE converted = 1
GROUP BY variant;
