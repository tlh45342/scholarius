-- Question Bank Management Schema Extension
-- Add these tables to scholarius.db to enable the editor

-- Store imported question banks
CREATE TABLE IF NOT EXISTS question_banks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    question_count INTEGER DEFAULT 0
);

-- Store individual questions with full metadata
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id TEXT NOT NULL,
    qid TEXT NOT NULL,
    prompt TEXT NOT NULL,
    question_type TEXT DEFAULT 'single-choice',
    correct_answer TEXT,
    explanation TEXT,
    domain TEXT,
    objective TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(bank_id) REFERENCES question_banks(bank_id) ON DELETE CASCADE,
    UNIQUE(bank_id, qid)
);

-- Store answer choices for questions
CREATE TABLE IF NOT EXISTS question_choices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    identifier TEXT NOT NULL,
    choice_text TEXT NOT NULL,
    position INTEGER DEFAULT 0,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- Store domains and objectives for organizational purposes
CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id TEXT NOT NULL,
    domain_id TEXT UNIQUE NOT NULL,
    domain_name TEXT NOT NULL,
    FOREIGN KEY(bank_id) REFERENCES question_banks(bank_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS objectives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id TEXT NOT NULL,
    objective_id TEXT UNIQUE NOT NULL,
    objective_name TEXT NOT NULL,
    FOREIGN KEY(domain_id) REFERENCES domains(domain_id) ON DELETE CASCADE
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_questions_bank_id ON questions(bank_id);
CREATE INDEX IF NOT EXISTS idx_questions_domain ON questions(domain);
CREATE INDEX IF NOT EXISTS idx_questions_objective ON questions(objective);
CREATE INDEX IF NOT EXISTS idx_question_choices_question_id ON question_choices(question_id);
CREATE INDEX IF NOT EXISTS idx_domains_bank_id ON domains(bank_id);
CREATE INDEX IF NOT EXISTS idx_objectives_domain_id ON objectives(domain_id);
