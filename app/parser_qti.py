"""
Extended QTI Parser with Multi-Choice Support
Parses QTI XML and stores questions in SQLite for editing
Supports single-choice, multiple-choice (2+), and other types
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from app.models import (
    BlueprintDomain,
    ExamBlueprint,
    Question,
    QuestionBank,
)
from app.db import get_conn


def strip_ns(tag: str) -> str:
    """Remove XML namespace from tag."""
    return tag.split("}", 1)[1] if "}" in tag else tag


def extract_text(elem) -> str:
    """Extract all text from an element and its children."""
    return " ".join(part.strip() for part in elem.itertext() if part.strip())


def _metadata_fields(parent) -> Dict[str, str]:
    """Extract QTI metadata fields into a dictionary."""
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
    """Convert string to int safely."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Optional[str], default: float = 0.0) -> float:
    """Convert string to float safely."""
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _parse_blueprint(root, metadata: Dict[str, str]) -> Optional[ExamBlueprint]:
    """Parse exam blueprint from QTI root."""
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


def _detect_question_type(prompt: str, cardinality: str) -> str:
    """
    Detect question type based on prompt text and QTI cardinality.
    """
    prompt_lower = prompt.lower()
    
    # Check for multi-choice indicators
    if cardinality == "multiple":
        return "multiple-choice"
    if "select" in prompt_lower and ("two" in prompt_lower or "2" in prompt_lower):
        return "multiple-choice"
    if "each correct answer" in prompt_lower:
        return "multiple-choice"
    if "which two" in prompt_lower or "which 3" in prompt_lower or "which 4" in prompt_lower:
        return "multiple-choice"
    
    # Check for true/false
    if "true or false" in prompt_lower or "true/false" in prompt_lower:
        return "true-false"
    
    # Default
    return "single-choice"


