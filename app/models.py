from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Question:
    qid: str
    prompt: str
    choices: Dict[str, str]
    correct: Optional[str] = None
    correct_answers: List[str] = field(default_factory=list)
    domain: Optional[str] = None
    objective: Optional[str] = None
    question_type: str = "single-choice"
    status: str = "active"
    explanation: str = ""

    def __post_init__(self):
        if self.correct_answers:
            self.correct_answers = list(dict.fromkeys(self.correct_answers))
            self.correct = self.correct_answers[0]
        elif self.correct:
            self.correct_answers = [self.correct]


@dataclass
class BlueprintDomain:
    domain_id: str
    name: str
    min_percent: float
    max_percent: float
    target_percent: float


@dataclass
class ExamBlueprint:
    selection_mode: str = "weighted-random"
    rounding_method: str = "largest-remainder"
    insufficient_question_policy: str = "warn"
    default_question_count: Optional[int] = None
    domains: List[BlueprintDomain] = field(default_factory=list)


@dataclass
class QuestionBank:
    identifier: str
    title: str
    questions: List[Question]
    metadata: Dict[str, str] = field(default_factory=dict)
    blueprint: Optional[ExamBlueprint] = None
