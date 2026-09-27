-- =============================================================================
-- Q29 - Are the numbers behind the dashboard internally consistent?
-- Business question: before anyone reads a KPI, do the cuts add up to the totals, and does the
-- stored SLA flag equal a fresh recomputation? Each row is one check with PASS/FAIL.
-- This is CROSS-LAYER RECONCILIATION (SQL vs itself and vs frozen figures), not proof that the
-- source data is right. Independent recomputation from the CSV lives in src/routeiq/validation.
-- =============================================================================
SET search_path TO routeiq, public;

WITH v AS (SELECT * FROM routeiq.vw_analytical_deliveries),
thr AS (
    SELECT category, PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY delivery_time_minutes) AS p75
    FROM v GROUP BY category
),
checks AS (
    SELECT 1 AS id, 'total deliveries = 43,648 (frozen cleaned row count)' AS check_name,
           43648::numeric AS expected, (SELECT COUNT(*) FROM v)::numeric AS actual
    UNION ALL SELECT 2, 'distinct order_id = total deliveries (no duplicates)',
           (SELECT COUNT(*) FROM v)::numeric, (SELECT COUNT(DISTINCT order_id) FROM v)::numeric
    UNION ALL SELECT 3, 'view rows = FactDelivery rows (no join fan-out)',
           (SELECT COUNT(*) FROM routeiq."FactDelivery")::numeric, (SELECT COUNT(*) FROM v)::numeric
    UNION ALL SELECT 4, 'total breaches = 10,328 (frozen)', 10328::numeric, (SELECT SUM(breach_flag) FROM v)::numeric
    UNION ALL SELECT 5, 'recomputed breach_flag vs stored sla_breach_flag: mismatches = 0',
           0::numeric,
           (SELECT COUNT(*) FROM v JOIN routeiq."FactDelivery" f USING (order_id)
             WHERE v.breach_flag <> f.sla_breach_flag::int)::numeric
    UNION ALL SELECT 6, 'stored category threshold vs fresh PERCENTILE_CONT(0.75): mismatches = 0',
           0::numeric,
           (SELECT COUNT(*) FROM (SELECT DISTINCT category, sla_threshold_minutes FROM v) s
             JOIN thr USING (category) WHERE ABS(s.sla_threshold_minutes - thr.p75) > 1e-9)::numeric
    UNION ALL SELECT 7, 'every category has exactly one threshold',
           16::numeric, (SELECT COUNT(*) FROM (SELECT category FROM v GROUP BY category HAVING COUNT(DISTINCT sla_threshold_minutes) = 1) x)::numeric
    UNION ALL SELECT 8, 'sum of breaches by traffic = total',
           (SELECT SUM(breach_flag) FROM v)::numeric,
           (SELECT SUM(b) FROM (SELECT SUM(breach_flag) AS b FROM v GROUP BY traffic) t)::numeric
    UNION ALL SELECT 9, 'sum of breaches by order hour = total',
           (SELECT SUM(breach_flag) FROM v)::numeric,
           (SELECT SUM(b) FROM (SELECT SUM(breach_flag) AS b FROM v GROUP BY order_hour) t)::numeric
    UNION ALL SELECT 10, 'on-time % + breach % = 100',
           100::numeric, (SELECT ROUND(100.0 * SUM(1 - breach_flag) / COUNT(*) + 100.0 * SUM(breach_flag) / COUNT(*), 6) FROM v)::numeric
    UNION ALL SELECT 11, 'valid ratings = 43,594 (54 rows have none)',
           43594::numeric, (SELECT COUNT(agent_rating) FROM v)::numeric
    UNION ALL SELECT 12, 'Semi-Urban: 152 deliveries, all breach',
           152::numeric, (SELECT COUNT(*) FROM v WHERE area = 'Semi-Urban' AND breach_flag = 1)::numeric
    UNION ALL SELECT 13, 'rating/age analysis population (excl. Semi-Urban and unrated rows) = 43,442 rows',
           43442::numeric, (SELECT COUNT(*) FROM v WHERE area <> 'Semi-Urban' AND rating_lt_4_5 IS NOT NULL)::numeric
    UNION ALL SELECT 14, 'peak-hour flag = hours 17-23 only',
           0::numeric, (SELECT COUNT(*) FROM v WHERE (is_peak_hour = 1) <> (order_hour BETWEEN 17 AND 23))::numeric
)
SELECT id, check_name, expected, actual,
       CASE WHEN expected = actual THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks
ORDER BY id;
