CREATE TABLE IF NOT EXISTS weekly_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_number INTEGER NOT NULL UNIQUE,
    title TEXT,
    instructions TEXT,
    presentation_requirements TEXT,
    start_on TEXT,
    due_on TEXT,
    is_open INTEGER NOT NULL DEFAULT 1,
    notify_students INTEGER NOT NULL DEFAULT 1,
    updated_by INTEGER,
    updated_at TEXT,
    FOREIGN KEY(updated_by) REFERENCES users(id)
);
