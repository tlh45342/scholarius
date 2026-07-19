# Scholarius

Scholarius is a lightweight web-based quiz and study system written in Python and packaged as a Docker application.

The goal of Scholarius is to provide an easy-to-deploy quiz platform suitable for classrooms, self-study, certification preparation, and technical training.

---

# Building

Build the image:

```bash
docker build -t scholarius .
```

Verify:

```bash
docker image ls
```

Launch:

```bash
docker compose up -d
```

---

## Accessibility and project status

Scholarius is a work in progress and is **not considered production-ready**.

Accessibility has been considered during the current design work. The project
aims to build practical WCAG 2.2 Level AA fundamentals into the normal
interface rather than requiring users to enable a separate “accessible mode.”

Current considerations include:

- readable light, dark, and system-following themes;
- visible keyboard focus indicators;
- labeled form controls and icon actions;
- keyboard-accessible controls;
- reduced-motion support;
- layouts that tolerate zoom and larger text;
- avoiding reliance on color alone for meaning;
- keeping essential instructions visible rather than hiding them only in
  tooltips.

These measures are a foundation, not a certification or guarantee of full
WCAG conformance. Scholarius has not yet undergone a formal accessibility
audit, assistive-technology test program, or production security review.
Please be patient as the application and its user experience continue to
develop.

---

# License

Private project.

---

# Author

Thomas Hamilton

---

# Question Bank and Assessment Goals

Scholarius treats XML as the authoritative, portable representation of a
question bank. SQLite may be used as a working index for searching and editing,
but changes made through the editor must ultimately be written safely back to
the bank XML before they become authoritative.

A **question bank** is the master collection of reusable questions. One bank
may also define several named **test versions**, such as Practice Test A,
Practice Test B, and Practice Test C. Each test version references questions
from the master bank instead of maintaining duplicate copies of the questions.

Scholarius is intended to support these question types:

1. **True/False** — choose one of two Boolean responses.
2. **Single Choice** — select exactly one answer from a set of choices.
3. **Multiple Response** — select two or more correct answers from a set of
   choices. The required number of selections may be fixed or declared by the
   question.
4. **Matching** — associate each item on the left with an item on the right.
5. **Ordering** — arrange a set of items into the correct sequence.

True/False, Single Choice, and Multiple Response are the initial implementation
priority. Matching and Ordering remain project goals, but their XML model,
editing interface, scoring behavior, keyboard operation, and accessible
non-drag alternatives should be designed before implementation.

See [`docs/QUESTION_BANK_MODEL.md`](docs/QUESTION_BANK_MODEL.md) for the
current terminology and design decisions.
