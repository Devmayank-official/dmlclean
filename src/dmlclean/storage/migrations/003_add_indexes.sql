-- Migration 003: Add additional indexes and optimization
-- Improves query performance for common operations

-- Protected Paths Table
-- Stores user-defined protected paths and glob patterns
CREATE TABLE IF NOT EXISTS protected_paths (
    id              TEXT PRIMARY KEY,     -- UUID
    path            TEXT NOT NULL,        -- Protected path or glob pattern
    description     TEXT,                 -- Human-readable description
    is_glob         INTEGER DEFAULT 0,    -- 0=path, 1=glob pattern
    created_at      TEXT NOT NULL,        -- ISO 8601 timestamp
    updated_at      TEXT                  -- ISO 8601 timestamp of last update
);

-- Index for protected paths queries
CREATE INDEX IF NOT EXISTS idx_protected_paths_path ON protected_paths(path);

-- Composite index for history queries by profile and status
CREATE INDEX IF NOT EXISTS idx_history_profile_status ON history(profile, status);

-- Composite index for history queries by date range and mode
CREATE INDEX IF NOT EXISTS idx_history_mode_timestamp ON history(mode, timestamp);

-- Index for manifest undo queries
CREATE INDEX IF NOT EXISTS idx_manifests_undone ON manifests(undone);

-- Index for schedules by profile
CREATE INDEX IF NOT EXISTS idx_schedules_profile ON schedules(profile);

-- Partial index for active schedules only (for efficient next-run queries)
CREATE INDEX IF NOT EXISTS idx_schedules_active 
ON schedules(next_run, enabled) 
WHERE enabled = 1;

-- Partial index for failed history entries (for error reporting)
CREATE INDEX IF NOT EXISTS idx_history_failed 
ON history(timestamp, error_message) 
WHERE status = 'failed';

-- Vacuum and analyze for optimization
VACUUM;
ANALYZE;
