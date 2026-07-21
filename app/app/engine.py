class QuizEngine:
    def __init__(self, questions):
        self.questions = questions
        self.answers = {}
        self.marked = set()

    def answer(self, qid, choice, marked=False):
        self.answers[qid] = choice
        if marked: self.marked.add(qid)
        else: self.marked.discard(qid)

    def score(self):
        return sum(1 for q in self.questions if self.answers.get(q.qid) == q.correct)

    def answer_rows(self):
        rows=[]
        for q in self.questions:
            selected=self.answers.get(q.qid)
            rows.append({
                "question_id": q.qid, "domain": q.domain, "objective": q.objective,
                "selected_answer": selected, "correct_answer": q.correct,
                "was_correct": selected == q.correct, "marked_for_review": q.qid in self.marked,
            })
        return rows
