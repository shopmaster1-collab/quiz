"""SECCIÓN: ADMIN SCHEMAS — Contratos para mantener productos y preguntas."""

from typing import Any
from pydantic import BaseModel, Field


class ProductUpsert(BaseModel):
    """SECCIÓN: PRODUCT UPSERT — Crea o actualiza información técnica/comercial."""
    sku: str = Field(min_length=2, max_length=100)
    name: str = Field(min_length=2, max_length=255)
    category: str
    short_description: str | None = None
    technical_profile: dict[str, Any] = Field(default_factory=dict)
    shopify_url: str | None = None
    shopify_variant_id: str | None = None
    image_url: str | None = None
    youtube_url: str | None = None
    tiktok_url: str | None = None
    manual_url: str | None = None
    active: bool = True


class QuestionUpsert(BaseModel):
    """SECCIÓN: QUESTION UPSERT — Crea o actualiza una pregunta."""
    code: str
    section_code: str
    title: str
    help_text: str | None = None
    answer_type: str = "single_choice"
    display_order: int
    active: bool = True


class OptionUpsert(BaseModel):
    """SECCIÓN: OPTION UPSERT — Agrega una opción y define el siguiente paso."""
    label: str
    value: str
    next_question_code: str | None = None
    icon: str | None = None
    display_order: int
    metadata_json: dict = Field(default_factory=dict)
