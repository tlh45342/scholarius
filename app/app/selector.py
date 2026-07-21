import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.models import ExamBlueprint, Question, QuestionBank


@dataclass
class SelectionResult:
    questions: List[Question]
    requested_count: int
    domain_counts: Dict[str, int]
    warnings: List[str]


def largest_remainder_counts(total: int, weights: Dict[str, float]) -> Dict[str, int]:
    if total <= 0:
        raise ValueError("Question count must be greater than zero")
    positive = {name: weight for name, weight in weights.items() if weight > 0}
    if not positive:
        raise ValueError("Blueprint has no positive domain weights")

    weight_sum = sum(positive.values())
    exact = {name: total * weight / weight_sum for name, weight in positive.items()}
    counts = {name: int(value) for name, value in exact.items()}
    remaining = total - sum(counts.values())

    order = sorted(
        exact,
        key=lambda name: (exact[name] - counts[name], positive[name], name),
        reverse=True,
    )
    for name in order[:remaining]:
        counts[name] += 1
    return counts


def _random_selection(questions: List[Question], count: int, rng: random.Random) -> SelectionResult:
    selected = rng.sample(questions, min(count, len(questions)))
    counts: Dict[str, int] = defaultdict(int)
    for question in selected:
        counts[question.domain or "Unclassified"] += 1
    warnings = []
    if count > len(questions):
        warnings.append(
            f"Requested {count} questions, but the bank contains only {len(questions)} supported questions."
        )
    return SelectionResult(selected, count, dict(counts), warnings)


def _weighted_selection(
    questions: List[Question],
    count: int,
    blueprint: ExamBlueprint,
    rng: random.Random,
) -> SelectionResult:
    grouped: Dict[str, List[Question]] = defaultdict(list)
    for question in questions:
        grouped[question.domain or "Unclassified"].append(question)

    weights = {domain.name: domain.target_percent for domain in blueprint.domains}
    desired = largest_remainder_counts(count, weights)
    selected: List[Question] = []
    warnings: List[str] = []
    shortfall = 0

    for domain in blueprint.domains:
        pool = grouped.get(domain.name, [])
        wanted = desired.get(domain.name, 0)
        take = min(wanted, len(pool))
        if take:
            selected.extend(rng.sample(pool, take))
        if take < wanted:
            missing = wanted - take
            shortfall += missing
            warnings.append(
                f"{domain.name} supplied {take} of {wanted} requested questions."
            )

    if shortfall:
        already = {q.qid for q in selected}
        remainder_pool = [q for q in questions if q.qid not in already]
        fill = min(shortfall, len(remainder_pool))
        if fill:
            selected.extend(rng.sample(remainder_pool, fill))
        if fill < shortfall:
            warnings.append(
                f"The bank could not fill {shortfall - fill} requested question slot(s)."
            )

    rng.shuffle(selected)
    actual: Dict[str, int] = defaultdict(int)
    for question in selected:
        actual[question.domain or "Unclassified"] += 1

    return SelectionResult(selected, count, dict(actual), warnings)


def build_test(
    bank: QuestionBank,
    question_count: Optional[int] = None,
    selection_mode: str = "blueprint",
    seed: Optional[int] = None,
) -> SelectionResult:
    if not bank.questions:
        raise ValueError("Question bank contains no supported questions")

    count = question_count or (
        bank.blueprint.default_question_count if bank.blueprint else None
    ) or len(bank.questions)
    if count <= 0:
        raise ValueError("Question count must be greater than zero")

    rng = random.Random(seed)
    if selection_mode == "blueprint" and bank.blueprint:
        return _weighted_selection(bank.questions, count, bank.blueprint, rng)
    return _random_selection(bank.questions, count, rng)
