# Scholarius 0.0.2 update

This update adds the first domain-aware test-building slice.

## Changed files

- `app/main.py`
- `app/models.py`
- `app/parser_qti.py`
- `app/static/style.css`
- `app/templates/action.html`
- `app/templates/quiz.html`
- `app/templates/results.html`

## New files

- `app/version.py`
- `app/selector.py`
- `tests/test_blueprint.py`

## Features

- One authoritative version value: `0.0.2`
- Version returned by `/version` and `/v1/version`
- Version printed during application startup
- QTI question-level `domain`, `objective`, and `question_type` metadata parsing
- Scholarius XML blueprint parsing
- Largest-remainder percentage allocation
- Weighted random selection by domain
- User-selectable question count
- Quiz or Test mode selection
- Random fallback for old banks without blueprints
- Domain inventory and expected default-test allocation on the setup page
- Actual domain selection summary on the results page

## Install

Copy the listed files into the matching paths in the GitHub repository, commit, pull on the server, and rebuild:

```bash
git add app tests UPDATE-0.0.2.md
git commit -m "Add domain-aware weighted test generation and version 0.0.2"
git push
```

On the server:

```bash
git pull
docker compose down
docker compose up -d --build
docker logs scholarius
```

Confirm version reporting:

```bash
curl http://localhost:8000/version
```

Expected:

```json
{"product":"Scholarius","version":"0.0.2"}
```

Then import the AZ-900 XML through Question Bank Management and open it through Take Quiz / Test.
