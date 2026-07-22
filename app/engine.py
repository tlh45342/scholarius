class QuizEngine:
    def __init__(self, questions):
        self.questions = questions
        self.answers = {}
        self.marked = set()

    @staticmethod
    def _normalize(value):
        if value is None:
            return tuple()
        if isinstance(value, (list, tuple, set)):
            return tuple(sorted(str(item) for item in value if str(item)))
        return (str(value),)

    def answer(self, qid, choice, marked=False):
        self.answers[qid] = list(choice) if isinstance(choice, (list, tuple, set)) else choice
        if marked:
            self.marked.add(qid)
        else:
            self.marked.discard(qid)

    def is_correct(self, question):
        selected = self._normalize(self.answers.get(question.qid))
        expected = self._normalize(question.correct_answers or question.correct)
        return selected == expected

    def score(self):
        return sum(1 for question in self.questions if self.is_correct(question))

    def answer_rows(self):
        rows = []
        for question in self.questions:
            selected = self.answers.get(question.qid)
            selected_values = self._normalize(selected)
            correct_values = self._normalize(question.correct_answers or question.correct)
            rows.append({
                "question_id": question.qid,
                "domain": question.domain,
                "objective": question.objective,
                "selected_answer": ",".join(selected_values),
                "correct_answer": ",".join(correct_values),
                "was_correct": selected_values == correct_values,
                "marked_for_review": question.qid in self.marked,
            })
        return rows
