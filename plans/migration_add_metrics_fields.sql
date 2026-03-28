-- Migration: Add new metrics fields to Phase and Execution tables
-- Date: 2026-03-28
-- Description: Add cache_read_tokens, cache_write_tokens, cache_hit_percent, latency, model_name to Execution; change cache_hit to float in Phase

-- Step 1: Change cache_hit in Phase from INTEGER to REAL (float)
ALTER TABLE phase RENAME TO phase_old;

CREATE TABLE phase (
    id INTEGER NOT NULL,
    mission VARCHAR NOT NULL,
    project_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    user_id INTEGER,
    skill VARCHAR,
    status VARCHAR NOT NULL,
    logging VARCHAR,
    token_in INTEGER NOT NULL,
    token_out INTEGER NOT NULL,
    cache_hit REAL NOT NULL DEFAULT 0.0,
    reasoning INTEGER NOT NULL,
    "order" INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(project_id) REFERENCES project (id),
    FOREIGN KEY(role_id) REFERENCES role (id),
    FOREIGN KEY(user_id) REFERENCES user (id)
);

-- Copy data from old table
INSERT INTO phase (id, mission, project_id, role_id, user_id, skill, status, logging, token_in, token_out, cache_hit, reasoning, "order", created_at, updated_at)
SELECT id, mission, project_id, role_id, user_id, skill, status, logging, token_in, token_out, CAST(cache_hit AS REAL), reasoning, "order", created_at, updated_at
FROM phase_old;

DROP TABLE phase_old;

-- Step 2: Add new columns to Execution table
ALTER TABLE execution ADD COLUMN cache_read_tokens INTEGER DEFAULT 0;
ALTER TABLE execution ADD COLUMN cache_write_tokens INTEGER DEFAULT 0;
ALTER TABLE execution ADD COLUMN cache_hit_percent REAL DEFAULT 0.0;
ALTER TABLE execution ADD COLUMN latency REAL DEFAULT 0.0;
ALTER TABLE execution ADD COLUMN model_name VARCHAR;