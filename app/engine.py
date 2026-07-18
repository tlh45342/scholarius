class QuizEngine:
    def __init__(self, questions):
        self.questions = questions
        self.answers = {}

    def answer(self, qid, choice):
        self.answers[qid] = choice

    def score(self):
        total = 0

        for q in self.questions:
            user_answer = self.answers.get(q.qid)

            if user_answer == q.correct:
                total += 1

        return total
