"""Question-bank editor routes.

XML remains the authoritative question-bank representation. SQLite is an
editable index. Every successful editor save is written back to XML before the
index is refreshed.
"""

from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from app.db import get_conn
from app.parser_qti import (
    get_question_by_id,
    load_qti_bank,
    store_question_bank_to_db,
    update_question_in_qti,
    update_bank_metadata_in_qti,
    create_empty_qti_bank,
)


def add_qb_routes(app: FastAPI, templates, is_admin, session_user, qti_dir: Path):
    def require_admin(request: Request):
        session = session_user(request)
        if not session or not is_admin(session):
            return None
        return session


    def load_bank_record(bank_id: str):
        conn = get_conn()
        try:
            return conn.execute(
                "SELECT bank_id, title, filename, question_count, imported_at FROM question_banks WHERE bank_id=?",
                (bank_id,),
            ).fetchone()
        finally:
            conn.close()

    def load_authoritative_bank(bank_id: str):
        record = load_bank_record(bank_id)
        if not record:
            raise HTTPException(status_code=404, detail="Question bank not found")
        xml_path = qti_dir / record["filename"]
        if not xml_path.exists():
            raise HTTPException(status_code=500, detail="Authoritative XML file is missing")
        return record, xml_path, load_qti_bank(xml_path)

    @app.get("/qb-manage/bank/{bank_id}/manage", response_class=HTMLResponse)
    def qb_manage_bank(request: Request, bank_id: str, message: str = ""):
        session = require_admin(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)
        record, _, bank = load_authoritative_bank(bank_id)
        return templates.TemplateResponse(request, "qb_bank_manage.html", {
            "request": request, "bank": record, "metadata": bank.metadata,
            "display_name": session.get("display_name"), "is_admin": True,
            "message": message,
        })

    @app.get("/qb-manage/bank/{bank_id}/details", response_class=HTMLResponse)
    def qb_bank_details_form(request: Request, bank_id: str, message: str = ""):
        session = require_admin(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)
        record, _, bank = load_authoritative_bank(bank_id)
        return templates.TemplateResponse(request, "qb_bank_details.html", {
            "request": request, "bank": record, "metadata": bank.metadata,
            "display_name": session.get("display_name"), "is_admin": True,
            "message": message,
        })

    @app.post("/qb-manage/bank/{bank_id}/details")
    async def qb_bank_details_save(request: Request, bank_id: str):
        if not require_admin(request):
            raise HTTPException(status_code=403, detail="Administrator access required")
        record, xml_path, _ = load_authoritative_bank(bank_id)
        form = await request.form()
        title = str(form.get("title", "")).strip()
        updates = {
            "description": str(form.get("description", "")).strip(),
            "author": str(form.get("author", "")).strip(),
            "bank_version": str(form.get("bank_version", "")).strip(),
        }
        update_bank_metadata_in_qti(xml_path, title=title, metadata_updates=updates)
        refreshed = load_qti_bank(xml_path)
        store_question_bank_to_db(refreshed, filename=record["filename"])
        conn = get_conn()
        try:
            conn.execute("UPDATE quizzes SET title=? WHERE id=?", (title, bank_id))
            conn.commit()
        finally:
            conn.close()
        return RedirectResponse(url=f"/qb-manage/bank/{bank_id}/details?message=Bank+details+saved+to+XML", status_code=303)

    @app.get("/qb-manage/bank/{bank_id}/settings", response_class=HTMLResponse)
    def qb_bank_settings_form(request: Request, bank_id: str, message: str = ""):
        session = require_admin(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)
        record, _, bank = load_authoritative_bank(bank_id)
        return templates.TemplateResponse(request, "qb_test_settings.html", {
            "request": request, "bank": record, "metadata": bank.metadata,
            "display_name": session.get("display_name"), "is_admin": True,
            "message": message,
        })

    @app.post("/qb-manage/bank/{bank_id}/settings")
    async def qb_bank_settings_save(request: Request, bank_id: str):
        if not require_admin(request):
            raise HTTPException(status_code=403, detail="Administrator access required")
        record, xml_path, bank = load_authoritative_bank(bank_id)
        form = await request.form()
        passing = str(form.get("passing_score_percent", "80")).strip()
        try:
            passing_value = int(passing)
            if not 0 <= passing_value <= 100:
                raise ValueError
        except ValueError:
            raise HTTPException(status_code=400, detail="Passing score must be from 0 to 100")
        updates = {
            "default_test_name": str(form.get("default_test_name", "")).strip(),
            "test_description": str(form.get("test_description", "")).strip(),
            "time_limit_minutes": str(form.get("time_limit_minutes", "")).strip(),
            "default_test_question_count": str(form.get("default_test_question_count", "")).strip(),
            "passing_score_percent": str(passing_value),
            "score_basis": "percent",
            "shuffle_questions": "true" if form.get("shuffle_questions") else "false",
            "shuffle_choices": "true" if form.get("shuffle_choices") else "false",
            "allow_review": "true" if form.get("allow_review") else "false",
            "show_explanations": str(form.get("show_explanations", "quiz-only")),
        }
        update_bank_metadata_in_qti(xml_path, title=bank.title, metadata_updates=updates)
        refreshed = load_qti_bank(xml_path)
        store_question_bank_to_db(refreshed, filename=record["filename"])
        return RedirectResponse(url=f"/qb-manage/bank/{bank_id}/settings?message=Test+settings+saved+to+XML", status_code=303)

    @app.get("/qb-manage/create/step/{step}", response_class=HTMLResponse)
    def qb_create_step(request: Request, step: int):
        session = require_admin(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)
        if step not in {1, 2, 3}:
            return RedirectResponse(url="/qb-manage/create/step/1", status_code=303)
        return templates.TemplateResponse(request, "qb_create_wizard.html", {
            "request": request, "step": step, "display_name": session.get("display_name"), "is_admin": True,
        })

    @app.post("/qb-manage/create/finish")
    async def qb_create_finish(request: Request):
        if not require_admin(request):
            raise HTTPException(status_code=403, detail="Administrator access required")
        form = await request.form()
        bank_id = str(form.get("bank_id", "")).strip().upper()
        title = str(form.get("title", "")).strip()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{1,63}", bank_id):
            raise HTTPException(status_code=400, detail="Identifier must use 2-64 letters, numbers, underscores, or hyphens")
        conn = get_conn()
        try:
            if conn.execute("SELECT 1 FROM quizzes WHERE id=?", (bank_id,)).fetchone():
                raise HTTPException(status_code=409, detail="That bank identifier already exists")
        finally:
            conn.close()
        filename = f"{bank_id}.xml"
        xml_path = qti_dir / filename
        metadata = {
            "description": str(form.get("description", "")).strip(),
            "author": str(form.get("author", "")).strip(),
            "bank_version": str(form.get("bank_version", "1.0")).strip(),
            "default_test_name": str(form.get("default_test_name", title)).strip(),
            "test_description": str(form.get("test_description", "")).strip(),
            "time_limit_minutes": str(form.get("time_limit_minutes", "")).strip(),
            "default_test_question_count": str(form.get("default_test_question_count", "")).strip(),
            "passing_score_percent": str(form.get("passing_score_percent", "80")).strip(),
            "score_basis": "percent",
            "shuffle_questions": "true" if form.get("shuffle_questions") else "false",
            "shuffle_choices": "true" if form.get("shuffle_choices") else "false",
            "allow_review": "true" if form.get("allow_review") else "false",
            "show_explanations": str(form.get("show_explanations", "quiz-only")),
        }
        bank = create_empty_qti_bank(xml_path, identifier=bank_id, title=title, metadata=metadata)
        store_question_bank_to_db(bank, filename=filename)
        conn = get_conn()
        try:
            conn.execute("INSERT INTO quizzes (id, title, filename) VALUES (?, ?, ?)", (bank_id, title, filename))
            conn.commit()
        finally:
            conn.close()
        return RedirectResponse(url=f"/qb-manage/bank/{bank_id}/manage?message=Question+bank+created", status_code=303)

    @app.get("/qb-manage/banks", response_class=HTMLResponse)
    def qb_list_banks(request: Request):
        session = require_admin(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)
        conn = get_conn()
        try:
            banks = conn.execute(
                """SELECT bank_id, title, filename, question_count, imported_at
                   FROM question_banks ORDER BY title COLLATE NOCASE"""
            ).fetchall()
        finally:
            conn.close()
        return templates.TemplateResponse(
            request,
            "qb_list.html",
            {
                "request": request,
                "banks": banks,
                "display_name": session.get("display_name"),
                "is_admin": True,
            },
        )

    @app.get("/qb-manage/bank/{bank_id}", response_class=HTMLResponse)
    def qb_view_bank(
        request: Request,
        bank_id: str,
        domain: Optional[str] = None,
        type: Optional[str] = None,
    ):
        session = require_admin(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)
        conn = get_conn()
        try:
            bank = conn.execute(
                "SELECT bank_id, title, filename, question_count FROM question_banks WHERE bank_id=?",
                (bank_id,),
            ).fetchone()
            if not bank:
                raise HTTPException(status_code=404, detail="Question bank not found")
            sql = """SELECT id, qid, prompt, question_type, domain, objective
                     FROM questions WHERE bank_id=?"""
            params = [bank_id]
            if domain:
                sql += " AND domain=?"
                params.append(domain)
            if type:
                sql += " AND question_type=?"
                params.append(type)
            sql += " ORDER BY qid COLLATE NOCASE"
            questions = conn.execute(sql, params).fetchall()
            domains = [r[0] for r in conn.execute(
                "SELECT DISTINCT domain FROM questions WHERE bank_id=? AND domain<>'' ORDER BY domain",
                (bank_id,),
            ).fetchall()]
            types = [r[0] for r in conn.execute(
                "SELECT DISTINCT question_type FROM questions WHERE bank_id=? ORDER BY question_type",
                (bank_id,),
            ).fetchall()]
        finally:
            conn.close()
        return templates.TemplateResponse(
            request,
            "qb_view_bank.html",
            {
                "request": request,
                "bank": bank,
                "bank_id": bank["bank_id"],
                "bank_title": bank["title"],
                "questions": questions,
                "domains": domains,
                "types": types,
                "selected_domain": domain,
                "selected_type": type,
                "display_name": session.get("display_name"),
                "is_admin": True,
            },
        )

    @app.get("/qb-manage/question/{question_id}", response_class=HTMLResponse)
    def qb_edit_question_form(request: Request, question_id: int, message: str = "", error: str = ""):
        session = require_admin(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)
        question = get_question_by_id(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        conn = get_conn()
        try:
            domains = [r[0] for r in conn.execute(
                "SELECT DISTINCT domain FROM questions WHERE bank_id=? AND domain<>'' ORDER BY domain",
                (question["bank_id"],),
            ).fetchall()]
        finally:
            conn.close()
        return templates.TemplateResponse(
            request,
            "qb_edit_question.html",
            {
                "request": request,
                "question": question,
                "domains": domains,
                "question_types": ["true-false", "single-choice", "multiple-choice"],
                "display_name": session.get("display_name"),
                "message": message,
                "error": error,
                "is_admin": True,
            },
        )

    @app.post("/qb-manage/question/{question_id}")
    async def qb_save_question(request: Request, question_id: int):
        session = require_admin(request)
        if not session:
            raise HTTPException(status_code=403, detail="Administrator access required")
        question = get_question_by_id(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        form = await request.form()
        prompt = str(form.get("prompt", "")).strip()
        question_type = str(form.get("question_type", "single-choice"))
        explanation = str(form.get("explanation", "")).strip()
        domain = str(form.get("domain", "")).strip()
        objective = str(form.get("objective", "")).strip()
        if question_type not in {"true-false", "single-choice", "multiple-choice"}:
            raise HTTPException(status_code=400, detail="Unsupported question type")
        choices = {
            identifier: str(form.get(f"choice_{identifier}", "")).strip()
            for identifier in question["choices"]
        }
        if not prompt or len([v for v in choices.values() if v]) < 2:
            raise HTTPException(status_code=400, detail="A prompt and at least two choices are required")
        if question_type == "multiple-choice":
            correct_answers = [
                identifier for identifier in choices
                if form.get(f"correct_{identifier}") is not None
            ]
            if len(correct_answers) < 2:
                raise HTTPException(status_code=400, detail="Multiple Response requires at least two correct choices")
        else:
            correct = str(form.get("correct_answer", "")).strip()
            correct_answers = [correct] if correct else []
            if len(correct_answers) != 1 or correct_answers[0] not in choices:
                raise HTTPException(status_code=400, detail="Select one correct answer")

        conn = get_conn()
        try:
            bank = conn.execute(
                "SELECT filename FROM question_banks WHERE bank_id=?",
                (question["bank_id"],),
            ).fetchone()
        finally:
            conn.close()
        if not bank:
            raise HTTPException(status_code=500, detail="Question bank registry is missing")
        xml_path = qti_dir / bank["filename"]
        update_question_in_qti(
            xml_path,
            qid=question["qid"],
            prompt=prompt,
            choices=choices,
            correct_answers=correct_answers,
            question_type=question_type,
            explanation=explanation,
            domain=domain,
            objective=objective,
        )
        refreshed = load_qti_bank(xml_path)
        store_question_bank_to_db(refreshed, filename=bank["filename"])
        return RedirectResponse(
            url=f"/qb-manage/question/{question_id}?message=Question+saved+to+XML",
            status_code=303,
        )

    @app.post("/qb-manage/question/{question_id}/delete")
    def qb_delete_question(request: Request, question_id: int):
        # Deletion is intentionally deferred until XML-safe deletion and bank
        # minimum-size behavior are designed. Avoid a database-only delete.
        if not require_admin(request):
            raise HTTPException(status_code=403, detail="Administrator access required")
        return JSONResponse(
            {"status": "not_implemented", "detail": "XML-safe deletion is not enabled yet."},
            status_code=501,
        )

    @app.get("/qb-manage/api/questions", response_class=JSONResponse)
    def qb_api_questions(request: Request, bank_id: Optional[str] = None):
        if not require_admin(request):
            raise HTTPException(status_code=403, detail="Administrator access required")
        conn = get_conn()
        try:
            sql = "SELECT id, qid, bank_id, prompt, question_type, domain, objective FROM questions"
            params = []
            if bank_id:
                sql += " WHERE bank_id=?"
                params.append(bank_id)
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
        return {"questions": [dict(row) for row in rows]}
