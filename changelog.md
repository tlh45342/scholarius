# Scholarius Changelog

## 0.0.9

### SSL startup restoration

- Restored self-signed HTTPS startup without reintroducing `start.sh`.
- Added `app/serve.py` as the container's long-running Uvicorn launcher.
- Reuses `app/cert.pem` and `app/key.pem` when present.
- Generates a replacement certificate with OpenSSL when either file is absent.
- Added the `SCHOLARIUS_SSL_HOST` environment setting for the certificate IP.


## Question-bank authoring

Scholarius now supports a complete first authoring loop:

- create a new QTI/XML question bank;
- open an installed bank in the bank editor;
- add single-answer multiple-choice questions;
- assign optional domain and objective metadata;
- delete an existing question with confirmation;
- export the bank's current QTI/XML file.

Newly created and imported banks use the same editor and export path. The XML
file remains the authoritative bank representation for this release, while
SQLite stores the bank catalog and user history.

## Question Bank Management

- **List** shows installed banks.
- **Import** retains the existing QTI upload workflow.
- **Export** now provides real downloads.
- **Create** now creates a usable bank rather than a placeholder.
- **Edit** now opens a bank and manages its questions.

## Scope and safeguards

The first editor intentionally supports the question type already understood
by Scholarius: single-answer multiple choice, including two-choice true/false
questions. Stable bank and question identifiers are validated. Duplicate
identifiers are rejected, and XML writes use a temporary file before replacing
the current bank.

Scholarius remains a work in progress and is not production-ready.

## 0.0.8

## Theme preference

- Adds Light, Dark, and Follow System choices.
- Stores the preference with the user account.
- Applies the selected theme across rendered pages.
- Uses shared CSS variables so future pages can inherit theme behavior.

## UX cleanup

- Home-screen actions now use consistent blue primary buttons.
- Question Bank Management actions now use consistent blue buttons.
- Removes textual Home links from quiz cards.
- Retains explicit question-marking behavior.
- Repairs the Question Bank List route by reading installed banks from SQLite.

## Accessibility foundation

- Adds keyboard-visible focus indicators.
- Respects reduced-motion preferences.
- Uses theme-aware contrast variables.
- Keeps accessible labels on icon controls.
- Documents accessibility intent and work-in-progress status in README.md.

Scholarius remains under active development and is not production-ready.

## 0.0.7

## Question Bank Management

The Question Bank Management card is now a simple task launcher:

- List
- Import
- Export
- Create
- Edit

This keeps the management card focused on choosing a task rather than
combining several workflows on one screen.

### Working pages

- **List** shows the installed question banks.
- **Import** retains the existing QTI XML upload and validation workflow.

### Reserved workspaces

Export, Create, and Edit now open focused placeholder cards. These cards make
the intended navigation visible without pretending that unfinished functions
are already operational.

## History navigation

The View History card now uses the standard lower-left Home icon. The older
text Home link has been removed.

## Version

Scholarius is now version `0.0.7`.


## Final visual tuning

- The blue page gradient has been darkened slightly while preserving the
  existing restrained appearance.
- The lower-left **version stamp** has slightly stronger contrast and weight.
  It remains secondary interface metadata rather than a prominent control.

## 0.0.6

## Progressive account help

The login card keeps **Create Account** as a full secondary action, but no
longer carries its explanatory sentence all the time.

When the user hovers over the button or reaches it with the keyboard, a
tooltip explains:

> Create a user account to save quiz history, marked questions, and
> preferences.

This is an example of **progressive disclosure**: keep the primary interface
quiet, then reveal supporting information when the user shows interest in
the action.

## Accessibility details

- The button uses `aria-describedby` to associate it with the explanation.
- The explanation appears for both mouse hover and keyboard focus.
- The tooltip is supporting information rather than a requirement, so the
  Create Account action remains understandable even when hover is unavailable.
- Reduced-motion preferences are respected.

## Version

Scholarius is now version `0.0.6`.

## 0.0.5

## First-run experience

- Adds a Welcome to Scholarius card before administrator creation.
- Explains what Scholarius is and what the setup process will do.
- Moves administrator creation to `/setup/admin`.
- The welcome card appears only while no user accounts exist.

## Card navigation

- Adds a discreet Home or Back icon in the lower-left of focused task cards.
- Keeps the global lower-left utility navigation for Home, Profile, and Admin.
- Retains the quiet version indicator outside the cards.

## Question bank management

- Simplifies `/qb-manage` into an installed-question-bank list.
- Moves QTI upload and validation controls to `/qb-manage/import`.
- Adds an Import Question Bank button to the management card.
- Import errors return to the dedicated import page.
- Successful imports return to the installed-bank list.

## Account UX retained

- Create Account remains a full secondary button on the login card.
- The login card explains that user accounts preserve history,
  marked questions, and preferences.
- The home card does not display the signed-in username.

## 0.0.4

This test installment adds:

- first-run administrator creation at `/setup`;
- PBKDF2-SHA256 password hashing using the Python standard library;
- real username/password verification;
- normal self-service profile creation at `/register`;
- `admin` and `user` roles;
- admin-only Question Bank Management and Administration pages;
- editable display name, light/dark preference, and password on `/profile`;
- logout support;
- automatic upgrade of old plaintext development passwords after a successful login.

## Important migration behavior

An existing `users` table is upgraded in place. Existing development accounts with plaintext passwords can log in once using their current password; Scholarius then replaces that value with a secure hash.

If there are no users, opening `/` redirects to `/setup` to create the first administrator.

## 0.0.3

Adds persistent attempt and answer history.

- Records each completed attempt.
- Records every selected and correct answer.
- Stores domain and objective metadata with each answer.
- Adds Mark for Review on the question page.
- Shows recent attempts and aggregate domain performance.
- Migrates an existing SQLite database in place.

Replace the included files, rebuild, complete a quiz, then open `/history`.

## 0.0.10 - QTI-native editor consolidation

- Removed the abandoned SQL-first question-bank editor branch and its duplicate templates and schema notes.
- Unified question-bank management around the authoritative QTI XML file.
- Added direct question editing for prompt, choices, correct answer, domain, objective, and status.
- Added active/retired question status; retired questions remain in XML but are excluded from quizzes and tests.
- Added safe XML writes using a temporary file, parse validation, atomic replacement, and a `.bak` backup.
- Kept SQLite limited to catalogue, users, attempts, scores, and history.
