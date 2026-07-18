import xml.etree.ElementTree as ET
from app.models import Question


def strip_ns(tag):
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def extract_text(elem):
    return " ".join(part.strip() for part in elem.itertext() if part.strip())


def load_qti(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    questions = []

    for item in (elem for elem in root.iter() if strip_ns(elem.tag) == "assessmentItem"):
        qid = item.attrib.get("identifier", "unknown")

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

        questions.append(
            Question(
                qid=qid,
                prompt=prompt,
                choices=choices,
                correct=correct,
            )
        )

    return questions
