from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union


@dataclass
class Question:
    """
    Represents a single question with support for:
    - Single-choice (1 correct answer)
    - Multiple-choice (2+ correct answers)
    - True/False
    - Matching
    - Order Selection
    """
    qid: str
    prompt: str
    choices: Dict[str, str]  # {"A": "text", "B": "text", ...}
    correct: Optional[str] = None  # For single-choice: "A"
    correct_answers: Optional[List[str]] = None  # For multi-choice: ["A", "B"]
    domain: Optional[str] = None
    objective: Optional[str] = None
    question_type: str = "single-choice"  # single-choice, multiple-choice, true-false, matching, order-select
    explanation: Optional[str] = None
    
    def is_multichoice(self) -> bool:
        """Check if this is a multiple-choice question (select 2+)."""
        return self.question_type == "multiple-choice"
    
    def get_correct_answers(self) -> List[str]:
        """Get correct answer(s) as a list."""
        if self.is_multichoice() and self.correct_answers:
            return self.correct_answers
        elif self.correct:
            return [self.correct]
        return []


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
