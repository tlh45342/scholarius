# Multi-Choice Support Integration Guide

**Status:** Ready to integrate  
**Feature:** Multiple-choice questions (select 2+ correct answers)  
**Time to integrate:** ~20 minutes  

## Overview

This adds full support for **multiple-choice questions** where students select 2 or more correct answers. Examples:

> "Which TWO actions can you perform? Each correct answer presents a complete solution."
> - ☑ Action A
> - ☑ Action B  
> - ☐ Action C
> - ☐ Action D

## What's Changing

| Component | Change | File |
|-----------|--------|------|
| Database | Add `correct_answers` column (JSON) | db_extended_multichoice.py |
| Models | Add `correct_answers` list field | models_multichoice.py |
| Parser | Detect & parse multi-choice from QTI | parser_qti_multichoice.py |
| Routes | Handle checkbox form submission | routes_qb_editor_multichoice.py |
| Template | Show checkboxes vs radio buttons | qb_edit_question_multichoice.html |

## Integration Steps

### Step 1: Update Database (5 min)

Replace `app/db.py` with `db_extended_multichoice.py`:

```bash
cp db_extended_multichoice.py app/db.py
```

**What's new:**
- `correct_answers TEXT` column in `questions` table
- Stores JSON array of correct choices: `["A", "B"]`
- Backward compatible (single-choice still uses `correct_answer`)

### Step 2: Update Models (2 min)

Replace `app/models.py` with `models_multichoice.py`:

```bash
cp models_multichoice.py app/models.py
```

**What's new:**
```python
correct: Optional[str] = None  # Single-choice: "A"
correct_answers: Optional[List[str]] = None  # Multi-choice: ["A", "B"]
is_multichoice() -> bool  # Helper method
```

### Step 3: Update Parser (2 min)

Replace `app/parser_qti.py` with `parser_qti_multichoice.py`:

```bash
cp parser_qti_multichoice.py app/parser_qti.py
```

**What's new:**
- Detects QTI `cardinality="multiple"` attribute
- Parses all correct responses into a list
- Auto-detects multi-choice from prompt keywords:
  - "select two"
  - "which two"
  - "each correct answer"
  - etc.
- Stores as JSON in database
- Retrieves and deserializes correctly

### Step 4: Update Routes (2 min)

Replace the routes in `app/main.py` with `routes_qb_editor_multichoice.py`:

In your `app/main.py`, find this section:
```python
from app.routes_qb_editor import add_qb_routes
add_qb_routes(app, templates, is_admin, session_user)
```

Replace with:
```python
from app.routes_qb_editor_multichoice import add_qb_routes
add_qb_routes(app, templates, is_admin, session_user)
```

**What's new:**
- POST handler checks `question_type` field
- For multi-choice: collects all checked checkboxes
- For single-choice: collects single radio button
- Stores as JSON if multiple correct answers
- Form validation ensures at least one correct answer

### Step 5: Update Template (2 min)

Replace your question editor template:

```bash
# Delete old template
rm app/templates/qb_edit_question.html

# Add new template  
cp qb_edit_question_multichoice.html app/templates/qb_edit_question_multichoice.html
```

**What's new:**
- Dynamic form controls based on question type
- Radio buttons for single-choice
- Checkboxes for multiple-choice
- JavaScript switches between radio/checkbox UI
- Help text explains which mode is active
- Type-specific styling (green for multi-choice, blue for single, orange for T/F)

### Step 6: Database Migration (5 min)

Delete the old database to force re-initialization:

```bash
rm app/scholarius.db
```

When you restart the app, it will automatically create all tables including the new `correct_answers` column.

**OR** manually add the column if you want to keep existing data:

```bash
sqlite3 app/scholarius.db "ALTER TABLE questions ADD COLUMN correct_answers TEXT;"
```

### Step 7: Restart & Test (2 min)

```bash
docker compose down
docker compose up -d --build
```

Wait for app to start, then:

