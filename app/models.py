from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Question:
    qid: str
    prompt: str
    choices: Dict[str, str]
    correct: Optional[str] = None
    domain: Optional[str] = None
    objective: Optional[str] = None
    question_type: str = "single-choice"
    status: str = "active"


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
