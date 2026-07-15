-- Phase 1: dataset metadata, freshness, configurable rules, incidents and trends.
-- Run against an existing database when upgrading. New installs can rely on
-- SQLAlchemy create_all instead.

-- 1. Dataset ownership / governance metadata + freshness expectations.
ALTER TABLE datasets
    ADD COLUMN IF NOT EXISTS owner VARCHAR,
    ADD COLUMN IF NOT EXISTS team VARCHAR,
    ADD COLUMN IF NOT EXISTS domain VARCHAR,
    ADD COLUMN IF NOT EXISTS criticality VARCHAR NOT NULL DEFAULT 'medium',
    ADD COLUMN IF NOT EXISTS expected_freshness_hours INTEGER;

-- 2. Richer column profiling.
ALTER TABLE column_profiles
    ADD COLUMN IF NOT EXISTS distinct_count INTEGER;

-- 3. Configurable data-quality rules.
CREATE TABLE IF NOT EXISTS dataset_rules (
    id UUID PRIMARY KEY,
    dataset_id UUID REFERENCES datasets(id),
    column_name VARCHAR,
    rule_type VARCHAR NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    severity VARCHAR NOT NULL DEFAULT 'high',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Incidents (group one or more alerts).
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY,
    dataset_id UUID REFERENCES datasets(id),
    title VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'open',
    severity VARCHAR NOT NULL DEFAULT 'medium',
    assignee VARCHAR,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

-- 5. Link alerts to incidents.
ALTER TABLE alerts
    ADD COLUMN IF NOT EXISTS incident_id UUID REFERENCES incidents(id);

CREATE INDEX IF NOT EXISTS idx_alerts_incident_id ON alerts(incident_id);
CREATE INDEX IF NOT EXISTS idx_incidents_dataset_status ON incidents(dataset_id, status);
CREATE INDEX IF NOT EXISTS idx_dataset_rules_dataset ON dataset_rules(dataset_id);