1. **Login**
2. **Go to** Question Bank Management
3. **Import** a test bank or use existing questions
4. **Edit a question** and change type to "multiple-choice"
5. **Select 2+ correct answers** using checkboxes
6. **Save** - should work!

## Testing Checklist

- [ ] Can create/import single-choice questions
- [ ] Can edit single-choice questions
- [ ] Radio buttons show for single-choice
- [ ] Can change to "multiple-choice" type
- [ ] Checkboxes show for multiple-choice
- [ ] Can select 2+ correct answers
- [ ] Form rejects if 0 correct answers selected
- [ ] Saves correctly to database
- [ ] Questions show correct type when viewing bank
- [ ] Can switch back and forth between types
- [ ] Existing questions still work (backward compatible)

## Data Structure

### Single-Choice Question
```json
{
  "id": 1,
  "qid": "q1",
  "question_type": "single-choice",
  "prompt": "What is...?",
  "choices": {"A": "text", "B": "text", "C": "text", "D": "text"},
  "correct_answer": "B",
  "correct_answers": null
}
```

### Multi-Choice Question
```json
{
  "id": 2,
  "qid": "q2",
  "question_type": "multiple-choice",
  "prompt": "Which TWO...? Each correct answer...",
  "choices": {"A": "text", "B": "text", "C": "text", "D": "text"},
  "correct_answer": null,
  "correct_answers": ["A", "B"]
}
```

In database (questions table):
- Single-choice: `correct_answer = "B"`, `correct_answers = null`
- Multi-choice: `correct_answer = null`, `correct_answers = '["A", "B"]'` (JSON)

## API & Import

### QTI XML Support

Single-choice:
```xml
<responseDeclaration identifier="RESPONSE" cardinality="single">
  <correctResponse><value>B</value></correctResponse>
</responseDeclaration>
```

Multi-choice:
```xml
<responseDeclaration identifier="RESPONSE" cardinality="multiple">
  <correctResponse>
    <value>A</value>
    <value>B</value>
  </correctResponse>
</responseDeclaration>
```

Both are automatically detected and handled.

## Backward Compatibility

✅ **Fully backward compatible:**
- Old single-choice questions still work
- No data loss on migration
- Can mix single and multi-choice in same bank
- Querying doesn't break
- Old API calls still work

## Known Limitations (LEVEL 1)

- No visual question preview yet (LEVEL 2)
- No bulk edit for question types (LEVEL 2)
- Matching and Order Selection are stored but editing UI is basic (LEVEL 2)
- No scoring rules defined yet for multi-choice (e.g., partial credit)

## Files Reference

| Old File | New File | Location |
|----------|----------|----------|
| db.py | db_extended_multichoice.py | app/ |
| models.py | models_multichoice.py | app/ |
| parser_qti.py | parser_qti_multichoice.py | app/ |
| routes_qb_editor.py | routes_qb_editor_multichoice.py | app/ |
| qb_edit_question.html | qb_edit_question_multichoice.html | app/templates/ |

## Troubleshooting

**Q: Checkboxes don't appear for multi-choice**  
A: Reload the page (Ctrl+Shift+R for hard refresh). JavaScript loads on page load.

**Q: Getting database error on import**  
A: Delete scholarius.db and restart. It will recreate with correct schema.

**Q: Multi-choice questions not showing correct answers when editing**  
A: Make sure you're on the new template. Old template won't show them.

**Q: Form submission fails with "correct answer required"**  
A: For multi-choice, you need to check at least one checkbox. Check the form validation.

## Next: LEVEL 2

Once this is stable:

- Visual UI for matching question types
- Order selection with drag-and-drop
- Question preview/test before save
- Scoring rules for multi-choice (all correct = full points, partial credit, etc.)
- Better type icons in card view

## Questions?

Refer to specific file comments for detailed logic. All files are well-commented.

---

**Ready to ship!** 🚀

Integrate, test, and you've got full multi-choice support alongside single-choice, T/F, and other types.
