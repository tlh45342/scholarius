from pathlib import Path
from datetime import datetime, timezone
import re
import uuid
import xml.etree.ElementTree as ET

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth import hash_password, verify_password
from app.db import get_conn, init_db
from app.engine import QuizEngine
from app.parser_qti import load_qti_bank
from app.selector import build_test, largest_remainder_counts
from app.version import PRODUCT_NAME, __version__, version_info

app = FastAPI(title=PRODUCT_NAME, version=__version__)
init_db()
print(f"{PRODUCT_NAME} {__version__} starting")

BASE_DIR = Path(__file__).resolve().parent
QTI_DIR = BASE_DIR / "qti"

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

SESSIONS = {}
SESSION_INDEX = {}


def current_session(request: Request):
    token = request.cookies.get("token")
    if not token:
        return None, None
    return token, SESSIONS.get(token)


def session_user(request: Request):
    _, session = current_session(request)
    return session if isinstance(session, dict) else None


def redirect_to_login():
    return RedirectResponse(url="/login", status_code=303)


def is_admin(session):
    return isinstance(session, dict) and session.get("role") == "admin"


def user_count():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    session = session_user(request)
    if session:
        return templates.TemplateResponse(
            request,
            "home.html",
            {
                "request": request,
                "username": session.get("username", "unknown"),
                "display_name": session.get("display_name") or session.get("username", "unknown"),
                "is_admin": is_admin(session),
                "version": __version__,
            },
        )
    if user_count() == 0:
        return RedirectResponse(url="/setup", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/version")
def version_endpoint():
    return version_info()


@app.get("/v1/version")
def version_endpoint_v1():
    return version_info()


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = ""):
    if user_count() == 0:
        return RedirectResponse(url="/setup", status_code=303)
    return templates.TemplateResponse(
        request, "login.html", {"request": request, "error": error, "version": __version__}
    )


@app.post("/auth/login")
def auth_login(username: str = Form(...), password: str = Form(...)):
    username = username.strip()
    conn = get_conn()
    row = conn.execute(
        "SELECT username, password, display_name, role, theme FROM users WHERE username=?",
        (username,),
    ).fetchone()
    if not row or not verify_password(password, row["password"]):
        conn.close()
        return RedirectResponse(url="/login?error=Invalid+username+or+password", status_code=303)

    # Upgrade old plaintext development passwords after a successful login.
    if not row["password"].startswith("pbkdf2_sha256$"):
        conn.execute("UPDATE users SET password=? WHERE username=?", (hash_password(password), username))
        conn.commit()
    conn.close()

    token = str(uuid.uuid4())
    SESSIONS[token] = {
        "username": row["username"],
        "display_name": row["display_name"] or row["username"],
        "role": row["role"] or "user",
        "theme": row["theme"] or "light",
    }
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="token", value=token, httponly=True, samesite="lax")
    return response


@app.get("/logout")
def logout(request: Request):
    token, _ = current_session(request)
    if token:
        SESSIONS.pop(token, None)
        SESSION_INDEX.pop(token, None)
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("token")
    return response


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, error: str = ""):
    if user_count() == 0:
        return RedirectResponse(url="/setup", status_code=303)
    return templates.TemplateResponse(
        request, "register.html", {"request": request, "error": error, "version": __version__}
    )


