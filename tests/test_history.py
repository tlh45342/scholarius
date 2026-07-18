from app.engine import QuizEngine
from app.models import Question

def test_answer_rows_include_history_fields():
    q=Question(qid="q1", prompt="p", choices={"A":"a","B":"b"}, correct="A", domain="D", objective="O")
    e=QuizEngine([q]); e.answer("q1","B",marked=True)
    row=e.answer_rows()[0]
    assert row["was_correct"] is False
    assert row["marked_for_review"] is True
