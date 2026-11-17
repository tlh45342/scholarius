"""Standalone integration regression: python tests/test_attempt_review.py"""
import json
import sqlite3
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import app.main as main

with tempfile.TemporaryDirectory() as tmp:
    db = Path(tmp) / "review.db"
    def connect():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        return c
    c = connect()
    c.executescript("""
    CREATE TABLE quizzes(id TEXT PRIMARY KEY,title TEXT,filename TEXT);
    CREATE TABLE attempts(id INTEGER PRIMARY KEY,username TEXT,quiz_id TEXT,mode TEXT,score INTEGER,question_count INTEGER,completed_at TEXT,timestamp TEXT);
    CREATE TABLE attempt_answers(id INTEGER PRIMARY KEY,attempt_id INTEGER REFERENCES attempts(id) ON DELETE CASCADE,username TEXT,domain TEXT,was_correct INTEGER,marked_for_review INTEGER,question_id TEXT,selected_answer TEXT,correct_answer TEXT,question_snapshot TEXT);
    INSERT INTO quizzes VALUES('q','Sample',NULL);
    INSERT INTO attempts VALUES(1,'alice','q','quiz',1,2,'today','today');
    INSERT INTO attempts VALUES(2,'bob','q','quiz',1,1,'today','today');
    """)
    snap = json.dumps({"prompt":"Original question", "choices":{"A":"Wrong","B":"Right"}, "explanation":"Explanation text", "question_type":"single-choice"})
    c.execute("INSERT INTO attempt_answers VALUES(1,1,'alice','Domain',0,0,'Q1','A','B',?)",(snap,))
    c.execute("INSERT INTO attempt_answers VALUES(2,1,'alice','Domain',1,0,'Q2','B','B',?)",(snap,))
    c.execute("INSERT INTO attempt_answers VALUES(3,2,'bob','Domain',1,0,'Q3','B','B',?)",(snap,))
    c.commit();c.close()
    main.get_conn = connect
    main.SESSIONS["review-alice"] = {"username":"alice","role":"user"}
    client = TestClient(main.app)
    client.cookies.set("token","review-alice")
    history = client.get("/history")
    assert history.status_code == 200 and "Review selected attempt" in history.text
    first = client.get("/history/attempt/1")
    assert first.status_code == 200 and "Question 1 of 2" in first.text
    assert "Original question" in first.text and "Explanation text" in first.text
    assert "Your answer" in first.text and "Correct answer" in first.text
    assert "Incorrect" in first.text and "question=2" in first.text
    assert "question=0" not in first.text
    second = client.get("/history/attempt/1?question=2")
    assert "Question 2 of 2" in second.text and "Correct" in second.text
    assert "question=1" in second.text and "question=3" not in second.text
    assert "Question 2 of 2" in client.get("/history/attempt/1?question=999").text
    assert client.get("/history/attempt/2").status_code == 404
    assert TestClient(main.app).get("/history/attempt/1",follow_redirects=False).status_code == 303
    c=connect()
    assert c.execute("SELECT COUNT(*) FROM attempt_answers").fetchone()[0] == 3
    c.close()
    print("PASS: review navigation, snapshots, explanation, correctness, ownership, read-only")
