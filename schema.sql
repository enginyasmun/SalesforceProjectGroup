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
    avatar_filename TEXT,
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
    project_step_number INTEGER,
    project_evidence_url TEXT,
    project_file_name TEXT,
    presentation_title TEXT,
    presentation_summary TEXT,
    presentation_link TEXT,
    presentation_file_name TEXT,
    project_review_status TEXT NOT NULL DEFAULT 'pending',
    presentation_review_status TEXT NOT NULL DEFAULT 'pending',
    project_feedback TEXT,
    presentation_feedback TEXT,
    instructor_feedback TEXT,
    strengths TEXT,
    revision_actions TEXT,
    score_business REAL,
    score_evidence REAL,
    score_salesforce REAL,
    score_communication REAL,
    score_professionalism REAL,
    total_score REAL,
    submitted_at TEXT,
    revision_number INTEGER NOT NULL DEFAULT 0,
    reviewed_by INTEGER,
    reviewed_at TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE(student_id,week_number),
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(reviewed_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    short_name TEXT,
    summary TEXT NOT NULL,
    business_problem TEXT,
    users TEXT,
    objects TEXT,
    outcomes TEXT,
    source_filename TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    step_number INTEGER NOT NULL,
    phase TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    tasks TEXT,
    deliverables TEXT,
    source_reference TEXT,
    is_published INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id,step_number),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS student_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL UNIQUE,
    project_id INTEGER NOT NULL,
    current_step INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('not_started','active','blocked','completed')),
    instructor_note TEXT,
    started_at TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS student_certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    certification_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started' CHECK(status IN ('not_started','studying','scheduled','passed')),
    target_date TEXT,
    notes TEXT,
    verified_by INTEGER,
    verified_at TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE(student_id,certification_id),
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(certification_id) REFERENCES certifications(id),
    FOREIGN KEY(verified_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS homework_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    instructions TEXT NOT NULL,
    presentation_requirements TEXT,
    due_date TEXT,
    example_url TEXT,
    example_file_name TEXT,
    created_by INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS homework_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'assigned' CHECK(status IN ('assigned','submitted','under_review','revision','approved')),
    presentation_title TEXT,
    submission_notes TEXT,
    presentation_url TEXT,
    file_name TEXT,
    score REAL,
    instructor_comment TEXT,
    assigned_at TEXT NOT NULL,
    submitted_at TEXT,
    reviewed_by INTEGER,
    reviewed_at TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE(request_id,student_id),
    FOREIGN KEY(request_id) REFERENCES homework_requests(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(reviewed_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    kind TEXT NOT NULL DEFAULT 'general',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    link_url TEXT,
    is_read INTEGER NOT NULL DEFAULT 0,
    email_status TEXT NOT NULL DEFAULT 'not_configured',
    email_error TEXT,
    emailed_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_instructor ON users(selected_instructor_id);
CREATE INDEX IF NOT EXISTS idx_users_approval ON users(approval_status);
CREATE INDEX IF NOT EXISTS idx_submissions_student ON submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_steps_project ON project_steps(project_id,step_number);
CREATE INDEX IF NOT EXISTS idx_student_projects_project ON student_projects(project_id);
CREATE INDEX IF NOT EXISTS idx_student_certs_student ON student_certifications(student_id);
CREATE INDEX IF NOT EXISTS idx_homework_student ON homework_assignments(student_id,status);
CREATE INDEX IF NOT EXISTS idx_homework_request ON homework_assignments(request_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id,is_read,created_at);