@app.post("/register")
def register_profile(
    username: str = Form(...),
    display_name: str = Form(""),
    password: str = Form(...),
    confirm_password: str = Form(...),
    theme: str = Form("light"),
):
    username = username.strip()
    display_name = display_name.strip() or username
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,40}", username):
        return RedirectResponse(url="/register?error=Use+3-40+letters,+numbers,+dots,+dashes,+or+underscores", status_code=303)
    if password != confirm_password:
        return RedirectResponse(url="/register?error=Passwords+do+not+match", status_code=303)
    try:
        password_hash = hash_password(password)
    except ValueError as exc:
        from urllib.parse import quote_plus
        return RedirectResponse(url=f"/register?error={quote_plus(str(exc))}", status_code=303)
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, password, display_name, role, theme, created_at) VALUES (?, ?, ?, 'user', ?, ?)",
            (username, password_hash, display_name, theme if theme in {'light','dark'} else 'light', datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    except Exception:
        conn.close()
        return RedirectResponse(url="/register?error=That+username+already+exists", status_code=303)
    conn.close()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, message: str = "", error: str = ""):
    session = session_user(request)
    if not session:
        return redirect_to_login()
    return templates.TemplateResponse(
        request, "profile.html", {"request": request, "user": session, "message": message, "error": error, "version": __version__}
    )


@app.post("/profile")
def profile_update(
    request: Request,
    display_name: str = Form(...),
    theme: str = Form("light"),
    new_password: str = Form(""),
    confirm_password: str = Form(""),
):
    token, session = current_session(request)
    if not token or not isinstance(session, dict):
        return redirect_to_login()
    display_name = display_name.strip() or session["username"]
    theme = theme if theme in {"light", "dark"} else "light"
    conn = get_conn()
    if new_password:
        if new_password != confirm_password:
            conn.close()
            return RedirectResponse(url="/profile?error=Passwords+do+not+match", status_code=303)
        try:
            password_hash = hash_password(new_password)
        except ValueError as exc:
            from urllib.parse import quote_plus
            conn.close()
            return RedirectResponse(url=f"/profile?error={quote_plus(str(exc))}", status_code=303)
        conn.execute("UPDATE users SET display_name=?, theme=?, password=? WHERE username=?",
                     (display_name, theme, password_hash, session["username"]))
    else:
        conn.execute("UPDATE users SET display_name=?, theme=? WHERE username=?",
                     (display_name, theme, session["username"]))
    conn.commit(); conn.close()
    session["display_name"] = display_name
    session["theme"] = theme
    return RedirectResponse(url="/profile?message=Profile+updated", status_code=303)


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def inspect_qti_xml(data: bytes):
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML: {exc}") from exc

    if local_name(root.tag) != "assessmentTest":
        raise ValueError("The root element must be assessmentTest.")

    quiz_id = root.attrib.get("identifier", "").strip()
    title = root.attrib.get("title", "").strip()
    if not quiz_id:
        raise ValueError("assessmentTest is missing its identifier attribute.")
    if not title:
        raise ValueError("assessmentTest is missing its title attribute.")

    supported = 0
    problems = []
    for item in (elem for elem in root.iter() if local_name(elem.tag) == "assessmentItem"):
        qid = item.attrib.get("identifier", "unknown")
        prompt = next((elem for elem in item.iter() if local_name(elem.tag) == "prompt"), None)
        choices = [elem for elem in item.iter() if local_name(elem.tag) == "simpleChoice"]
        correct_values = [
            (elem.text or "").strip()
            for parent in item.iter()
            if local_name(parent.tag) == "correctResponse"
            for elem in parent.iter()
            if local_name(elem.tag) == "value" and (elem.text or "").strip()
        ]
        choice_ids = {choice.attrib.get("identifier") for choice in choices}

        if prompt is None or not " ".join(prompt.itertext()).strip():
            problems.append(f"{qid}: missing prompt")
        elif len(choices) < 2:
            problems.append(f"{qid}: fewer than two choices")
        elif len(correct_values) != 1:
            problems.append(f"{qid}: requires exactly one correct answer")
        elif correct_values[0] not in choice_ids:
            problems.append(f"{qid}: correct answer does not match a choice")
        else:
            supported += 1

    if supported == 0:
        detail = "; ".join(problems[:5])
        raise ValueError("No supported single-answer questions were found." + (f" {detail}" if detail else ""))

    return quiz_id, title, supported, problems


