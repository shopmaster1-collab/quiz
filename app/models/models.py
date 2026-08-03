"""SECCIÓN: MODELOS ORM — Define la estructura persistente del Quiz."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Product(Base):
    """SECCIÓN: PRODUCT MODEL — Producto técnico y sus enlaces comerciales."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text)
    technical_profile: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    shopify_url: Mapped[str | None] = mapped_column(Text)
    shopify_variant_id: Mapped[str | None] = mapped_column(String(100))
    image_url: Mapped[str | None] = mapped_column(Text)
    youtube_url: Mapped[str | None] = mapped_column(Text)
    tiktok_url: Mapped[str | None] = mapped_column(Text)
    manual_url: Mapped[str | None] = mapped_column(Text)

    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QuizQuestion(Base):
    """SECCIÓN: QUESTION MODEL — Pregunta configurable del diagnóstico."""

    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    section_code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    help_text: Mapped[str | None] = mapped_column(Text)
    answer_type: Mapped[str] = mapped_column(String(30), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    options: Mapped[list["QuizOption"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuizOption.display_order",
    )


class QuizOption(Base):
    """SECCIÓN: OPTION MODEL — Respuesta y siguiente paso del árbol."""

    __tablename__ = "quiz_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    next_question_code: Mapped[str | None] = mapped_column(String(100))
    icon: Mapped[str | None] = mapped_column(String(100))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    question: Mapped[QuizQuestion] = relationship(back_populates="options")


class QuizSession(Base):
    """SECCIÓN: SESSION MODEL — Estado y perfil acumulado del visitante."""

    __tablename__ = "quiz_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(30), default="started", nullable=False)
    current_question_code: Mapped[str | None] = mapped_column(String(100))
    profile_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    email: Mapped[str | None] = mapped_column(String(255))
    consent_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_marketing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_summary: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    answers: Mapped[list["QuizAnswer"]] = relationship(cascade="all, delete-orphan")
    recommendations: Mapped[list["QuizRecommendation"]] = relationship(cascade="all, delete-orphan")


class QuizAnswer(Base):
    """SECCIÓN: ANSWER MODEL — Respuesta individual de una sesión."""

    __tablename__ = "quiz_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_code: Mapped[str] = mapped_column(String(100), nullable=False)
    answer_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QuizRecommendation(Base):
    """SECCIÓN: RECOMMENDATION MODEL — Resultado ordenado del motor."""

    __tablename__ = "quiz_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    reasons_json: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped[Product] = relationship()
