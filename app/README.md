# Scholarius


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

## Question-bank authoring status

As of version 0.0.9, administrators can create a bank, add and delete
single-answer multiple-choice questions, and export the current bank as
QTI/XML. The XML file is the authoritative question-bank representation for
this stage of development. More advanced editing, additional question types,
and recovery/version-history features remain future work.

## Repository organization

Scholarius uses a deliberately small and predictable repository layout:

```text
README.md
changelog.md
docs/
app/
Dockerfile
compose.yaml
requirements.txt
```

- `README.md` introduces the project and its current status.
- `changelog.md` contains the complete release history in one file.
- `docs/` contains design notes and supporting project documentation.
- `app/` contains the Scholarius application.

Version-specific `UPDATE-x.x.x.md` files are no longer used. New release
information is added to `changelog.md`.

The distributed project does not currently include a `tests/` directory.
Development validation may still be performed while preparing a release, but
those temporary checks are not part of the end-user package. A formal test
suite can be restored later if the project requires one.

## Question-bank ownership

Scholarius treats each QTI XML file as the authoritative question bank. Question text, answers, metadata, and active/retired status are edited in the XML file itself. SQLite is used for users, the installed-bank catalogue, attempts, scores, and history; it is not the master copy of question content.

Question-bank saves are written to a temporary file, parsed for validity, backed up to `<bank>.xml.bak`, and then atomically replace the original XML file.
