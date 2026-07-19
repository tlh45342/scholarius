"""
FastAPI routes for Question Bank Management with Multi-Choice Support
Add these routes to app/main.py

These routes provide:
- Question bank listing with card view
- Question editing (Single-Choice, Multiple-Choice, True/False, Matching, Order Selection)
- Question creation and deletion
- Filtering by domain, objective, type
- API endpoints for AJAX operations
"""

from datetime import datetime
from typing import List, Optional
import json
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

# Import your existing modules
from app.db import get_conn
from app.parser_qti_extended import (
    get_questions_by_bank,
    get_question_by_id,
    store_question_bank_to_db,
)


def add_qb_routes(app: FastAPI, templates, is_admin, session_user):
    """
    Add question bank routes to the FastAPI app.
    Call this in main.py after app initialization.
    """

    @app.get("/qb-manage", response_class=HTMLResponse)
    def qb_manage_home(request: Request):
        """Question Bank Management home page."""
        session = session_user(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)

        # Get all question banks
        conn = get_conn()
        banks = conn.execute(
            "SELECT bank_id, title, question_count, imported_at FROM question_banks ORDER BY imported_at DESC"
        ).fetchall()
        conn.close()

        return templates.TemplateResponse(
            request,
            "qb_manage_home.html",
            {
                "request": request,
                "username": session.get("username"),
                "display_name": session.get("display_name") or session.get("username"),
                "banks": [dict(b) for b in banks],
            },
        )

    @app.get("/qb-manage/bank/{bank_id}", response_class=HTMLResponse)
    def qb_view_bank(request: Request, bank_id: str):
        """View all questions in a bank with filtering."""
        session = session_user(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)

        domain_filter = request.query_params.get("domain", "")
        question_type_filter = request.query_params.get("type", "")

        conn = get_conn()

        # Get bank info
        bank = conn.execute(
            "SELECT title, question_count FROM question_banks WHERE bank_id = ?",
            (bank_id,),
        ).fetchone()

        if not bank:
            conn.close()
            raise HTTPException(status_code=404, detail="Question bank not found")

        # Get unique domains and types for filter dropdowns
        domains = conn.execute(
            "SELECT DISTINCT domain FROM questions WHERE bank_id = ? ORDER BY domain",
            (bank_id,),
        ).fetchall()

        types = conn.execute(
            "SELECT DISTINCT question_type FROM questions WHERE bank_id = ? ORDER BY question_type",
            (bank_id,),
        ).fetchall()

        # Build query with filters
        query = """
            SELECT id, qid, prompt, question_type, correct_answer, domain, objective
            FROM questions
            WHERE bank_id = ?
        """
        params = [bank_id]

        if domain_filter:
            query += " AND domain = ?"
            params.append(domain_filter)

        if question_type_filter:
            query += " AND question_type = ?"
            params.append(question_type_filter)

        query += " ORDER BY id"

        questions = conn.execute(query, params).fetchall()
        conn.close()

        return templates.TemplateResponse(
            request,
            "qb_view_bank.html",
            {
                "request": request,
                "username": session.get("username"),
                "display_name": session.get("display_name") or session.get("username"),
                "bank_id": bank_id,
                "bank_title": bank[0],
                "questions": [dict(q) for q in questions],
                "domains": [d[0] for d in domains if d[0]],
                "types": [t[0] for t in types if t[0]],
                "selected_domain": domain_filter,
                "selected_type": question_type_filter,
            },
        )

    @app.get("/qb-manage/edit/{question_id}", response_class=HTMLResponse)
    def qb_edit_question(request: Request, question_id: int):
        """Edit a single question (single-choice or multiple-choice)."""
        session = session_user(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)

        question = get_question_by_id(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Get all domains/objectives for this bank for dropdowns
        conn = get_conn()
        domains = conn.execute(
            "SELECT DISTINCT domain FROM questions WHERE bank_id = ? ORDER BY domain",
            (question["bank_id"],),
        ).fetchall()
        conn.close()

        return templates.TemplateResponse(
            request,
            "qb_edit_question_multichoice.html",
            {
                "request": request,
                "username": session.get("username"),
                "display_name": session.get("display_name") or session.get("username"),
                "question": question,
                "domains": [d[0] for d in domains if d[0]],
                "question_types": ["single-choice", "multiple-choice", "true-false", "matching", "order-select"],
                "is_multichoice": question.get("question_type") == "multiple-choice",
            },
        )

    @app.post("/qb-manage/edit/{question_id}")
    async def qb_save_question(
        request: Request,
        question_id: int,
        prompt: str = Form(...),
        question_type: str = Form(...),
        correct_answer: str = Form(default=""),
        explanation: str = Form(default=""),
        domain: str = Form(default=""),
        objective: str = Form(default=""),
    ):
        """Save edits to a question (handles single-choice and multiple-choice)."""
        session = session_user(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)

        question = get_question_by_id(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Parse form data for choices
        form_data = await request.form()
        choices = {}
        for key in form_data:
            if key.startswith("choice_"):
                identifier = key.replace("choice_", "").upper()
                if identifier in form_data:
                    choices[identifier] = form_data[key]

        # Handle correct answer(s)
        correct_answers_list = None
        if question_type == "multiple-choice":
            # For multi-choice, collect all checked boxes
            correct_answers_list = []
            for letter in ["A", "B", "C", "D"]:
                key = f"correct_{letter}"
                if key in form_data:
                    correct_answers_list.append(letter)
            
            if not correct_answers_list:
                return RedirectResponse(
                    url=f"/qb-manage/edit/{question_id}?error=At+least+one+correct+answer+required",
                    status_code=303,
                )
            correct_answer = None
        else:
            # For single-choice, just one answer
            if not correct_answer:
                return RedirectResponse(
                    url=f"/qb-manage/edit/{question_id}?error=Correct+answer+required",
                    status_code=303,
                )

        conn = get_conn()
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()

        try:
            # Prepare correct_answers JSON if multi-choice
            correct_answers_json = None
            if correct_answers_list:
                correct_answers_json = json.dumps(correct_answers_list)

            # Update question
            cur.execute(
                """
                UPDATE questions
                SET prompt = ?, question_type = ?, correct_answer = ?, correct_answers = ?,
                    explanation = ?, domain = ?, objective = ?, updated_at = ?
                WHERE id = ?
                """,
                (prompt, question_type, correct_answer, correct_answers_json, 
                 explanation, domain, objective, now, question_id),
            )

            # Update choices
            cur.execute("DELETE FROM question_choices WHERE question_id = ?", (question_id,))

            for idx, (identifier, choice_text) in enumerate(choices.items()):
                if choice_text.strip():
                    cur.execute(
                        """
                        INSERT INTO question_choices 
                        (question_id, identifier, choice_text, position)
                        VALUES (?, ?, ?, ?)
                        """,
                        (question_id, identifier, choice_text, idx),
                    )

            conn.commit()

            return RedirectResponse(
                url=f"/qb-manage/bank/{question['bank_id']}", status_code=303
            )

        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()

    @app.post("/qb-manage/delete/{question_id}")
    def qb_delete_question(request: Request, question_id: int):
        """Delete a question."""
        session = session_user(request)
        if not session:
            return RedirectResponse(url="/login", status_code=303)

        question = get_question_by_id(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        conn = get_conn()
        cur = conn.cursor()

        try:
            cur.execute("DELETE FROM question_choices WHERE question_id = ?", (question_id,))
            cur.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            conn.commit()

            return RedirectResponse(
                url=f"/qb-manage/bank/{question['bank_id']}", status_code=303
            )

        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()

    @app.get("/qb-manage/api/questions")
    def qb_api_questions(
        request: Request,
        bank_id: Optional[str] = None,
        domain: Optional[str] = None,
        question_type: Optional[str] = None,
    ):
        """JSON API for getting filtered questions."""
        session = session_user(request)
        if not session:
            raise HTTPException(status_code=403, detail="Not authenticated")

        conn = get_conn()
        query = "SELECT id, qid, prompt, question_type, domain FROM questions WHERE 1=1"
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

        query += " ORDER BY id"

        questions = conn.execute(query, params).fetchall()
        conn.close()

        return JSONResponse([dict(q) for q in questions])
