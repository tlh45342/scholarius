class Question:
    def __init__(self, qid, prompt, choices, correct=None):
        self.qid = qid
        self.prompt = prompt
        self.choices = choices
        self.correct = correct
