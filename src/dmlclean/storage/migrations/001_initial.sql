-- Migration 001: Initial schema
-- Creates core tables for history, manifests, and disk trends

-- Cleaning History Table
-- Tracks all cleaning operations with statistics
CREATE TABLE IF NOT EXISTS history (
    id              TEXT PRIMARY KEY,     -- UUID
    timestamp       TEXT NOT NULL,        -- ISO 8601 timestamp
    mode            TEXT NOT NULL,        -- dry-run | trash | permanent
    profile         TEXT,                 -- developer | designer | system-admin | custom
    scan_mode       TEXT NOT NULL,        -- fast | deep | custom
    files_found     INTEGER DEFAULT 0,
    files_deleted   INTEGER DEFAULT 0,
    size_bytes      INTEGER DEFAULT 0,
    duration_ms     INTEGER DEFAULT 0,
    categories      TEXT,                 -- JSON array of category names
    status          TEXT DEFAULT 'complete', -- complete | partial | failed
    error_message   TEXT,                 -- Error details if status = failed
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Deletion Manifest Index Table
-- Indexes manifest files stored in history/manifests/ directory
CREATE TABLE IF NOT EXISTS manifests (
    id              TEXT PRIMARY KEY,     -- matches history.id
    manifest_path   TEXT NOT NULL,        -- path to JSON manifest file
    created_at      TEXT NOT NULL,        -- ISO 8601 timestamp
    file_count      INTEGER DEFAULT 0,
    size_bytes      INTEGER DEFAULT 0,
    undone          INTEGER DEFAULT 0,    -- 0=false, 1=true
    undone_at       TEXT,                 -- ISO 8601 timestamp of undo
    notes           TEXT
);

-- Disk Usage Trend Table
-- Tracks disk usage over time for trend analysis
CREATE TABLE IF NOT EXISTS disk_trend (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL,        -- ISO 8601 timestamp
    mount_point     TEXT NOT NULL,        -- e.g., "C:\", "/", "/home"
    total_bytes     INTEGER,
    free_bytes      INTEGER,
    used_bytes      INTEGER,
    percent_used    REAL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp);
CREATE INDEX IF NOT EXISTS idx_history_status ON history(status);
CREATE INDEX IF NOT EXISTS idx_history_profile ON history(profile);
CREATE INDEX IF NOT EXISTS idx_manifests_created_at ON manifests(created_at);
CREATE INDEX IF NOT EXISTS idx_disk_trend_timestamp ON disk_trend(timestamp);
CREATE INDEX IF NOT EXISTS idx_disk_trend_mount_point ON disk_trend(mount_point);
