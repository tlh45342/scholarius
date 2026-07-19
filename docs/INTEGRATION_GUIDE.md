# Question Bank Editor - Integration Guide

This guide walks you through integrating the LEVEL 1 Question Bank Editor into Scholarius.

## Overview

The editor provides:
- ✅ Question bank listing (card view)
- ✅ Question filtering (by domain, type)
- ✅ Edit questions (True/False, Multiple Choice, Matching, Order Selection)
- ✅ Add/delete questions
- ✅ Store explanation/review text
- ✅ Domain/objective assignment
- ✅ All users can edit (not admin-only)

## Integration Steps

### 1. Update Database Schema

**File:** `app/db.py`

Replace your current `db.py` with the provided `db_extended.py`. This adds:
- `question_banks` table - stores imported bank metadata
- `questions` table - individual questions with full metadata
- `question_choices` table - answer choices for each question
- `domains` and `objectives` tables - organizational metadata

Or manually run the SQL in `01_db_schema_extension.sql` against `scholarius.db`.

```bash
# Option A: Replace the file
cp db_extended.py app/db.py

# Option B: Run SQL manually (if db.py works for you)
sqlite3 app/scholarius.db < 01_db_schema_extension.sql
```

### 2. Update Models

**File:** `app/models.py`

Replace with `models_updated.py` to add the `explanation` field to the Question dataclass.

```bash
cp models_updated.py app/models.py
```

### 3. Update QTI Parser

**File:** `app/parser_qti.py`

Replace with `parser_qti_extended.py`. This adds functions to:
- Store parsed questions to SQLite
- Retrieve questions by bank
- Retrieve individual questions by ID
- Extract explanation/review text from QTI

```bash
cp parser_qti_extended.py app/parser_qti.py
```

### 4. Integrate Routes into FastAPI

**File:** `app/main.py`

At the end of your `main.py` (after app initialization but before `if __name__ == "__main__"`), add:

```python
# Import the route module
from app.routes_qb_editor import add_qb_routes

# Initialize the question bank routes
add_qb_routes(app, templates, is_admin, session_user)
```

**IMPORTANT:** Make sure these functions exist in main.py:
- `templates` (Jinja2Templates object)
- `is_admin(session)` function
- `session_user(request)` function

If they don't exist, define them based on your current authentication setup.

### 5. Add Templates

**Files:** Copy to `app/templates/`

- `qb_manage_home.html` - Question bank listing
- `qb_view_bank.html` - View/filter questions in a bank
- `qb_edit_question.html` - Edit single question

```bash
cp qb_manage_home.html app/templates/
cp qb_view_bank.html app/templates/
cp qb_edit_question.html app/templates/
```

### 6. Update Main Template Navigation

**File:** `app/templates/home.html` (or wherever your main nav is)

Add a link to the Question Bank Management:

```html
<li class="nav-item">
    <a class="nav-link" href="/qb-manage">📚 QB Management</a>
</li>
```

Or if you have a separate admin/tools section:

```html
{% if is_admin %}
<li class="nav-item">
    <a class="nav-link" href="/qb-manage">📚 Question Bank Editor</a>
</li>
{% endif %}
```

### 7. Hook Import into QTI Parser

**File:** `app/main.py` - find the import_quiz route

After successfully importing a QTI file, store it in the database:

Find this section in `import_quiz` function (around line 490):

```python
conn.execute(
    """
    INSERT INTO quizzes (id, title, filename)
    VALUES (?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        title=excluded.title,
        filename=excluded.filename
    """,
    (quiz_id, title, filename),
)
```

After that block, add:

```python
# Store questions in the database for editing
try:
    from app.parser_qti_extended import load_qti_bank, store_question_bank_to_db
    bank = load_qti_bank(destination)
    store_question_bank_to_db(bank)
except Exception as e:
    print(f"Warning: Could not store questions for editing: {e}")
```

This makes newly imported question banks available for editing.

### 8. Testing

After integration, test the following:

1. **Start the app:**
   ```bash
   docker compose up -d --build
   ```

2. **Login** as admin or any user

3. **Navigate** to `/qb-manage`

4. **Import a QTI file** from the main import page (if you haven't already)

5. **View question bank** - click "View & Edit"

6. **Filter questions** - try filtering by domain or type

7. **Edit a question**:
   - Change the prompt
   - Edit answers
   - Change correct answer
   - Add explanation
   - Set domain/objective

8. **Save** - should redirect back to bank view

## File Structure After Integration

```
scholarius/
├── app/
│   ├── db.py (UPDATED with question bank tables)
│   ├── models.py (UPDATED with explanation field)
│   ├── parser_qti.py (UPDATED with storage functions)
│   ├── main.py (ADD route initialization at end)
│   ├── routes_qb_editor.py (NEW - question management routes)
│   ├── templates/
│   │   ├── qb_manage_home.html (NEW)
│   │   ├── qb_view_bank.html (NEW)
│   │   ├── qb_edit_question.html (NEW)
│   │   └── home.html (UPDATED navigation)
│   └── scholarius.db (AUTO-UPDATED with new tables)
```

## Features Breakdown

### Question Bank Home (`/qb-manage`)
- Card view of all imported question banks
- Shows question count per bank
- "View & Edit" button → view bank
- "Create Quiz" button → (future integration)

### View Bank (`/qb-manage/bank/{bank_id}`)
- List all questions in a bank as cards
- Filter by domain
- Filter by question type
- Edit or delete individual questions

### Edit Question (`/qb-manage/edit/{question_id}`)
- Edit prompt text
- Edit answer choices
- Set correct answer (radio button)
- Add/edit explanation (review text)
- Assign to domain and objective
- Change question type

## Known Limitations (LEVEL 1)

- Cannot create new questions (only edit imported ones)
- Cannot create new domains/objectives (only assign existing)
- Matching and Order Selection types are stored but UI is basic
- No image support in questions yet
- No bulk operations (edit multiple questions at once)

## LEVEL 2 Roadmap

These features will be added next:
- Create new questions from scratch
- Create/manage domains and objectives
- Better matching pair UI
- Order selection visual editor
- Bulk edit/delete
- Question bank cloning
- Export edited questions back to QTI

## Troubleshooting

**Problem:** Routes not found (404)
- Check that `add_qb_routes()` is called in main.py
- Verify templates directory path is correct

**Problem:** Database errors
- Ensure db_extended.py was properly installed
- Run `init_db()` again: it will create missing tables
- Check foreign key constraints

**Problem:** Questions not appearing after import
- Manually call `store_question_bank_to_db()` for older imports
- Check that parser_qti_extended.py is being used

**Problem:** Templates not rendering
- Verify Bootstrap CDN link is accessible
- Check template file names match exactly
- Ensure Jinja2 is configured correctly

## Questions?

Refer back to the architecture:
- Parser creates Question objects from QTI
- store_question_bank_to_db() normalizes into database
- Routes serve HTML templates with database data
- User edits in UI, changes saved back to database
- Questions remain available for quiz creation

The separation is intentional: question bank (for editing) is separate from quiz engine (for taking tests).
