"""SECCIÓN: QUIZ API — Endpoints públicos del diagnóstico."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import QuizSession
from app.schemas.quiz import (
    EmailCaptureIn,
    QuizAnswerIn,
    QuizAnswerOut,
    QuizResultOut,
    QuizStartOut,
)
from app.services.deepseek_service import generate_profile_summary
from app.services.quiz_service import (
    TOTAL_VISIBLE_STEPS,
    estimate_progress,
    save_answer_and_get_next,
    serialize_question,
    start_session,
)
from app.services.recommendation_service import evaluate_products

router = APIRouter(prefix="/api/v1/quiz", tags=["Quiz"])


@router.post("/start", response_model=QuizStartOut)
def start_quiz(db: Session = Depends(get_db)) -> dict:
    """SECCIÓN: QUIZ START ENDPOINT — Crea sesión y devuelve primera pregunta."""
    quiz_session, question = start_session(db)
    return {
        "session_id": quiz_session.id,
        "progress_step": estimate_progress(question),
        "total_steps": TOTAL_VISIBLE_STEPS,
        "question": serialize_question(question),
    }


@router.post("/answer", response_model=QuizAnswerOut)
def answer_quiz(payload: QuizAnswerIn, db: Session = Depends(get_db)) -> dict:
    """SECCIÓN: QUIZ ANSWER ENDPOINT — Guarda respuesta y avanza."""
    _, next_question = save_answer_and_get_next(
        db=db,
        session_id=payload.session_id,
        question_code=payload.question_code,
        answer=payload.answer,
    )
    completed = next_question is None
    return {
        "completed": completed,
        "progress_step": estimate_progress(next_question, completed=completed),
        "total_steps": TOTAL_VISIBLE_STEPS,
        "question": serialize_question(next_question) if next_question else None,
    }


@router.get("/{session_id}/result", response_model=QuizResultOut)
def get_result(session_id: UUID, db: Session = Depends(get_db)) -> dict:
    """SECCIÓN: QUIZ RESULT ENDPOINT — Ejecuta reglas y redacta diagnóstico."""
    quiz_session = db.get(QuizSession, session_id)
    if not quiz_session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    if quiz_session.status not in {"answers_completed", "completed"}:
        raise HTTPException(status_code=409, detail="La sesión todavía no está completa.")

    try:
        candidates = evaluate_products(db, quiz_session)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    summary = generate_profile_summary(quiz_session.profile_json, candidates)
    quiz_session.ai_summary = summary
    quiz_session.status = "completed"
    db.commit()

    def product_output(candidate):
        product = candidate.product
        return {
            "sku": product.sku,
            "name": product.name,
            "short_description": product.short_description,
            "image_url": product.image_url,
            "shopify_url": product.shopify_url,
            "shopify_variant_id": product.shopify_variant_id,
            "youtube_url": product.youtube_url,
            "tiktok_url": product.tiktok_url,
            "manual_url": product.manual_url,
            "score": candidate.score,
            "reasons": candidate.reasons,
        }

    return {
        "session_id": quiz_session.id,
        "profile_summary": summary,
        "primary_product": product_output(candidates[0]),
        "alternatives": [product_output(candidate) for candidate in candidates[1:]],
    }


@router.post("/email")
def capture_email(payload: EmailCaptureIn, db: Session = Depends(get_db)) -> dict:
    """SECCIÓN: EMAIL CAPTURE ENDPOINT — Guarda correo y consentimientos."""
    quiz_session = db.get(QuizSession, payload.session_id)
    if not quiz_session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    if not payload.consent_email:
        raise HTTPException(
            status_code=422,
            detail="Se requiere consentimiento para enviar el diagnóstico.",
        )

    quiz_session.email = str(payload.email)
    quiz_session.consent_email = payload.consent_email
    quiz_session.consent_marketing = payload.consent_marketing
    db.commit()

    return {
        "saved": True,
        "email_sent": False,
        "message": "Correo guardado. El envío se habilitará en la fase de correo transaccional.",
    }
