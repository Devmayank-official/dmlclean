-- Migration 002: Add schedules table
-- Adds support for persistent scheduled cleaning jobs

-- Scheduled Jobs Table
-- Stores scheduled cleaning operations with APScheduler integration
CREATE TABLE IF NOT EXISTS schedules (
    id              TEXT PRIMARY KEY,     -- UUID
    name            TEXT NOT NULL,        -- Human-readable job name
    cron_expression TEXT NOT NULL,        -- Cron expression (e.g., "0 3 * * *")
    human_readable  TEXT,                 -- Natural language description
    enabled         INTEGER DEFAULT 1,    -- 1=active, 0=paused
    profile         TEXT DEFAULT 'developer', -- Cleaning profile to use
    scan_mode       TEXT DEFAULT 'fast',  -- fast | deep | custom
    clean_mode      TEXT DEFAULT 'dry-run', -- dry-run | trash | permanent
    categories      TEXT,                 -- JSON array of category names
    min_age_days    INTEGER DEFAULT 0,    -- Minimum file age to clean
    min_size_mb     INTEGER DEFAULT 0,    -- Minimum file size to clean
    last_run        TEXT,                 -- ISO 8601 timestamp of last run
    next_run        TEXT,                 -- ISO 8601 timestamp of next run
    run_count       INTEGER DEFAULT 0,    -- Total number of successful runs
    fail_count      INTEGER DEFAULT 0,    -- Consecutive failures
    last_error      TEXT,                 -- Last error message if any
    created_at      TEXT NOT NULL,        -- ISO 8601 timestamp
    updated_at      TEXT                  -- ISO 8601 timestamp of last update
);

-- Indexes for schedule queries
CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON schedules(enabled);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run);
CREATE INDEX IF NOT EXISTS idx_schedules_name ON schedules(name);

-- Add updated_at trigger for schedules
CREATE TRIGGER IF NOT EXISTS update_schedules_updated_at
AFTER UPDATE ON schedules
BEGIN
    UPDATE schedules SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
