# Scholarius Changelog

## 0.0.12 — 2026-07-21

### Question-bank management

- Added **Open**, **Export**, and **Delete** controls directly to the installed-bank list.
- Bank deletion now removes the registry entry, authoritative XML file, and its editor backup after explicit confirmation.
- Kept one authoritative bank identifier while presenting the title as the human-readable name.

### Question editor

- Enlarged the question and explanation editing areas.
- Added explanation authoring for new and existing questions.
- Stored explanations as XML metadata and restored them when a bank is loaded.
- Improved form spacing and editor action alignment.
- Retained the black **Retired** label; retired questions remain editable but are excluded from quiz/test selection.

### Interface and documentation

- Darkened the universal Home/navigation controls for stronger visual presence.
- Updated the project overview, Docker instructions, XML/SQLite ownership model, project status, and licensing status.
- Bumped the application version to 0.0.12.

## 0.0.10 and earlier

Earlier work established self-signed HTTPS startup, profiles and themes, quiz/test history, QTI/XML import and export, question-bank creation, XML-safe question editing, question add/delete, and the first question-bank management interface.
