CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student','instructor')),
    is_admin INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 0,
    approval_status TEXT NOT NULL DEFAULT 'pending' CHECK(approval_status IN ('pending','approved','rejected')),
    selected_instructor_id INTEGER,
    approved_by INTEGER,
    approved_at TEXT,
    bootcamp_name TEXT,
    graduation_date TEXT,
    linkedin_url TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(selected_instructor_id) REFERENCES users(id),
    FOREIGN KEY(approved_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    week_number INTEGER NOT NULL CHECK(week_number BETWEEN 1 AND 8),
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','submitted','under_review','revision','approved')),
    project_story TEXT,
    requirement_notes TEXT,
    research_notes TEXT,
    design_notes TEXT,
    presentation_url TEXT,
    reflection TEXT,
    file_name TEXT,
    instructor_feedback TEXT,
    reviewed_by INTEGER,
    reviewed_at TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE(student_id,week_number),
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(reviewed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_users_instructor ON users(selected_instructor_id);
CREATE INDEX IF NOT EXISTS idx_users_approval ON users(approval_status);
CREATE INDEX IF NOT EXISTS idx_submissions_student ON submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
