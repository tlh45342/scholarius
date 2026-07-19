# Scholarius Complete Changelog (v0.0.2 → v0.0.8)

**Current Version:** 0.0.8  
**Status:** Under active development, not production-ready  
**Last Updated:** July 19, 2026

---

## Overview

Scholarius has evolved from a basic question viewer to a complete student-focused quiz platform with authentication, history tracking, and question bank management.

---

## Version History

### v0.0.2: Domain-Aware Test Building (First Release)

**Focus:** Blueprint-based quiz generation with domain weighting

**Files Changed:**
- `app/main.py`
- `app/models.py`
- `app/parser_qti.py`
- `app/static/style.css`
- `app/templates/action.html`
- `app/templates/quiz.html`
- `app/templates/results.html`

**New Files:**
- `app/version.py`
- `app/selector.py`
- `tests/test_blueprint.py`

**Features Added:**
- ✅ Authoritative version reporting (`/version` and `/v1/version`)
- ✅ QTI question-level metadata parsing (domain, objective, question_type)
- ✅ Scholarius XML blueprint parsing
- ✅ Largest-remainder percentage allocation algorithm
- ✅ Weighted random selection by domain
- ✅ User-selectable question count (for custom quizzes)
- ✅ Quiz vs Test mode selection
- ✅ Random fallback for banks without blueprints
- ✅ Domain inventory display on setup page
- ✅ Domain selection summary on results page

**How It Works:**
- Students can create custom quizzes by selecting question count
- System uses exam blueprint to randomly select questions weighted by domain
- Results show which domains were tested and performance by domain

---

### v0.0.3: Persistent History

**Focus:** Student progress tracking and review

**Features Added:**
- ✅ Records each completed attempt (timestamp, score, mode)
- ✅ Records every selected and correct answer for each question
- ✅ Stores domain and objective metadata with answers
- ✅ "Mark for Review" feature on question page
- ✅ History page shows recent attempts and aggregate domain performance
- ✅ In-place SQLite database migration (no data loss)

**Student Benefit:**
- Students can review their quiz history
- See which domains they struggle with
- Review marked questions they wanted to revisit
- Aggregate performance data helps identify weak areas

**Database Changes:**
- `attempts` table - quiz sessions
- `attempt_answers` table - individual question answers with metadata

---

### v0.0.4: Authentication & Administration

**Focus:** Security, role-based access, student privacy

**Features Added:**
- ✅ First-run admin creation at `/setup`
- ✅ PBKDF2-SHA256 password hashing (Python standard library)
- ✅ Real username/password verification
- ✅ Self-service user registration at `/register`
- ✅ Role-based access control (`admin`, `user`)
- ✅ Admin-only pages for Question Bank Management and Administration
- ✅ Profile management (`/profile`):
  - Editable display name
  - Light/dark theme preference
  - Password change
- ✅ Logout support
- ✅ Automatic password upgrade (plaintext → hashed after login)

**Security Details:**
- Old plaintext development passwords auto-upgrade on first login
- Existing user table migrated in place (no data loss)
- Students' history/preferences tied to accounts

**Admin Capabilities:**
- Import question banks (QTI XML)
- Manage users
- View administration dashboard

---

### v0.0.5: Refined First-Run Experience

**Focus:** UX polish, navigation clarity, question bank workflow

**First-Run Changes:**
- ✅ Welcome card before admin creation (explains what Scholarius is)
- ✅ Admin creation moved to `/setup/admin` (separate from welcome)
- ✅ Welcome only appears when no users exist

**Navigation Improvements:**
- ✅ Discreet Home/Back icon in lower-left of task cards
- ✅ Global navigation retained (Home, Profile, Admin)
- ✅ Version indicator remains subtle

**Question Bank Management Refactor:**
- ✅ `/qb-manage` simplified to show installed banks
- ✅ QTI upload moved to `/qb-manage/import` (dedicated page)
- ✅ "Import Question Bank" button on management card
- ✅ Import errors stay on import page for retry
- ✅ Successful imports return to bank list

**Account UX:**
- ✅ "Create Account" button remains on login card
- ✅ Explains that accounts save history & preferences

**Philosophy:**
- Simpler is better
- Dedicated pages for different tasks
- Clear error handling and flow

---

### v0.0.6: Progressive Disclosure & Accessibility

**Focus:** UX best practices, screen reader support, keyboard navigation

**Features Added:**
- ✅ "Create Account" tooltip on hover/focus:
  > "Create a user account to save quiz history, marked questions, and preferences."
- ✅ Aria labels for screen reader support
- ✅ Keyboard-visible focus states
- ✅ Reduced-motion preference support
- ✅ Tooltip displays on both mouse hover and keyboard focus

**Accessibility Foundation:**
- Information revealed progressively (not all at once)
- Actions remain understandable even without tooltips
- Aria relationships connect button to explanation