def load_qti_bank(file_path) -> QuestionBank:
    """Load QTI bank from XML file with multi-choice support."""
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
        correct_answers = None
        explanation = ""
        cardinality = "single"

        for elem in item.iter():
            tag = strip_ns(elem.tag)
            
            # Get response cardinality (single vs multiple)
            if tag == "responseDeclaration":
                cardinality = elem.attrib.get("cardinality", "single")
            
            # Extract correct response(s)
            elif tag == "correctResponse":
                correct_values = []
                for child in elem.iter():
                    if strip_ns(child.tag) == "value" and child.text:
                        correct_values.append(child.text.strip())
                
                if len(correct_values) > 1:
                    correct_answers = correct_values
                    correct = None
                elif correct_values:
                    correct = correct_values[0]
                    correct_answers = None
            
            elif tag == "prompt":
                prompt = extract_text(elem)
            
            elif tag == "simpleChoice":
                cid = elem.attrib.get("identifier")
                if cid:
                    choices[cid] = extract_text(elem)
            
            elif tag == "feedbackBlock":
                # Capture explanation if present
                explanation = extract_text(elem)

        # Validate question
        if not prompt or len(choices) < 2:
            continue
        
        # Ensure correct answer(s) are valid
        if correct_answers:
            # Multi-choice: verify all are in choices
            if not all(c in choices for c in correct_answers):
                continue
        elif correct:
            # Single-choice: verify it's in choices
            if correct not in choices:
                continue
        else:
            # No correct answer found
            continue

        # Detect question type
        question_type = item_metadata.get("question_type", 
                                         _detect_question_type(prompt, cardinality))

        questions.append(
            Question(
                qid=qid,
                prompt=prompt,
                choices=choices,
                correct=correct,
                correct_answers=correct_answers,
                domain=item_metadata.get("domain"),
                objective=item_metadata.get("objective"),
                question_type=question_type,
                explanation=explanation if explanation else None,
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


def store_question_bank_to_db(bank: QuestionBank, filename: str = ""):
    """Refresh the SQLite editing index from an authoritative XML bank."""
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    try:
        cur.execute(
            """INSERT INTO question_banks (bank_id, title, filename, imported_at, question_count)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(bank_id) DO UPDATE SET
                   title=excluded.title,
                   filename=excluded.filename,
                   imported_at=excluded.imported_at,
                   question_count=excluded.question_count""",
            (bank.identifier, bank.title, filename, now, len(bank.questions)),
        )
        # The index is rebuilt as a unit so removed or renamed XML items do not
        # linger in SQLite.
        cur.execute("DELETE FROM questions WHERE bank_id=?", (bank.identifier,))
        cur.execute("DELETE FROM domains WHERE bank_id=?", (bank.identifier,))

        domains_seen = set()
        objectives_seen = set()
        for question in bank.questions:
            if question.domain and question.domain not in domains_seen:
                cur.execute(
                    "INSERT OR IGNORE INTO domains (bank_id, domain_id, domain_name) VALUES (?, ?, ?)",
                    (bank.identifier, question.domain, question.domain),
                )
                domains_seen.add(question.domain)
            if question.objective and question.domain:
                objective_key = (question.domain, question.objective)
                if objective_key not in objectives_seen:
                    cur.execute(
                        "INSERT OR IGNORE INTO objectives (domain_id, objective_id, objective_name) VALUES (?, ?, ?)",
                        (question.domain, f"{question.domain}:{question.objective}", question.objective),
                    )
                    objectives_seen.add(objective_key)

            import json
            correct_answers_json = json.dumps(question.correct_answers) if question.correct_answers else None
            cur.execute(
                """INSERT INTO questions
                   (bank_id, qid, prompt, question_type, correct_answer, correct_answers,
                    explanation, domain, objective, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    bank.identifier, question.qid, question.prompt, question.question_type,
                    question.correct, correct_answers_json, question.explanation,
                    question.domain, question.objective, now, now,
                ),
            )
            question_id = cur.lastrowid
            for position, (choice_key, choice_text) in enumerate(question.choices.items()):
                cur.execute(
                    """INSERT INTO question_choices
                       (question_id, identifier, choice_text, position)
                       VALUES (?, ?, ?, ?)""",
                    (question_id, choice_key, choice_text, position),
                )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_questions_by_bank(bank_id: str) -> list:
    """Retrieve all questions from a specific question bank."""
    conn = get_conn()
    cur = conn.cursor()
    import json

    questions = []
    rows = cur.execute(
        """
        SELECT id, qid, prompt, question_type, correct_answer, correct_answers, 
               explanation, domain, objective
        FROM questions
        WHERE bank_id = ?
        ORDER BY id
        """,
        (bank_id,)
    ).fetchall()

    for row in rows:
        question_id = row[0]
        
        # Get choices for this question
        choices_rows = cur.execute(
            """
            SELECT identifier, choice_text
            FROM question_choices
            WHERE question_id = ?
            ORDER BY position
            """,
            (question_id,)
        ).fetchall()

        choices = {ch[0]: ch[1] for ch in choices_rows}
        
        # Parse correct_answers if it's JSON
        correct_answers = None
        if row[5]:  # correct_answers column
            try:
                correct_answers = json.loads(row[5])
            except:
                correct_answers = None

        questions.append({
            'id': question_id,
            'qid': row[1],
            'bank_id': bank_id,
            'prompt': row[2],
            'question_type': row[3],
            'correct_answer': row[4],
            'correct_answers': correct_answers,
            'explanation': row[6],
            'domain': row[7],
            'objective': row[8],
            'choices': choices,
        })

    conn.close()
    return questions


def get_question_by_id(question_id: int) -> dict:
    """Retrieve a single question by ID."""
    conn = get_conn()
    cur = conn.cursor()
    import json

    row = cur.execute(
        """
        SELECT id, qid, bank_id, prompt, question_type, correct_answer, correct_answers,
               explanation, domain, objective
        FROM questions
        WHERE id = ?
        """,
        (question_id,)
    ).fetchone()

    if not row:
        conn.close()
        return None

    # Get choices
    choices_rows = cur.execute(
        """
        SELECT identifier, choice_text
        FROM question_choices
        WHERE question_id = ?
        ORDER BY position
        """,
        (question_id,)
    ).fetchall()

    conn.close()
    
    # Parse correct_answers if it's JSON
    correct_answers = None
    if row[6]:  # correct_answers column
        try:
            correct_answers = json.loads(row[6])
        except:
            correct_answers = None

    return {
        'id': row[0],
        'qid': row[1],
        'bank_id': row[2],
        'prompt': row[3],
        'question_type': row[4],
        'correct_answer': row[5],
        'correct_answers': correct_answers,
        'explanation': row[7],
        'domain': row[8],
        'objective': row[9],
        'choices': {ch[0]: ch[1] for ch in choices_rows},
    }



def _first_descendant(parent, name: str):
    return next((elem for elem in parent.iter() if strip_ns(elem.tag) == name), None)


def _set_metadata_field(item, label: str, value: str):
    """Set or create a lightweight QTI metadata field without discarding unknown XML."""
    for field in (elem for elem in item.iter() if strip_ns(elem.tag) == "qtiMetadataField"):
        field_label = _first_descendant(field, "fieldLabel")
        if field_label is not None and (field_label.text or "").strip() == label:
            entry = _first_descendant(field, "fieldEntry")
            if entry is None:
                entry = ET.SubElement(field, "fieldEntry")
            entry.text = value
            return
    metadata = next((child for child in item if strip_ns(child.tag) == "qtiMetadata"), None)
    if metadata is None:
        metadata = ET.Element("qtiMetadata")
        item.insert(0, metadata)
    field = ET.SubElement(metadata, "qtiMetadataField")
    ET.SubElement(field, "fieldLabel").text = label
    ET.SubElement(field, "fieldEntry").text = value


def update_question_in_qti(
    file_path,
    *,
    qid: str,
    prompt: str,
    choices: Dict[str, str],
    correct_answers: List[str],
    question_type: str,
    explanation: str = "",
    domain: str = "",
    objective: str = "",
):
    """Safely update one assessmentItem and atomically replace the XML file."""
    path = Path(file_path)
    tree = ET.parse(path)
    root = tree.getroot()
    item = next(
        (elem for elem in root.iter()
         if strip_ns(elem.tag) == "assessmentItem" and elem.attrib.get("identifier") == qid),
        None,
    )
    if item is None:
        raise ValueError(f"Question '{qid}' was not found in {path.name}")

    prompt_elem = _first_descendant(item, "prompt")
    if prompt_elem is None:
        raise ValueError(f"Question '{qid}' has no editable prompt")
    prompt_elem.clear()
    prompt_elem.text = prompt

    choice_elems = {
        elem.attrib.get("identifier"): elem
        for elem in item.iter()
        if strip_ns(elem.tag) == "simpleChoice"
    }
    if set(choices) != set(choice_elems):
        raise ValueError("Choice identifiers changed unexpectedly; add/remove choices is not enabled yet")
    for identifier, text in choices.items():
        elem = choice_elems[identifier]
        elem.clear()
        elem.attrib["identifier"] = identifier
        elem.text = text

    declaration = _first_descendant(item, "responseDeclaration")
    if declaration is None:
        raise ValueError(f"Question '{qid}' has no responseDeclaration")
    declaration.attrib["cardinality"] = "multiple" if question_type == "multiple-choice" else "single"
    correct_response = _first_descendant(declaration, "correctResponse")
    if correct_response is None:
        correct_response = ET.SubElement(declaration, "correctResponse")
    for child in list(correct_response):
        correct_response.remove(child)
    for answer in correct_answers:
        ET.SubElement(correct_response, "value").text = answer

    interaction = _first_descendant(item, "choiceInteraction")
    if interaction is not None:
        interaction.attrib["maxChoices"] = str(len(correct_answers)) if question_type == "multiple-choice" else "1"

    _set_metadata_field(item, "question_type", question_type)
    _set_metadata_field(item, "domain", domain)
    _set_metadata_field(item, "objective", objective)

    feedback = _first_descendant(item, "feedbackBlock")
    if explanation:
        if feedback is None:
            feedback = ET.SubElement(item, "feedbackBlock", {"outcomeIdentifier": "FEEDBACK", "identifier": "EXPLANATION", "showHide": "show"})
        feedback.clear()
        feedback.attrib.update({"outcomeIdentifier": "FEEDBACK", "identifier": "EXPLANATION", "showHide": "show"})
        feedback.text = explanation
    elif feedback is not None:
        feedback.clear()
        feedback.attrib.update({"outcomeIdentifier": "FEEDBACK", "identifier": "EXPLANATION", "showHide": "show"})

    if hasattr(ET, "indent"):
        ET.indent(tree, space="    ")
    temporary = path.with_suffix(path.suffix + ".tmp")
    tree.write(temporary, encoding="utf-8", xml_declaration=True)
    # Validate the complete edited bank before replacing the known-good XML.
    load_qti_bank(temporary)
    temporary.replace(path)
