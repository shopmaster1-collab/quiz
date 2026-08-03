"""SECCIÓN: MAIN APPLICATION — Arranque, rutas, CORS y archivos estáticos."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_router
from app.api.quiz import router as quiz_router
from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Motor escalonado de recomendación de sensores MASTER.",
)

# SECCIÓN: CORS MIDDLEWARE — Autoriza únicamente tiendas y ambientes definidos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# SECCIÓN: API ROUTERS — Endpoints públicos y administrativos.
app.include_router(quiz_router)
app.include_router(admin_router)

# SECCIÓN: STATIC MOUNT — CSS, JavaScript y recursos del Quiz.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health() -> dict:
    """SECCIÓN: HEALTH ENDPOINT — Render verifica la disponibilidad."""
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}


@app.get("/test/quiz", include_in_schema=False)
def quiz_test_page() -> FileResponse:
    """SECCIÓN: TEST PAGE — Página aislada para revisar el Quiz antes de Shopify."""
    return FileResponse(STATIC_DIR / "quiz-test.html")


@app.get("/admin", include_in_schema=False)
def admin_page() -> FileResponse:
    """SECCIÓN: ADMIN PAGE — Panel visual inicial."""
    return FileResponse(STATIC_DIR / "admin.html")
