import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "scholarius.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
    cur.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, theme TEXT DEFAULT 'light')""")
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
    conn.commit(); conn.close()
