-- =============================================================================
-- 05_create_indexes.sql — RouteIQ Phase 2
-- Only indexes with a concrete, cited justification are created. PostgreSQL
-- does NOT automatically index a column just because it is a foreign key
-- (unlike the primary-key side, which gets one implicitly) — every FK column
-- on FactDelivery is indexed for that reason. A few additional indexes are
-- added for filter patterns explicitly named in KPI_DEFINITIONS.md /
-- SQL_ANALYSIS_PLAN.md. Nothing is indexed "just in case."
--
-- Already covered without a new index here:
--   - FactDelivery.order_id           -> UNIQUE constraint (03) creates one
--   - Every Dim*.<name>_key            -> PRIMARY KEY creates one
--   - DimArea.area_name, DimCategory.category_name, DimVehicle.vehicle_name,
--     DimWeatherTraffic(weather,traffic), DimAgent(agent_age,agent_rating)
--                                       -> UNIQUE constraints (02) create one
--
-- Run as: psql -U postgres -f 05_create_indexes.sql
-- =============================================================================

SET search_path TO routeiq, public;

-- ---- FK join indexes (one per FactDelivery -> Dim* relationship) ----------

CREATE INDEX idx_fact_agent_key            ON routeiq."FactDelivery" (agent_key);
CREATE INDEX idx_fact_date_key             ON routeiq."FactDelivery" (date_key);
CREATE INDEX idx_fact_area_key             ON routeiq."FactDelivery" (area_key);
CREATE INDEX idx_fact_category_key         ON routeiq."FactDelivery" (category_key);
CREATE INDEX idx_fact_weather_traffic_key  ON routeiq."FactDelivery" (weather_traffic_key);
CREATE INDEX idx_fact_vehicle_key          ON routeiq."FactDelivery" (vehicle_key);

-- ---- Documented analytical filter patterns ---------------------------------

-- sla_breach_flag is filtered or grouped on in nearly every P0/P1 query in
-- SQL_ANALYSIS_PLAN.md (Q1, Q8, Q12, Q13, Q14, Q16, Q20) and is the field
-- every headline KPI in KPI_DEFINITIONS.md (#1, #2, #7) depends on.
CREATE INDEX idx_fact_sla_breach_flag ON routeiq."FactDelivery" (sla_breach_flag);

-- week_number drives the weekly trend / week-over-week volatility KPI
-- (KPI_DEFINITIONS.md #8; SQL_ANALYSIS_PLAN.md Q11, Q17).
CREATE INDEX idx_fact_week_number ON routeiq."FactDelivery" (week_number);
