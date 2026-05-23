-- Run against an existing database when upgrading from the initial schema.
-- New installs can rely on SQLAlchemy create_all instead.

ALTER TABLE column_profiles
    ADD COLUMN IF NOT EXISTS null_pct DOUBLE PRECISION;

ALTER TABLE alerts
    ADD COLUMN IF NOT EXISTS dataset_run_id UUID REFERENCES dataset_runs(id),
    ADD COLUMN IF NOT EXISTS column_name VARCHAR,
    ADD COLUMN IF NOT EXISTS metric VARCHAR,
    ADD COLUMN IF NOT EXISTS previous_value VARCHAR,
    ADD COLUMN IF NOT EXISTS current_value VARCHAR;

-- Backfill null_pct for historical column profiles (optional)
UPDATE column_profiles cp
SET null_pct = ROUND(cp.null_count::numeric / NULLIF(dr.row_count, 0), 6)
FROM dataset_runs dr
WHERE cp.dataset_run_id = dr.id
  AND cp.null_pct IS NULL
  AND dr.row_count > 0;
