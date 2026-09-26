-- =============================================================================
-- 01_create_schema.sql — RouteIQ Phase 2
-- Creates the dedicated PostgreSQL schema all star-schema objects live in.
--
-- Design note: a single schema ("routeiq") inside the default "postgres"
-- database is used, rather than provisioning a new database. STAR_SCHEMA.md
-- does not mandate a database name; this keeps the footprint minimal and
-- matches this file's own scope (a schema, not a database).
--
-- Run as: psql -U postgres -f 01_create_schema.sql
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS routeiq;

COMMENT ON SCHEMA routeiq IS
    'RouteIQ star schema (Phase 2): FactDelivery + six dimensions, built from '
    'the frozen Phase 1 outputs data/cleaned/cleaned_delivery.csv and '
    'data/cleaned/sla_reference.csv per STAR_SCHEMA.md.';

-- All subsequent scripts assume this search_path.
SET search_path TO routeiq, public;