def safe_quiz_filename(quiz_id: str) -> str:
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "-", quiz_id).strip(".-")
    if not safe_id:
        safe_id = uuid.uuid4().hex
    return f"{safe_id}.xml"


@app.get("/qb-manage", response_class=HTMLResponse)
def qb_manage_page(request: Request, message: str = "", error: str = ""):
    session = session_user(request)
    if not is_admin(session):
        return HTMLResponse("<h2>Administrator access required</h2><a href='/'>Home</a>", status_code=403)
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title, filename FROM quizzes ORDER BY title"
    ).fetchall()
    conn.close()
    return templates.TemplateResponse(
        request,
        "qb_manage.html",
        {
            "request": request,
            "quizzes": rows,
            "message": message,
            "error": error,
            "is_admin": True,
            "version": __version__,
        },
    )


@app.get("/qb-manage/import", response_class=HTMLResponse)
def qb_import_page(request: Request, error: str = ""):
    session = session_user(request)
    if not is_admin(session):
        return HTMLResponse(
            "<h2>Administrator access required</h2><a href='/'>Home</a>",
            status_code=403,
        )
    return templates.TemplateResponse(
        request,
        "qb_import.html",
        {
            "request": request,
            "error": error,
            "is_admin": True,
            "version": __version__,
        },
    )


@app.post("/qb-manage/import")
async def import_quiz(
    request: Request,
    quiz_file: UploadFile = File(...),
    overwrite: bool = Form(False),
):
    if not is_admin(session_user(request)):
        return HTMLResponse("<h2>Administrator access required</h2>", status_code=403)
    original_name = Path(quiz_file.filename or "").name
    if not original_name.lower().endswith(".xml"):
        return RedirectResponse(
            url="/qb-manage/import?error=Only+XML+files+can+be+imported.",
            status_code=303,
        )

    data = await quiz_file.read(2 * 1024 * 1024 + 1)
    await quiz_file.close()
    if not data:
        return RedirectResponse(
            url="/qb-manage/import?error=The+uploaded+file+was+empty.",
            status_code=303,
        )
    if len(data) > 2 * 1024 * 1024:
        return RedirectResponse(
            url="/qb-manage/import?error=The+XML+file+exceeds+the+2+MB+limit.",
            status_code=303,
        )

    try:
        quiz_id, title, question_count, warnings = inspect_qti_xml(data)
    except ValueError as exc:
        from urllib.parse import quote_plus
        return RedirectResponse(
            url=f"/qb-manage/import?error={quote_plus(str(exc))}",
            status_code=303,
        )

    filename = safe_quiz_filename(quiz_id)
    destination = QTI_DIR / filename

    conn = get_conn()
    existing = conn.execute(
        "SELECT filename FROM quizzes WHERE id=?", (quiz_id,)
    ).fetchone()
    if existing and not overwrite:
        conn.close()
        from urllib.parse import quote_plus
        return RedirectResponse(
            url=(
                "/qb-manage/import?error="
                + quote_plus(
                    f"Quiz '{quiz_id}' already exists. Select Replace existing quiz to overwrite it."
                )
            ),
            status_code=303,
        )

    QTI_DIR.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".xml.tmp")
    temporary.write_bytes(data)
    temporary.replace(destination)

    if existing and existing[0] != filename:
        old_path = QTI_DIR / existing[0]
        if old_path.exists() and old_path != destination:
            old_path.unlink()

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
    conn.commit()
    conn.close()

    from urllib.parse import quote_plus
    warning_text = f" ({len(warnings)} unsupported item(s) skipped by validation)" if warnings else ""
    message = quote_plus(
        f"Imported '{title}' with {question_count} supported questions{warning_text}."
    )
    return RedirectResponse(url=f"/qb-manage?message={message}", status_code=303)


