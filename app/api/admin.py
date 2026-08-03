"""SECCIÓN: ADMIN API — CRUD sencillo para productos, preguntas y opciones."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import require_admin
from app.models.models import Product, QuizOption, QuizQuestion
from app.schemas.admin import OptionUpsert, ProductUpsert, QuestionUpsert

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Administración"],
    dependencies=[Depends(require_admin)],
)


@router.get("/products")
def list_products(db: Session = Depends(get_db)) -> list[dict]:
    """SECCIÓN: ADMIN PRODUCT LIST — Lista productos para el panel."""
    products = db.scalars(select(Product).order_by(Product.name)).all()
    return [
        {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "category": product.category,
            "active": product.active,
            "shopify_url": product.shopify_url,
            "technical_profile": product.technical_profile,
        }
        for product in products
    ]


@router.post("/products")
def create_product(payload: ProductUpsert, db: Session = Depends(get_db)) -> dict:
    """SECCIÓN: ADMIN PRODUCT CREATE — Agrega un producto futuro."""
    if db.scalar(select(Product).where(Product.sku == payload.sku)):
        raise HTTPException(status_code=409, detail="El SKU ya existe.")
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"id": product.id, "sku": product.sku}


@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    payload: ProductUpsert,
    db: Session = Depends(get_db),
) -> dict:
    """SECCIÓN: ADMIN PRODUCT UPDATE — Actualiza producto existente."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    for field, value in payload.model_dump().items():
        setattr(product, field, value)

    db.commit()
    return {"updated": True, "id": product.id}


@router.get("/questions")
def list_questions(db: Session = Depends(get_db)) -> list[dict]:
    """SECCIÓN: ADMIN QUESTION LIST — Lista árbol con opciones."""
    questions = db.scalars(
        select(QuizQuestion)
        .options(selectinload(QuizQuestion.options))
        .order_by(QuizQuestion.display_order)
    ).all()
    return [
        {
            "id": question.id,
            "code": question.code,
            "section_code": question.section_code,
            "title": question.title,
            "answer_type": question.answer_type,
            "active": question.active,
            "options": [
                {
                    "id": option.id,
                    "label": option.label,
                    "value": option.value,
                    "next_question_code": option.next_question_code,
                }
                for option in question.options
            ],
        }
        for question in questions
    ]


@router.post("/questions")
def create_question(payload: QuestionUpsert, db: Session = Depends(get_db)) -> dict:
    """SECCIÓN: ADMIN QUESTION CREATE — Agrega una pregunta."""
    if db.scalar(select(QuizQuestion).where(QuizQuestion.code == payload.code)):
        raise HTTPException(status_code=409, detail="El código ya existe.")
    question = QuizQuestion(**payload.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return {"id": question.id, "code": question.code}


@router.post("/questions/{question_id}/options")
def create_option(
    question_id: int,
    payload: OptionUpsert,
    db: Session = Depends(get_db),
) -> dict:
    """SECCIÓN: ADMIN OPTION CREATE — Agrega respuesta y transición."""
    question = db.get(QuizQuestion, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada.")

    option = QuizOption(question_id=question_id, **payload.model_dump())
    db.add(option)
    db.commit()
    db.refresh(option)
    return {"id": option.id}
