# Scholarius

Scholarius is a small, flexible, self-hosted quiz and test application. It is intended for people who want focused question-bank authoring and realistic practice tests without operating a full learning-management system such as Moodle.

Current release: **0.0.12**

## What Scholarius does

- Imports and exports QTI-style XML question banks.
- Creates and edits question banks through a web interface.
- Adds, edits, retires, and deletes questions.
- Supports quiz and test workflows, randomized selection, scoring, and history.
- Stores user profiles and preferences, including light and dark themes.
- Runs locally or in Docker with automatically generated self-signed HTTPS certificates.

## Question-bank ownership

Each XML file is the authoritative copy of its question bank. Question text, answer choices, explanations, domain/objective metadata, and active/retired status are written to XML.

SQLite supports application concerns such as users, the installed-bank catalogue, attempts, scores, and history. It is not intended to replace the XML master copy of question content.

Question-bank saves are written to a temporary file, parsed for validity, backed up to `<bank>.xml.bak`, and then atomically replace the original XML file.

A question marked **Retired (black label)** remains in its bank for historical and editorial purposes but is excluded from quizzes and tests.

## Run with Docker

```bash
docker compose up -d --build
```

Then open:

```text
https://localhost:8000
```

The first connection will normally show a browser warning because Scholarius creates a self-signed certificate. The certificate and SQLite database persist in the mounted `app/` directory.

To inspect startup:

```bash
docker compose logs -f scholarius
```

To stop the service:

```bash
docker compose down
```

## Repository layout

```text
README.md
changelog.md
docs/
app/
Dockerfile
compose.yaml
requirements.txt
```

The root directory is the Docker build context. The active Python package, templates, static files, XML banks, database, and certificates are under `app/`.

## Project status and accessibility

Scholarius is a work in progress and is **not considered production-ready**. It has not undergone a formal security review or accessibility certification.

The interface nevertheless includes practical accessibility foundations: labeled controls, keyboard focus indicators, reduced-motion support, light/dark/system themes, zoom-tolerant layouts, and labels that do not depend on color alone.

## License

Scholarius is released under the MIT License. See `LICENSE` for the full terms.