@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    _, session = current_session(request)
    if not isinstance(session, dict):
        return RedirectResponse(url="/login", status_code=303)
    username = session.get("username", "unknown")
    conn = get_conn()
    attempts = conn.execute(
        """SELECT a.id, a.quiz_id, COALESCE(q.title, a.quiz_id) AS title, a.mode, a.score,
                  a.question_count, COALESCE(a.completed_at, a.timestamp) AS completed_at
           FROM attempts a LEFT JOIN quizzes q ON q.id=a.quiz_id
           WHERE a.username=? ORDER BY a.id DESC LIMIT 50""", (username,)
    ).fetchall()
    domains = conn.execute(
        """SELECT COALESCE(domain, 'Unclassified') AS domain, COUNT(*) AS seen,
                  SUM(was_correct) AS correct, ROUND(100.0*SUM(was_correct)/COUNT(*),1) AS accuracy
           FROM attempt_answers WHERE username=? GROUP BY COALESCE(domain, 'Unclassified') ORDER BY domain""",
        (username,),
    ).fetchall()
    summary = conn.execute(
        """SELECT COUNT(*) AS seen, SUM(was_correct) AS correct,
                  SUM(CASE WHEN was_correct=0 THEN 1 ELSE 0 END) AS missed,
                  SUM(marked_for_review) AS marked
           FROM attempt_answers WHERE username=?""", (username,)
    ).fetchone()
    conn.close()
    return templates.TemplateResponse(request, "history.html", {
        "request": request, "attempts": attempts, "domains": domains, "summary": summary,
        "username": username, "version": __version__, "is_admin": is_admin(session),
    })


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, message: str = "", error: str = ""):
    session = session_user(request)
    if not is_admin(session):
        return HTMLResponse("<h2>Administrator access required</h2><a href='/'>Home</a>", status_code=403)
    conn = get_conn()
    users = conn.execute("SELECT username, display_name, role, theme FROM users ORDER BY username").fetchall()
    conn.close()
    return templates.TemplateResponse(
        request, "admin.html", {"request": request, "users": users, "message": message, "error": error, "version": __version__, "is_admin": True}
    )


@app.post("/admin/create-user")
def admin_create_user(
    request: Request,
    username: str = Form(...),
    display_name: str = Form(""),
    password: str = Form(...),
    role: str = Form("user"),
):
    if not is_admin(session_user(request)):
        return HTMLResponse("<h2>Administrator access required</h2>", status_code=403)
    username = username.strip()
    try:
        password_hash = hash_password(password)
        conn = get_conn()
        conn.execute(
            "INSERT INTO users (username, password, display_name, role, theme, created_at) VALUES (?, ?, ?, ?, 'light', ?)",
            (username, password_hash, display_name.strip() or username, role if role in {'user','admin'} else 'user', datetime.now(timezone.utc).isoformat()),
        )
        conn.commit(); conn.close()
    except Exception as exc:
        from urllib.parse import quote_plus
        return RedirectResponse(url=f"/admin?error={quote_plus(str(exc))}", status_code=303)
    return RedirectResponse(url="/admin?message=User+created", status_code=303)


@app.get("/setup", response_class=HTMLResponse)
def setup_welcome_page(request: Request):
    if user_count() > 0:
        return HTMLResponse(
            "<h2>Scholarius is already configured.</h2>"
            "<a href='/login'>Continue to login</a>"
        )
    return templates.TemplateResponse(
        request,
        "setup_welcome.html",
        {"request": request, "version": __version__},
    )


@app.get("/setup/admin", response_class=HTMLResponse)
def setup_admin_page(request: Request, error: str = ""):
    if user_count() > 0:
        return HTMLResponse(
            "<h2>Scholarius is already configured.</h2>"
            "<a href='/login'>Continue to login</a>"
        )
    return templates.TemplateResponse(
        request,
        "setup.html",
        {"request": request, "error": error, "version": __version__},
    )