**Design Philosophy:**
- Keep primary interface quiet
- Reveal supporting info when user shows interest
- Respect user accessibility preferences

---

### v0.0.7: Task-Focused Management

**Focus:** Clear workflows, placeholder architecture, navigation polish

**Question Bank Management Refactor:**
- ✅ Management card is now a task launcher
- ✅ Separate focused cards for each operation
- ✅ Navigation clarity through dedicated pages

**Implemented Pages:**
- ✅ **List** - Installed question banks
- ✅ **Import** - QTI XML upload and validation

**Placeholder Pages** (Reserved for future work):
- 📋 **Export** - Export question bank to file
- 📋 **Create** - Create new question bank from scratch
- 📋 **Edit** - Edit existing question bank

**History Navigation:**
- ✅ Standard lower-left Home icon (removed text "Home" link)
- ✅ Consistent with other task cards

**Visual Polish:**
- ✅ Darkened blue page gradient (restrained appearance)
- ✅ Version stamp - stronger contrast & weight (but still secondary)

---

### v0.0.8: Theming & Final UX Polish

**Focus:** Visual consistency, accessibility foundation, system integration

**Theme System:**
- ✅ Light, Dark, and Follow System theme options
- ✅ Preference stored with user account
- ✅ Applies across all rendered pages
- ✅ Shared CSS variables for future pages
- ✅ Theme-aware contrast for accessibility

**UI Consistency:**
- ✅ Home-screen actions use consistent blue primary buttons
- ✅ Question Bank Management actions use consistent blue buttons
- ✅ Removed textual "Home" links from quiz cards
- ✅ Preserved explicit question-marking behavior

**Accessibility Enhancements:**
- ✅ Keyboard-visible focus indicators (all elements)
- ✅ Reduced-motion preferences respected
- ✅ Theme-aware contrast variables
- ✅ Accessible labels on icon controls
- ✅ Documentation of accessibility intent in README.md

**Bug Fixes:**
- ✅ Fixed Question Bank List route (now reads from SQLite)

**Philosophy:**
- Visual harmony across the app
- Foundation for future accessibility work
- System theme integration (Light/Dark/Auto)

---

## Architecture Overview

### Current Stack

**Backend:**
- FastAPI (Python 3.11+)
- SQLite (local database)
- Jinja2 templates
- Python stdlib security (PBKDF2-SHA256)

**Frontend:**
- HTML/CSS/JavaScript (vanilla)
- Bootstrap 5 (for components)
- No JavaScript framework (intentionally simple)
- Responsive design

**Data Storage:**
- SQLite database (single file: `app/scholarius.db`)
- QTI XML format for question banks
- JSON in cells for complex data (attempts, answers)

### Database Schema

**Users:**
- `users` - User accounts (username, password hash, theme, display_name, role)

**Quizzes & Attempts:**
- `quizzes` - Imported question banks
- `attempts` - Quiz sessions (user, quiz_id, score, timestamp)
- `attempt_answers` - Individual answers (attempt_id, question_id, selected, correct, domain, objective)

**Question Management** (NEW with v0.0.9 - Question Editor):
- `question_banks` - Imported bank metadata
- `questions` - Individual questions (editable)
- `question_choices` - Answer choices
- `domains` - Domain/objective hierarchy

### Key Files

```
app/
├── main.py           - FastAPI app, routes
├── models.py         - Pydantic dataclasses
├── db.py             - SQLite connection & init
├── parser_qti.py     - QTI XML parsing
├── selector.py       - Quiz generation logic
├── auth.py           - Authentication/hashing
├── version.py        - Version info
├── engine.py         - Quiz/test logic
├── static/           - CSS, JavaScript
└── templates/        - Jinja2 HTML templates
```

---

## Student Workflow (Current v0.0.8)

```
1. User visits /
   ↓
2. If not logged in → /login (or /register for new account)
   ↓
3. Authenticated → Home page with options:
   - Take Quiz (weighted by domain)
   - Take Test (full bank)
   - View History (past attempts)
   - Question Bank (admin only)
   ↓
4. Take Quiz/Test:
   - Questions presented one at a time
   - Mark for Review option
   - Submit each answer
   ↓
5. Results page:
   - Score, time, questions attempted
   - Domain performance
   - Marked questions for review
   ↓
6. View History:
   - Past attempts
   - Aggregate performance by domain
   - Review specific attempts
```

---

## Admin Workflow (Current v0.0.8)

```
1. Admin logs in
   ↓
2. Question Bank Management (/qb-manage):
   - List installed banks
   - Import new QTI XML
   - (Export, Create, Edit - placeholders)
   ↓
3. Import QTI:
   - Upload XML file
   - Validation
   - Success → back to list
   ↓
4. Administration (future):
   - User management
   - System settings
   - Analytics
```

---

