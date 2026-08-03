"""Initial schema.

SECCIÓN: MIGRACIÓN INICIAL — Crea productos, preguntas, sesiones y resultados.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """SECCIÓN: MIGRACIÓN UPGRADE — Crea todas las tablas iniciales."""
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("technical_profile", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("shopify_url", sa.Text(), nullable=True),
        sa.Column("shopify_variant_id", sa.String(100), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("youtube_url", sa.Text(), nullable=True),
        sa.Column("tiktok_url", sa.Text(), nullable=True),
        sa.Column("manual_url", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("section_code", sa.String(100), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("help_text", sa.Text(), nullable=True),
        sa.Column("answer_type", sa.String(30), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "quiz_options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("value", sa.String(100), nullable=False),
        sa.Column("next_question_code", sa.String(100), nullable=True),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_table(
        "quiz_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("current_question_code", sa.String(100), nullable=True),
        sa.Column("profile_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("consent_email", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consent_marketing", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "quiz_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_code", sa.String(100), nullable=False),
        sa.Column("answer_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "quiz_recommendations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("ranking", sa.Integer(), nullable=False),
        sa.Column("reasons_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_quiz_answers_session_id", "quiz_answers", ["session_id"])
    op.create_index("ix_recommendations_session_id", "quiz_recommendations", ["session_id"])


def downgrade() -> None:
    """SECCIÓN: MIGRACIÓN DOWNGRADE — Elimina las tablas en orden seguro."""
    op.drop_index("ix_recommendations_session_id", table_name="quiz_recommendations")
    op.drop_index("ix_quiz_answers_session_id", table_name="quiz_answers")
    op.drop_table("quiz_recommendations")
    op.drop_table("quiz_answers")
    op.drop_table("quiz_sessions")
    op.drop_table("quiz_options")
    op.drop_table("quiz_questions")
    op.drop_table("products")