@app.post("/setup/create-admin")
def setup_create_admin(
    username: str = Form(...),
    display_name: str = Form(""),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    if user_count() > 0:
        return HTMLResponse("<h2>Setup has already been completed.</h2>", status_code=409)
    username = username.strip()
    if password != confirm_password:
        return RedirectResponse(url="/setup/admin?error=Passwords+do+not+match", status_code=303)
    try:
        password_hash = hash_password(password)
    except ValueError as exc:
        from urllib.parse import quote_plus
        return RedirectResponse(url=f"/setup/admin?error={quote_plus(str(exc))}", status_code=303)
    conn = get_conn()
    conn.execute(
        "INSERT INTO users (username, password, display_name, role, theme, created_at) VALUES (?, ?, ?, 'admin', 'light', ?)",
        (username, password_hash, display_name.strip() or username, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit(); conn.close()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/quiz-select", response_class=HTMLResponse)
def quiz_select_page(request: Request):
    if not session_user(request):
        return redirect_to_login()
    conn = get_conn()
    rows = conn.execute("SELECT id, title FROM quizzes ORDER BY title").fetchall()
    conn.close()
    quizzes = {row[0]: row[1] for row in rows}
    return templates.TemplateResponse(
        request,
        "quiz_select.html",
        {"request": request, "quizzes": quizzes, "version": __version__, "is_admin": is_admin(session_user(request))},
    )


@app.get("/action", response_class=HTMLResponse)
def action_page(request: Request, quiz_id: str):
    if not session_user(request):
        return redirect_to_login()
    conn = get_conn()
    row = conn.execute(
        "SELECT title, filename FROM quizzes WHERE id=?", (quiz_id,)
    ).fetchone()
    conn.close()
    if not row:
        return HTMLResponse("<h2>Quiz not found</h2>", status_code=404)

    try:
        bank = load_qti_bank(QTI_DIR / row[1])
    except Exception as exc:
        return HTMLResponse(
            f"<h2>Quiz file load failed</h2><pre>{exc}</pre>",
            status_code=500,
        )

    domain_inventory = {}
    for question in bank.questions:
        name = question.domain or "Unclassified"
        domain_inventory[name] = domain_inventory.get(name, 0) + 1

    default_count = (
        bank.blueprint.default_question_count
        if bank.blueprint and bank.blueprint.default_question_count
        else len(bank.questions)
    )
    default_count = min(default_count, len(bank.questions))
    planned_counts = {}
    if bank.blueprint:
        planned_counts = largest_remainder_counts(
            default_count,
            {domain.name: domain.target_percent for domain in bank.blueprint.domains},
        )

    return templates.TemplateResponse(
        request,
        "action.html",
        {
            "request": request,
            "quiz_id": quiz_id,
            "title": row[0],
            "bank": bank,
            "question_count": len(bank.questions),
            "default_count": default_count,
            "planned_counts": planned_counts,
            "domain_inventory": domain_inventory,
            "version": __version__,
            "is_admin": is_admin(session_user(request)),
        },
    )


def get_engine(token: str):
    session = SESSIONS.get(token)
    if not isinstance(session, dict):
        return None
    return session.get("engine")


@app.get("/start-quiz")
def start_quiz(
    request: Request,
    quiz_id: str,
    question_count: int = 0,
    selection_mode: str = "blueprint",
    quiz_mode: str = "quiz",
):
    token, session = current_session(request)
    if not token or not session:
        return RedirectResponse(url="/login", status_code=303)

    conn = get_conn()
    row = conn.execute("SELECT filename FROM quizzes WHERE id=?", (quiz_id,)).fetchone()
    conn.close()
    if not row:
        return HTMLResponse("<h2>Quiz not found in database</h2>", status_code=404)

    try:
        bank = load_qti_bank(QTI_DIR / row[0])
        requested = question_count if question_count > 0 else None
        selection = build_test(
            bank,
            question_count=requested,
            selection_mode=selection_mode,
        )
    except Exception as exc:
        return HTMLResponse(
            f"<h2>Quiz file load failed</h2><pre>{exc}</pre>",
            status_code=500,
        )

    if not selection.questions:
        return HTMLResponse(
            "<h2>No supported questions were found in this quiz.</h2>",
            status_code=400,
        )

    username = session.get("username", "unknown") if isinstance(session, dict) else str(session)
    updated_session = dict(session) if isinstance(session, dict) else {"username": username, "role": "user"}
    updated_session.update({
        "username": username,
        "engine": QuizEngine(selection.questions),
        "quiz_id": quiz_id,
        "quiz_mode": quiz_mode,
        "selection_mode": selection_mode,
        "domain_counts": selection.domain_counts,
        "selection_warnings": selection.warnings,
        "saved": False,
    })
    SESSIONS[token] = updated_session
    SESSION_INDEX[token] = 0
    return RedirectResponse(url="/quiz-ui", status_code=303)


@app.get("/quiz-ui", response_class=HTMLResponse)
def quiz_ui(request: Request):
    token, _ = current_session(request)
    if not token:
        return RedirectResponse(url="/login", status_code=303)

    engine = get_engine(token)
    if not engine:
        return HTMLResponse("<h2>No quiz selected</h2><a href='/'>Go Home</a>")

    idx = SESSION_INDEX.get(token, 0)
    if idx >= len(engine.questions):
        return RedirectResponse(url="/results-ui", status_code=303)

    return templates.TemplateResponse(
        request,
        "quiz.html",
        {
            "request": request,
            "question": engine.questions[idx],
            "is_last": idx == len(engine.questions) - 1,
            "position": idx + 1,
            "total": len(engine.questions),
            "version": __version__,
            "is_admin": is_admin(session_user(request)),
        },
    )


@app.post("/answer")
def answer(request: Request, qid: str = Form(...), choice: str = Form(...), marked: bool = Form(False)):
    token, _ = current_session(request)
    if not token:
        return RedirectResponse(url="/login", status_code=303)

    engine = get_engine(token)
    if not engine:
        return HTMLResponse("<h2>No quiz session</h2>", status_code=400)

    engine.answer(qid, choice, marked=marked)
    SESSION_INDEX[token] = SESSION_INDEX.get(token, 0) + 1
    return RedirectResponse(url="/quiz-ui", status_code=303)


@app.get("/results-ui", response_class=HTMLResponse)
def results_ui(request: Request):
    token, session = current_session(request)
    if not token or not isinstance(session, dict) or "engine" not in session:
        return RedirectResponse(url="/login", status_code=303)

    engine = session["engine"]
    if not session.get("saved"):
        now = datetime.now(timezone.utc).isoformat()
        conn = get_conn()
        cur = conn.execute(
            """INSERT INTO attempts (username, quiz_id, timestamp, completed_at, mode, selection_mode, score, question_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (session.get("username", "unknown"), session.get("quiz_id"), now, now,
             session.get("quiz_mode", "quiz"), session.get("selection_mode", "random"),
             engine.score(), len(engine.questions)),
        )
        attempt_id = cur.lastrowid
        for row in engine.answer_rows():
            conn.execute(
                """INSERT INTO attempt_answers
                   (attempt_id, username, quiz_id, question_id, domain, objective, selected_answer, correct_answer, was_correct, marked_for_review, answered_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (attempt_id, session.get("username", "unknown"), session.get("quiz_id"), row["question_id"],
                 row["domain"], row["objective"], row["selected_answer"], row["correct_answer"],
                 int(row["was_correct"]), int(row["marked_for_review"]), now),
            )
        conn.commit(); conn.close()
        session["saved"] = True
        session["attempt_id"] = attempt_id
    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "request": request,
            "score": engine.score(),
            "total": len(engine.questions),
            "domain_counts": session.get("domain_counts", {}),
            "selection_warnings": session.get("selection_warnings", []),
            "quiz_mode": session.get("quiz_mode", "quiz"),
            "version": __version__,
            "is_admin": is_admin(session),
        },
    )