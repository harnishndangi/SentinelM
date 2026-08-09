-- ====================================================================
-- SentinelML - Autonomous ML Reliability & Self-Healing Platform
-- Complete PostgreSQL / Supabase DDL Schema & Initial Seed Data
-- ====================================================================
-- Instructions: Copy and paste this entire SQL script into the Supabase SQL Editor
-- (https://supabase.com/dashboard/project/_/sql) and click "RUN".
-- ====================================================================

BEGIN;

-- 1. Create Enums
DO $$ BEGIN
    CREATE TYPE model_version_status AS ENUM ('TRAINING', 'CANDIDATE', 'STAGING', 'PRODUCTION', 'ARCHIVED', 'FAILED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE incident_severity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE incident_status AS ENUM ('OPEN', 'INVESTIGATING', 'RETRAINING', 'RESOLVED', 'FAILED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE deployment_status AS ENUM ('PENDING', 'ACTIVE', 'FAILED', 'ROLLED_BACK', 'ARCHIVED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE alert_status AS ENUM ('TRIGGERED', 'ACKNOWLEDGED', 'RESOLVED', 'MUTED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE alert_severity AS ENUM ('INFO', 'WARNING', 'ERROR', 'CRITICAL');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE drift_type AS ENUM ('DATA_DRIFT', 'CONCEPT_DRIFT', 'FEATURE_DRIFT', 'PREDICTION_DRIFT');
EXCEPTION WHEN duplicate_object THEN null; END $$;


-- 2. Create Tables

-- Users
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'engineer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- ML Models
CREATE TABLE IF NOT EXISTS ml_models (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    framework VARCHAR(100),
    task_type VARCHAR(100),
    owner_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_ml_models_name ON ml_models(name);

-- Model Versions
CREATE TABLE IF NOT EXISTS model_versions (
    id VARCHAR(36) PRIMARY KEY,
    model_id VARCHAR(36) NOT NULL REFERENCES ml_models(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    status model_version_status NOT NULL DEFAULT 'TRAINING',
    artifact_uri VARCHAR(512),
    parameters JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_model_versions_model_id ON model_versions(model_id);
CREATE INDEX IF NOT EXISTS ix_model_versions_status ON model_versions(status);

-- Model Metrics
CREATE TABLE IF NOT EXISTS model_metrics (
    id VARCHAR(36) PRIMARY KEY,
    model_version_id VARCHAR(36) NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    split VARCHAR(50) NOT NULL DEFAULT 'test',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_model_metrics_model_version_id ON model_metrics(model_version_id);
CREATE INDEX IF NOT EXISTS ix_model_metrics_metric_name ON model_metrics(metric_name);

-- Datasets
CREATE TABLE IF NOT EXISTS datasets (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    data_type VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_datasets_name ON datasets(name);

-- Dataset Versions
CREATE TABLE IF NOT EXISTS dataset_versions (
    id VARCHAR(36) PRIMARY KEY,
    dataset_id VARCHAR(36) NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    num_rows INTEGER,
    num_features INTEGER,
    storage_path VARCHAR(512),
    checksum VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_dataset_versions_dataset_id ON dataset_versions(dataset_id);

-- Predictions
CREATE TABLE IF NOT EXISTS predictions (
    id VARCHAR(36) PRIMARY KEY,
    model_version_id VARCHAR(36) NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    prediction_id VARCHAR(255) NOT NULL,
    input_features JSONB,
    output_prediction JSONB,
    confidence_score DOUBLE PRECISION,
    latency_ms DOUBLE PRECISION,
    actual_label DOUBLE PRECISION,
    label_received_at JSONB,
    error_val DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_predictions_model_version_id ON predictions(model_version_id);
CREATE INDEX IF NOT EXISTS ix_predictions_prediction_id ON predictions(prediction_id);
CREATE INDEX IF NOT EXISTS idx_prediction_model_created ON predictions(model_version_id, created_at);

-- Feature Logs
CREATE TABLE IF NOT EXISTS feature_logs (
    id VARCHAR(36) PRIMARY KEY,
    prediction_id VARCHAR(36) NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    feature_value DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_feature_logs_prediction_id ON feature_logs(prediction_id);
CREATE INDEX IF NOT EXISTS ix_feature_logs_feature_name ON feature_logs(feature_name);

-- Ground Truth Logs (Delayed Label Feedback)
CREATE TABLE IF NOT EXISTS ground_truth_logs (
    id VARCHAR(36) PRIMARY KEY,
    prediction_id VARCHAR(36) NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    actual_label DOUBLE PRECISION NOT NULL,
    feedback_source VARCHAR(100) NOT NULL DEFAULT 'manual_review',
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_ground_truth_logs_prediction_id ON ground_truth_logs(prediction_id);
CREATE INDEX IF NOT EXISTS ix_ground_truth_logs_received_at ON ground_truth_logs(received_at);

-- Drift Events
CREATE TABLE IF NOT EXISTS drift_events (
    id VARCHAR(36) PRIMARY KEY,
    model_version_id VARCHAR(36) NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    dataset_version_id VARCHAR(36) REFERENCES dataset_versions(id) ON DELETE SET NULL,
    drift_type drift_type NOT NULL DEFAULT 'DATA_DRIFT',
    is_actionable BOOLEAN NOT NULL DEFAULT FALSE,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_drift_events_model_version_id ON drift_events(model_version_id);
CREATE INDEX IF NOT EXISTS ix_drift_events_drift_type ON drift_events(drift_type);

-- Drift Scores
CREATE TABLE IF NOT EXISTS drift_scores (
    id VARCHAR(36) PRIMARY KEY,
    drift_event_id VARCHAR(36) NOT NULL REFERENCES drift_events(id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    method VARCHAR(100) NOT NULL,
    p_value DOUBLE PRECISION,
    drift_score DOUBLE PRECISION NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_drift_scores_drift_event_id ON drift_scores(drift_event_id);
CREATE INDEX IF NOT EXISTS ix_drift_scores_feature_name ON drift_scores(feature_name);

-- Incidents
CREATE TABLE IF NOT EXISTS incidents (
    id VARCHAR(36) PRIMARY KEY,
    model_version_id VARCHAR(36) NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    severity incident_severity NOT NULL DEFAULT 'MEDIUM',
    status incident_status NOT NULL DEFAULT 'OPEN',
    opened_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_incidents_model_version_id ON incidents(model_version_id);
CREATE INDEX IF NOT EXISTS ix_incidents_severity ON incidents(severity);
CREATE INDEX IF NOT EXISTS ix_incidents_status ON incidents(status);

-- Incident Events
CREATE TABLE IF NOT EXISTS incident_events (
    id VARCHAR(36) PRIMARY KEY,
    incident_id VARCHAR(36) NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_incident_events_incident_id ON incident_events(incident_id);

-- Training Runs
CREATE TABLE IF NOT EXISTS training_runs (
    id VARCHAR(36) PRIMARY KEY,
    model_version_id VARCHAR(36) NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    dataset_version_id VARCHAR(36) REFERENCES dataset_versions(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    start_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMPTZ,
    logs_path VARCHAR(512),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_training_runs_model_version_id ON training_runs(model_version_id);
CREATE INDEX IF NOT EXISTS ix_training_runs_status ON training_runs(status);

-- Experiments
CREATE TABLE IF NOT EXISTS experiments (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_experiments_name ON experiments(name);

-- Experiment Metrics
CREATE TABLE IF NOT EXISTS experiment_metrics (
    id VARCHAR(36) PRIMARY KEY,
    experiment_id VARCHAR(36) NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    step INTEGER NOT NULL DEFAULT 0,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_experiment_metrics_experiment_id ON experiment_metrics(experiment_id);
CREATE INDEX IF NOT EXISTS ix_experiment_metrics_metric_name ON experiment_metrics(metric_name);

-- Deployments
CREATE TABLE IF NOT EXISTS deployments (
    id VARCHAR(36) PRIMARY KEY,
    model_version_id VARCHAR(36) NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    environment VARCHAR(50) NOT NULL DEFAULT 'production',
    status deployment_status NOT NULL DEFAULT 'PENDING',
    endpoint_url VARCHAR(512),
    deployed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    terminated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_deployments_model_version_id ON deployments(model_version_id);
CREATE INDEX IF NOT EXISTS ix_deployments_environment ON deployments(environment);
CREATE INDEX IF NOT EXISTS ix_deployments_status ON deployments(status);

-- Deployment Metrics
CREATE TABLE IF NOT EXISTS deployment_metrics (
    id VARCHAR(36) PRIMARY KEY,
    deployment_id VARCHAR(36) NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    request_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    latency_p95_ms DOUBLE PRECISION,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_deployment_metrics_deployment_id ON deployment_metrics(deployment_id);
CREATE INDEX IF NOT EXISTS ix_deployment_metrics_timestamp ON deployment_metrics(timestamp);

-- Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(36) PRIMARY KEY,
    incident_id VARCHAR(36) REFERENCES incidents(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity alert_severity NOT NULL DEFAULT 'WARNING',
    status alert_status NOT NULL DEFAULT 'TRIGGERED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS ix_alerts_status ON alerts(status);

-- Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    details JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX IF NOT EXISTS ix_audit_logs_timestamp ON audit_logs(timestamp);

-- Alembic Version Tracking Table
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL CONSTRAINT alembic_version_pkc PRIMARY KEY
);

-- Insert version revision
INSERT INTO alembic_version (version_num) VALUES ('993712ccdc26') ON CONFLICT DO NOTHING;


-- ====================================================================
-- 3. Initial Seed Data (FraudDetector v1 in PRODUCTION)
-- ====================================================================

-- Insert Model
INSERT INTO ml_models (id, name, description, framework, task_type)
VALUES (
    'm-fraud-detector-001',
    'FraudDetector',
    'Real-time financial transaction anomaly and fraud detection model.',
    'scikit-learn',
    'classification'
) ON CONFLICT (name) DO NOTHING;

-- Insert Model Version 1 (PRODUCTION)
INSERT INTO model_versions (id, model_id, version, status, artifact_uri, parameters)
VALUES (
    'mv-fraud-detector-v1',
    'm-fraud-detector-001',
    '1',
    'PRODUCTION',
    's3://sentinelml-artifacts/models/FraudDetector/v1/model.joblib',
    '{"n_estimators": 100, "max_depth": 10, "random_state": 42}'::jsonb
) ON CONFLICT DO NOTHING;

-- Insert Sample Evaluation Metrics
INSERT INTO model_metrics (id, model_version_id, metric_name, metric_value, split)
VALUES 
    ('mm-fd-001', 'mv-fraud-detector-v1', 'precision', 0.92, 'test'),
    ('mm-fd-002', 'mv-fraud-detector-v1', 'recall', 0.93, 'test'),
    ('mm-fd-003', 'mv-fraud-detector-v1', 'f1', 0.91, 'test'),
    ('mm-fd-004', 'mv-fraud-detector-v1', 'roc_auc', 0.97, 'test'),
    ('mm-fd-005', 'mv-fraud-detector-v1', 'pr_auc', 0.94, 'test')
ON CONFLICT DO NOTHING;

-- 4. Enable Supabase Realtime for Live Streaming
DO $$ 
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE incidents;
    ALTER PUBLICATION supabase_realtime ADD TABLE drift_events;
    ALTER PUBLICATION supabase_realtime ADD TABLE alerts;
    ALTER PUBLICATION supabase_realtime ADD TABLE predictions;
    ALTER PUBLICATION supabase_realtime ADD TABLE ground_truth_logs;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

COMMIT;

