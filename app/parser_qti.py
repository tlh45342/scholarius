import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional

from app.models import (
    BlueprintDomain,
    ExamBlueprint,
    Question,
    QuestionBank,
)


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def extract_text(elem) -> str:
    return " ".join(part.strip() for part in elem.itertext() if part.strip())


def _metadata_fields(parent) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for field in (elem for elem in parent.iter() if strip_ns(elem.tag) == "qtiMetadataField"):
        label = None
        entry = None
        for child in field:
            tag = strip_ns(child.tag)
            if tag == "fieldLabel":
                label = (child.text or "").strip()
            elif tag == "fieldEntry":
                entry = (child.text or "").strip()
        if label and entry is not None:
            fields[label] = entry
    return fields


def _as_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Optional[str], default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _parse_blueprint(root, metadata: Dict[str, str]) -> Optional[ExamBlueprint]:
    blueprint_elem = next(
        (elem for elem in root.iter() if strip_ns(elem.tag) == "scholariusBlueprint"),
        None,
    )
    if blueprint_elem is None:
        return None

    domains = []
    for elem in blueprint_elem:
        if strip_ns(elem.tag) != "domain":
            continue
        name = (elem.attrib.get("name") or "").strip()
        if not name:
            continue
        domains.append(
            BlueprintDomain(
                domain_id=(elem.attrib.get("id") or name).strip(),
                name=name,
                min_percent=_as_float(elem.attrib.get("min_percent")),
                max_percent=_as_float(elem.attrib.get("max_percent")),
                target_percent=_as_float(elem.attrib.get("target_percent")),
            )
        )

    if not domains:
        return None

    return ExamBlueprint(
        selection_mode=blueprint_elem.attrib.get("selectionMode", "weighted-random"),
        rounding_method=blueprint_elem.attrib.get("roundingMethod", "largest-remainder"),
        insufficient_question_policy=blueprint_elem.attrib.get(
            "insufficientQuestionPolicy", "warn"
        ),
        default_question_count=_as_int(metadata.get("default_test_question_count")),
        domains=domains,
    )


def load_qti_bank(file_path) -> QuestionBank:
    path = Path(file_path)
    tree = ET.parse(path)
    root = tree.getroot()

    if strip_ns(root.tag) != "assessmentTest":
        raise ValueError("QTI root element must be assessmentTest")

    bank_id = (root.attrib.get("identifier") or path.stem).strip()
    title = (root.attrib.get("title") or path.stem).strip()
    metadata = _metadata_fields(root)
    blueprint = _parse_blueprint(root, metadata)

    questions = []
    for item in (elem for elem in root.iter() if strip_ns(elem.tag) == "assessmentItem"):
        qid = item.attrib.get("identifier", "unknown")
        item_metadata = _metadata_fields(item)

        prompt = ""
        choices = {}
        correct = None

        for elem in item.iter():
            tag = strip_ns(elem.tag)
            if tag == "correctResponse":
                for child in elem.iter():
                    if strip_ns(child.tag) == "value" and child.text:
                        correct = child.text.strip()
                        break
            elif tag == "prompt":
                prompt = extract_text(elem)
            elif tag == "simpleChoice":
                cid = elem.attrib.get("identifier")
                if cid:
                    choices[cid] = extract_text(elem)

        if not prompt or len(choices) < 2 or correct not in choices:
            continue

        questions.append(
            Question(
                qid=qid,
                prompt=prompt,
                choices=choices,
                correct=correct,
                domain=item_metadata.get("domain"),
                objective=item_metadata.get("objective"),
                question_type=item_metadata.get("question_type", "single-choice"),
                status=item_metadata.get("status", "active"),
                explanation=item_metadata.get("explanation", ""),
            )
        )

    return QuestionBank(
        identifier=bank_id,
        title=title,
        questions=questions,
        metadata=metadata,
        blueprint=blueprint,
    )


def load_qti(file_path):
    """Backward-compatible helper returning only questions."""
    return load_qti_bank(file_path).questions
