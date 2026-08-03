"""SECCIÓN: QUIZ SERVICE — Navegación, sesiones y persistencia de respuestas."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session, selectinload

from app.models.models import QuizAnswer, QuizOption, QuizQuestion, QuizSession


TOTAL_VISIBLE_STEPS = 5


def get_question(db: Session, code: str) -> QuizQuestion:
    """SECCIÓN: QUESTION LOOKUP — Recupera pregunta activa con sus opciones."""
    question = db.scalar(
        select(QuizQuestion)
        .where(QuizQuestion.code == code, QuizQuestion.active.is_(True))
        .options(selectinload(QuizQuestion.options))
    )
    if not question:
        raise HTTPException(status_code=404, detail=f"Pregunta no encontrada: {code}")
    return question


def serialize_question(question: QuizQuestion) -> dict:
    """SECCIÓN: QUESTION SERIALIZER — Convierte ORM a JSON público."""
    return {
        "code": question.code,
        "section_code": question.section_code,
        "title": question.title,
        "help_text": question.help_text,
        "answer_type": question.answer_type,
        "options": [
            {"label": option.label, "value": option.value, "icon": option.icon}
            for option in question.options
        ],
    }


def start_session(db: Session) -> tuple[QuizSession, QuizQuestion]:
    """SECCIÓN: QUIZ START — Crea sesión y entrega la primera pregunta."""
    first_question = db.scalar(
        select(QuizQuestion)
        .where(QuizQuestion.active.is_(True))
        .order_by(QuizQuestion.display_order.asc())
        .options(selectinload(QuizQuestion.options))
    )
    if not first_question:
        raise HTTPException(status_code=503, detail="El Quiz no tiene preguntas configuradas.")

    session = QuizSession(
        status="started",
        current_question_code=first_question.code,
        profile_json={},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, first_question


def save_answer_and_get_next(
    db: Session,
    session_id: UUID,
    question_code: str,
    answer: str | list[str] | bool | int | float,
) -> tuple[QuizSession, QuizQuestion | None]:
    """SECCIÓN: QUIZ ANSWER — Guarda respuesta, actualiza perfil y avanza."""
    quiz_session = db.get(QuizSession, session_id)
    if not quiz_session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    if quiz_session.status == "completed":
        raise HTTPException(status_code=409, detail="La sesión ya fue completada.")

    question = get_question(db, question_code)

    # SECCIÓN: ANSWER REPLACE — Permite editar una respuesta sin duplicarla.
    db.execute(
        delete(QuizAnswer).where(
            QuizAnswer.session_id == session_id,
            QuizAnswer.question_code == question_code,
        )
    )
    db.add(
        QuizAnswer(
            session_id=session_id,
            question_code=question_code,
            answer_value={"value": answer},
        )
    )

    # SECCIÓN: PROFILE UPDATE — El código de pregunta se vuelve clave del perfil.
    profile = dict(quiz_session.profile_json or {})
    profile[question_code] = answer
    quiz_session.profile_json = profile

    # SECCIÓN: NEXT QUESTION — Para opción única toma la transición configurada.
    next_code = None
    if isinstance(answer, str):
        selected_option = db.scalar(
            select(QuizOption).where(
                QuizOption.question_id == question.id,
                QuizOption.value == answer,
            )
        )
        if not selected_option:
            raise HTTPException(status_code=422, detail="Opción inválida.")
        next_code = selected_option.next_question_code

        # SECCIÓN: DYNAMIC FINAL ROUTE — Después de WiFi dirige a función de agua o gas.
        if question_code == "wifi_available":
            main_need = profile.get("main_need")
            next_code = "water_control" if main_need == "water" else "gas_valve"

    # SECCIÓN: MULTIPLE CHOICE END — En MVP, respuestas múltiples usan ruta fija.
    if isinstance(answer, list):
        next_code = "water_control" if question.section_code == "water" else "gas_valve"

    if next_code:
        next_question = get_question(db, next_code)
        quiz_session.current_question_code = next_code
    else:
        next_question = None
        quiz_session.current_question_code = None
        quiz_session.status = "answers_completed"
        quiz_session.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(quiz_session)
    return quiz_session, next_question


def estimate_progress(question: QuizQuestion | None, completed: bool = False) -> int:
    """SECCIÓN: PROGRESS — Traduce sección técnica a una barra de cinco etapas."""
    if completed:
        return TOTAL_VISIBLE_STEPS

    section_to_step = {
        "need": 1,
        "water_installation": 2,
        "gas_installation": 2,
        "water": 3,
        "gas": 3,
        "connectivity": 4,
        "features": 4,
    }
    return section_to_step.get(question.section_code if question else "", 1)
