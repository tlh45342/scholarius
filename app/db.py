import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "scholarius.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _add_column(conn, table, definition):
    name = definition.split()[0]
    if name not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    
    # Existing user and quiz tables
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            theme TEXT DEFAULT 'light'
        )"""
    )
    for definition in [
        "display_name TEXT",
        "role TEXT NOT NULL DEFAULT 'user'",
        "created_at TEXT",
    ]:
        _add_column(conn, "users", definition)

    cur.execute("""CREATE TABLE IF NOT EXISTS quizzes (id TEXT PRIMARY KEY, title TEXT, filename TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, quiz_id TEXT, timestamp TEXT, answers TEXT, results TEXT)""")
    for definition in [
        "mode TEXT DEFAULT 'quiz'",
        "selection_mode TEXT DEFAULT 'random'",
        "score INTEGER DEFAULT 0",
        "question_count INTEGER DEFAULT 0",
        "completed_at TEXT",
    ]:
        _add_column(conn, "attempts", definition)
    cur.execute("""CREATE TABLE IF NOT EXISTS attempt_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id INTEGER NOT NULL, username TEXT NOT NULL, quiz_id TEXT NOT NULL,
        question_id TEXT NOT NULL, domain TEXT, objective TEXT, selected_answer TEXT, correct_answer TEXT,
        was_correct INTEGER NOT NULL, marked_for_review INTEGER NOT NULL DEFAULT 0, answered_at TEXT NOT NULL,
        FOREIGN KEY(attempt_id) REFERENCES attempts(id) ON DELETE CASCADE)""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_attempt_answers_user_quiz ON attempt_answers(username, quiz_id)""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_attempt_answers_question ON attempt_answers(username, quiz_id, question_id)""")
    
    # NEW: Question Bank Management Tables with Multi-Choice Support
    cur.execute("""CREATE TABLE IF NOT EXISTS question_banks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bank_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        filename TEXT NOT NULL,
        imported_at TEXT NOT NULL,
        question_count INTEGER DEFAULT 0
    )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bank_id TEXT NOT NULL,
        qid TEXT NOT NULL,
        prompt TEXT NOT NULL,
        question_type TEXT DEFAULT 'single-choice',
        correct_answer TEXT,
        correct_answers TEXT,
        explanation TEXT,
        domain TEXT,
        objective TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(bank_id) REFERENCES question_banks(bank_id) ON DELETE CASCADE,
        UNIQUE(bank_id, qid)
    )""")
    
    # Add multi-choice column if it doesn't exist (backward compatibility)
    try:
        _add_column(conn, "questions", "correct_answers TEXT")
    except:
        pass
    
    cur.execute("""CREATE TABLE IF NOT EXISTS question_choices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        identifier TEXT NOT NULL,
        choice_text TEXT NOT NULL,
        position INTEGER DEFAULT 0,
        FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
    )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS domains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bank_id TEXT NOT NULL,
        domain_id TEXT UNIQUE NOT NULL,
        domain_name TEXT NOT NULL,
        FOREIGN KEY(bank_id) REFERENCES question_banks(bank_id) ON DELETE CASCADE
    )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS objectives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain_id TEXT NOT NULL,
        objective_id TEXT UNIQUE NOT NULL,
        objective_name TEXT NOT NULL,
        FOREIGN KEY(domain_id) REFERENCES domains(domain_id) ON DELETE CASCADE
    )""")
    
    # Create indexes for performance
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_questions_bank_id ON questions(bank_id)""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_questions_domain ON questions(domain)""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_questions_objective ON questions(objective)""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_question_choices_question_id ON question_choices(question_id)""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_domains_bank_id ON domains(bank_id)""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_objectives_domain_id ON objectives(domain_id)""")
    
    conn.commit()
    conn.close()
