"""SECCIÓN: QUIZ SCHEMAS — Valida solicitudes y respuestas públicas."""

from typing import Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class OptionOut(BaseModel):
    """SECCIÓN: OPTION OUTPUT — Opción visible en el Quiz."""
    label: str
    value: str
    icon: str | None = None


class QuestionOut(BaseModel):
    """SECCIÓN: QUESTION OUTPUT — Pregunta completa para el navegador."""
    code: str
    section_code: str
    title: str
    help_text: str | None = None
    answer_type: str
    options: list[OptionOut]


class QuizStartOut(BaseModel):
    """SECCIÓN: QUIZ START OUTPUT — Identificador y primera pregunta."""
    session_id: UUID
    progress_step: int
    total_steps: int
    question: QuestionOut


class QuizAnswerIn(BaseModel):
    """SECCIÓN: QUIZ ANSWER INPUT — Respuesta enviada por el usuario."""
    session_id: UUID
    question_code: str
    answer: str | list[str] | bool | int | float


class QuizAnswerOut(BaseModel):
    """SECCIÓN: QUIZ ANSWER OUTPUT — Siguiente pregunta o fin del árbol."""
    completed: bool
    progress_step: int
    total_steps: int
    question: QuestionOut | None = None


class ProductResultOut(BaseModel):
    """SECCIÓN: PRODUCT RESULT — Producto preparado para mostrarse y comprarse."""
    sku: str
    name: str
    short_description: str | None
    image_url: str | None
    shopify_url: str | None
    shopify_variant_id: str | None
    youtube_url: str | None
    tiktok_url: str | None
    manual_url: str | None
    score: int
    reasons: list[str]


class QuizResultOut(BaseModel):
    """SECCIÓN: QUIZ RESULT OUTPUT — Diagnóstico completo."""
    session_id: UUID
    profile_summary: str
    primary_product: ProductResultOut
    alternatives: list[ProductResultOut] = Field(default_factory=list)


class EmailCaptureIn(BaseModel):
    """SECCIÓN: EMAIL INPUT — Captura opcional con consentimientos separados."""
    session_id: UUID
    email: EmailStr
    consent_email: bool
    consent_marketing: bool = False