## Question Editor Integration (v0.0.9 - Planned)

**Status:** Ready to integrate (built in this session)

### What's Being Added

**Two versions available:**
- **LEVEL 1** - Single-choice editor
- **LEVEL 1.5** - Single + Multiple-choice editor

### New Database Tables

```sql
question_banks       -- Imported bank metadata
questions            -- Individual questions (editable)
question_choices     -- Answer choices per question
domains              -- Domain taxonomy
objectives           -- Objective taxonomy
```

### New Routes

```
GET  /qb-manage/                    - Bank listing page
GET  /qb-manage/bank/{bank_id}      - Questions in bank (with filters)
GET  /qb-manage/edit/{question_id}  - Edit form
POST /qb-manage/edit/{question_id}  - Save changes
POST /qb-manage/delete/{question_id} - Delete question
GET  /qb-manage/api/questions       - JSON API
```

### New Templates

```
qb_manage_home.html      - Bank listing (cards)
qb_view_bank.html        - Questions in bank (searchable)
qb_edit_question.html    - Question editor form
```

### Workflow

```
Admin imports QTI bank with messy OCR/extracted questions
   ↓
Uses Question Bank Management to view all questions
   ↓
Clicks "Edit" on any question
   ↓
Edits prompt, choices, correct answer, explanation
   ↓
Saves → validates → persists to database
   ↓
Questions now clean and ready for student quizzes
```

### Benefits

- ✅ Fix OCR artifacts in extracted questions
- ✅ Add explanations to questions
- ✅ Organize by domain/objective
- ✅ Support multiple-choice (select 2+)
- ✅ Create questions from scratch (future)

---

## Compatibility Notes

### Question Editor Integration

**Safe to integrate:**
- ✅ No changes to quiz engine
- ✅ No changes to student workflow
- ✅ Backward compatible database
- ✅ New tables only (no schema modifications to existing)
- ✅ Separate from attempt/history tracking

**Where it fits:**
- Admin only - students don't see editor
- Sits between import and quiz taking
- Improves question quality before students take quizzes

**Two Integration Strategies:**

**Option A: Merge files into existing repo**
```bash
# Use ZIP file approach
unzip scholarius-editor-level1.zip
# Files already named correctly
# Just update main.py with 2 lines
```

**Option B: Keep separate until tested**
```bash
# Integrate on a branch first
# Test thoroughly
# Merge when confident
```

---

## Version History Summary

| Version | Focus | Key Achievement |
|---------|-------|-----------------|
| 0.0.2 | Blueprint & Selection | Domain-aware quiz generation |
| 0.0.3 | History & Review | Student progress tracking |
| 0.0.4 | Auth & Admin | Secure accounts & roles |
| 0.0.5 | Workflow | Clean task-focused UX |
| 0.0.6 | Accessibility | Progressive disclosure & ARIA |
| 0.0.7 | Architecture | Clear task separation |
| 0.0.8 | Theming | System integration & consistency |
| **0.0.9** | **Question Editing** | **Admin can polish questions** |

---

## Known Limitations (v0.0.8)

❌ Questions cannot be created from UI (import only)  
❌ No question editing interface  
❌ No multi-select/matching questions  
❌ No analytics dashboard  
❌ No question export  
❌ Not suitable for large deployments (single SQLite file)  

---

## Roadmap (Post v0.0.8)

### Immediate (v0.0.9 - Ready Now)
- ✅ Question Bank Editor (single + multi-choice)
- 📋 Create new questions from UI
- 📋 Manage domains/objectives dynamically

### Short-term (v0.1.0)
- 📋 Question bank export to QTI
- 📋 Matching question type UI
- 📋 Order selection with drag-and-drop
- 📋 Bulk question operations

### Medium-term (v0.2.0)
- 📋 Analytics dashboard
- 📋 Student performance predictions
- 📋 Adaptive question selection
- 📋 REST API for integrations

### Long-term (v1.0.0)
- 📋 Multi-database support (PostgreSQL)
- 📋 Scaling infrastructure
- 📋 Advanced analytics
- 📋 Production-grade security audit

---

## Getting Started With v0.0.8 + Question Editor

1. **Review this document** - Understand what's been built
2. **Verify existing setup** - Current Scholarius is running
3. **Choose integration approach**:
   - LEVEL 1 (safer) vs LEVEL 1.5 (full features)
4. **Extract ZIP** - Files already organized correctly
5. **Update main.py** - 2 lines of code
6. **Test** - Import questions, try editor
7. **Deploy** - Push to production

---

## Questions?

Each version has its own UPDATE file with:
- Detailed file changes
- Installation instructions
- Testing procedures
- Architecture decisions

Review the specific UPDATE file for version details.

---

**Scholarius: Build once, review well, learn confidently.** ⭐

Status: Under active development. Not production-ready. Use for education purposes.
