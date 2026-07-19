"""
Scholarius Question Bank Editor Routes (Optional Integration)

These routes enable advanced question bank management including:
- Question listing by bank
- Question editing
- Question creation
- Question deletion

STATUS: Currently NOT integrated into main.py
INTEGRATION: See integration instructions below
"""

from datetime import datetime
from typing import Optional
import json
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from app.db import get_conn


def add_qb_routes(app: FastAPI, templates, is_admin, session_user):
    """
    Add question bank editor routes to the FastAPI app.
    
    Call this in main.py after app initialization:
    
        from app.routes_qb_editor import add_qb_routes
        add_qb_routes(app, templates, is_admin, session_user)
    """

    # ========================================================================
    # Question Bank Listing
    # ========================================================================

    @app.get("/qb-editor/banks", response_class=HTMLResponse)
    def qb_list_banks(request: Request):
        """List all imported question banks."""
        session = session_user(request)
        if not session or not is_admin(session):
            return RedirectResponse(url="/login", status_code=303)

        conn = get_conn()
        try:
            banks = conn.execute(
                "SELECT bank_id, title, question_count, imported_at FROM question_banks ORDER BY imported_at DESC"
            ).fetchall()
        finally:
            conn.close()

        return templates.TemplateResponse(
            request,
            "qb_list_banks.html",
            {
                "request": request,
                "banks": banks,
                "is_admin": True,
            },
        )

    # ========================================================================
    # View Questions in Bank
    # ========================================================================

    @app.get("/qb-editor/bank/{bank_id}", response_class=HTMLResponse)
    def qb_view_bank(
        request: Request,
        bank_id: str,
        domain: Optional[str] = None,
        question_type: Optional[str] = None,
    ):
        """View all questions in a bank with optional filtering."""
        session = session_user(request)
        if not session or not is_admin(session):
            return RedirectResponse(url="/login", status_code=303)

        conn = get_conn()
        try:
            # Get bank info
            bank = conn.execute(
                "SELECT bank_id, title, question_count FROM question_banks WHERE bank_id = ?",
                (bank_id,),
            ).fetchone()

            if not bank:
                raise HTTPException(status_code=404, detail="Bank not found")

            # Get questions with optional filters
            query = "SELECT id, prompt, question_type, domain, objective FROM questions WHERE bank_id = ?"
            params = [bank_id]

            if domain:
                query += " AND domain = ?"
                params.append(domain)

            if question_type:
                query += " AND question_type = ?"
                params.append(question_type)

            query += " ORDER BY id"

            questions = conn.execute(query, params).fetchall()

            # Get unique domains and types
            all_domains = conn.execute(
                "SELECT DISTINCT domain FROM questions WHERE bank_id = ? AND domain IS NOT NULL",
                (bank_id,),
            ).fetchall()

            all_types = conn.execute(
                "SELECT DISTINCT question_type FROM questions WHERE bank_id = ?",
                (bank_id,),
            ).fetchall()

        finally:
            conn.close()

        return templates.TemplateResponse(
            request,
            "qb_view_bank.html",
            {
                "request": request,
                "bank": bank,
                "questions": questions,
                "all_domains": [d[0] for d in all_domains],
                "all_types": [t[0] for t in all_types],
                "selected_domain": domain,
                "selected_type": question_type,
                "is_admin": True,
            },
        )

    # ========================================================================
    # Edit Question
    # ========================================================================

    @app.get("/qb-editor/question/{question_id}", response_class=HTMLResponse)
    def qb_edit_question_form(request: Request, question_id: int):
        """Display question editor form."""
        session = session_user(request)
        if not session or not is_admin(session):
            return RedirectResponse(url="/login", status_code=303)

        conn = get_conn()
        try:
            question = conn.execute(
                "SELECT id, prompt, question_type, correct_answer, explanation, domain, objective FROM questions WHERE id = ?",
                (question_id,),
            ).fetchone()

            if not question:
                raise HTTPException(status_code=404, detail="Question not found")

            choices = conn.execute(
                "SELECT identifier, choice_text FROM question_choices WHERE question_id = ? ORDER BY identifier",
                (question_id,),
            ).fetchall()

        finally:
            conn.close()

        return templates.TemplateResponse(
            request,
            "qb_edit_question.html",
            {
                "request": request,
                "question": question,
                "choices": choices,
                "is_admin": True,
            },
        )

    @app.post("/qb-editor/question/{question_id}")
    def qb_save_question(
        request: Request,
        question_id: int,
        prompt: str = Form(...),
        question_type: str = Form(default="single-choice"),
        correct_answer: str = Form(default=""),
        explanation: str = Form(default=""),
        domain: str = Form(default=""),
        objective: str = Form(default=""),
    ):
        """Save changes to a question."""
        session = session_user(request)
        if not session or not is_admin(session):
            raise HTTPException(status_code=403, detail="Admin access required")

        conn = get_conn()
        try:
            # Update question
            conn.execute(
                """UPDATE questions 
                   SET prompt = ?, question_type = ?, correct_answer = ?, 
                       explanation = ?, domain = ?, objective = ?
                   WHERE id = ?""",
                (prompt, question_type, correct_answer, explanation, domain, objective, question_id),
            )
            conn.commit()
        finally:
            conn.close()

        return RedirectResponse(url="/qb-editor/question/" + str(question_id), status_code=303)

    # ========================================================================
    # Delete Question
    # ========================================================================

    @app.post("/qb-editor/question/{question_id}/delete")
    def qb_delete_question(request: Request, question_id: int):
        """Delete a question."""
        session = session_user(request)
        if not session or not is_admin(session):
            raise HTTPException(status_code=403, detail="Admin access required")

        conn = get_conn()
        try:
            conn.execute("DELETE FROM question_choices WHERE question_id = ?", (question_id,))
            conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            conn.commit()
        finally:
            conn.close()

        return JSONResponse({"status": "deleted"})

    # ========================================================================
    # API Endpoints
    # ========================================================================

    @app.get("/qb-editor/api/questions", response_class=JSONResponse)
    def qb_api_questions(
        request: Request,
        bank_id: Optional[str] = None,
        domain: Optional[str] = None,
        question_type: Optional[str] = None,
    ):
        """JSON API for filtered questions."""
        session = session_user(request)
        if not session or not is_admin(session):
            raise HTTPException(status_code=403, detail="Admin access required")

        conn = get_conn()
        try:
            query = "SELECT id, prompt, question_type, domain, objective FROM questions WHERE 1=1"
            params = []

            if bank_id:
                query += " AND bank_id = ?"
                params.append(bank_id)

            if domain:
                query += " AND domain = ?"
                params.append(domain)

            if question_type:
                query += " AND question_type = ?"
                params.append(question_type)

            questions = conn.execute(query, params).fetchall()

        finally:
            conn.close()

        return {
            "questions": [
                {
                    "id": q[0],
                    "prompt": q[1],
                    "type": q[2],
                    "domain": q[3],
                    "objective": q[4],
                }
                for q in questions
            ]
        }
