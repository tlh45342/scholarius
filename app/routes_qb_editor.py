"""Question-bank editor routes.

XML remains the authoritative question-bank representation. SQLite is an
editable index. Every successful editor save is written back to XML before the
index is refreshed.
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from app.db import get_conn
from app.parser_qti import (
    get_question_by_id,
    load_qti_bank,
    store_question_bank_to_db,
    update_question_in_qti,
)


def add_qb_routes(app: FastAPI, templates, is_admin, session_user, qti_dir: Path):
    def require_admin(request: Request):
        session = session_user(request)
        if not session or not is_admin(session):
            return None
        return session

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
