# Question Bank Editor - Quick Start

**Time to implement: ~30 minutes**

## ✅ Checklist

### Step 1: Backup & Files (5 min)

- [ ] Backup your scholarius repo
- [ ] Copy these files into your repo:
  ```
  app/db_extended.py → replace app/db.py
  app/parser_qti_extended.py → replace app/parser_qti.py
  app/models_updated.py → replace app/models.py
  app/routes_qb_editor.py → NEW file in app/
  app/templates/qb_*.html → THREE new templates
  ```

### Step 2: Database (5 min)

- [ ] In `app/db.py`, verify `init_db()` is called on app startup
- [ ] Delete `scholarius.db` to force re-initialization (OR run SQL manually)
- [ ] Restart app to create new tables

### Step 3: Routes (5 min)

- [ ] Open `app/main.py`
- [ ] At the END of the file (before `if __name__ == "__main__"`), add:

```python
# Initialize Question Bank Management routes
from app.routes_qb_editor import add_qb_routes
add_qb_routes(app, templates, is_admin, session_user)
```

- [ ] Save

### Step 4: QTI Parser Hook (5 min)

- [ ] Find `import_quiz` function in `app/main.py`
- [ ] Find the line: `conn.execute("INSERT INTO quizzes...`
- [ ] After that `conn.execute(...)`, add this:

```python
# Store questions in database for editing
try:
    from app.parser_qti_extended import load_qti_bank, store_question_bank_to_db
    bank = load_qti_bank(destination)
    store_question_bank_to_db(bank)
except Exception as e:
    print(f"Note: Question storage for editing failed: {e}")
    # Continue anyway - quiz will still work
```

### Step 5: Navigation (2 min)

- [ ] Open `app/templates/home.html`
- [ ] Add this link somewhere in the navigation:

```html
<li class="nav-item">
    <a class="nav-link" href="/qb-manage">📚 Question Bank</a>
</li>
```

### Step 6: Test (3 min)

```bash
# Rebuild and restart
docker compose down
docker compose up -d --build

# Wait for startup...
# Open browser to http://localhost:8000
```

- [ ] Login as admin
- [ ] Click "Question Bank" in navigation
- [ ] See question banks (or import one if none exist)
- [ ] Click "View & Edit"
- [ ] See questions listed as cards
- [ ] Click "Edit" on a question
- [ ] Change something and save

### Step 7: Verify

- [ ] Questions appear after import ✓
- [ ] Can filter by domain ✓
- [ ] Can filter by type ✓
- [ ] Can edit question text ✓
- [ ] Can edit answer choices ✓
- [ ] Can set correct answer ✓
- [ ] Can add explanation ✓
- [ ] Can delete questions ✓

## If Something Breaks

**"404 Not Found" on /qb-manage:**
- Did you add `add_qb_routes()` to main.py?
- Check that templates are in `app/templates/` with exact names

**Database error:**
- Delete `app/scholarius.db` and restart (will reinitialize)
- Or run the SQL from `01_db_schema_extension.sql` manually

**Questions not appearing after import:**
- Make sure you added the `store_question_bank_to_db()` call in import_quiz
- Reimport your QTI file
- Check app logs for errors

**Templates not rendering (blank page):**
- Check Bootstrap CDN is accessible
- Verify template filenames in `app/templates/`
- Check Jinja2 is working (other templates should also fail)

## What's Working Now (LEVEL 1)

✅ Import QTI → questions stored in SQLite  
✅ List all banks  
✅ View questions in bank  
✅ Filter by domain and type  
✅ Edit question prompt  
✅ Edit answer choices  
✅ Set correct answer  
✅ Add explanation/review  
✅ Delete questions  
✅ Domain/objective assignment  

## Coming Next (LEVEL 2)

🔄 Create new questions from UI  
🔄 Create/manage domains  
🔄 Better matching editor  
🔄 Better order selection editor  
🔄 Bulk operations  

## When You're Done

Commit to git:

```bash
git add .
git commit -m "Add LEVEL 1 Question Bank Editor

- Question bank listing with card view
- Question editing (MC, T/F, Matching, Order Select)
- Filtering by domain and type
- Explanation/review text support
- Database schema for question management"

git push
```

## File Locations Reference

| File | Location | Action |
|------|----------|--------|
| db_extended.py | app/db.py | Replace |
| parser_qti_extended.py | app/parser_qti.py | Replace |
| models_updated.py | app/models.py | Replace |
| routes_qb_editor.py | app/routes_qb_editor.py | New file |
| qb_manage_home.html | app/templates/ | New file |
| qb_view_bank.html | app/templates/ | New file |
| qb_edit_question.html | app/templates/ | New file |

---

**Questions?** Check INTEGRATION_GUIDE.md for detailed explanations.

**Ready?** Let's ship it! 🚀
