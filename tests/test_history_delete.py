import sqlite3
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import app.main as main

with tempfile.TemporaryDirectory() as tmp:
    db = Path(tmp) / "test.db"
    def connect():
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    conn = connect()
    conn.executescript("""
    CREATE TABLE quizzes(id TEXT PRIMARY KEY,title TEXT);
    CREATE TABLE attempts(id INTEGER PRIMARY KEY,username TEXT,quiz_id TEXT,mode TEXT,score INTEGER,question_count INTEGER,completed_at TEXT,timestamp TEXT);
    CREATE TABLE attempt_answers(id INTEGER PRIMARY KEY,attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,username TEXT,domain TEXT,was_correct INTEGER,marked_for_review INTEGER);
    INSERT INTO quizzes VALUES('q','Example');
    INSERT INTO attempts VALUES(1,'alice','q','quiz',1,1,'now','now');
    INSERT INTO attempts VALUES(2,'alice','q','quiz',1,1,'now','now');
    INSERT INTO attempts VALUES(3,'bob','q','quiz',1,1,'now','now');
    INSERT INTO attempt_answers VALUES(1,1,'alice','D',1,0);
    INSERT INTO attempt_answers VALUES(2,2,'alice','D',1,0);
    INSERT INTO attempt_answers VALUES(3,3,'bob','D',1,0);
    """)
    conn.commit()
    conn.close()
    main.get_conn = connect
    main.SESSIONS['test-alice'] = {'username':'alice','role':'user'}
    client = TestClient(main.app)
    client.cookies.set('token','test-alice')
    page = client.get('/history')
    assert page.status_code == 200, page.text
    assert 'history-attempt-row' in page.text
    assert 'Delete selected attempt' in page.text
    response = client.post('/history/attempt/3/delete',follow_redirects=False)
    assert response.status_code == 303
    conn = connect()
    assert conn.execute('SELECT COUNT(*) FROM attempts').fetchone()[0] == 3
    conn.close()
    response = client.post('/history/attempt/1/delete',follow_redirects=False)
    assert response.status_code == 303 and response.headers['location'] == '/history'
    conn = connect()
    assert [r[0] for r in conn.execute('SELECT id FROM attempts ORDER BY id')] == [2,3]
    assert [r[0] for r in conn.execute('SELECT id FROM attempt_answers ORDER BY id')] == [2,3]
    conn.close()
    page = client.get('/history')
    assert '1</strong><span>Answers' in page.text, page.text[:1000]
    anonymous = TestClient(main.app)
    assert anonymous.post('/history/attempt/2/delete',follow_redirects=False).status_code == 303
    print('PASS: selection markup, authorization, cascade, isolation, refreshed statistics, login guard')
