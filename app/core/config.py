"""SECCIÓN: CONFIGURACIÓN — Centraliza variables de entorno del sistema."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SECCIÓN: SETTINGS MODEL — Define y valida la configuración."""

    app_name: str = "MASTER Diagnóstico de Soluciones"
    app_env: str = "development"
    public_base_url: str = "http://localhost:8000"
    database_url: str
    allowed_origins: str = "http://localhost:8000"

    # SECCIÓN: SHOPIFY — Fuente de verdad para datos comerciales volátiles.
    shopify_store_url: str = "https://master.mx"
    shopify_sync_timeout: float = 30.0
    shopify_sync_max_pages: int = 10

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_max_tokens: int = 700

    admin_username: str = "admin"
    admin_password: str = "change-me"

    email_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """SECCIÓN: CORS PARSER — Convierte dominios separados por coma en lista."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        """
        SECCIÓN: DATABASE URL NORMALIZER
        FUNCIÓN: Convierte la URL de Render para usar psycopg versión 3.
        """
        raw_url = self.database_url.strip()

        if raw_url.startswith("postgresql+psycopg://"):
            return raw_url

        if raw_url.startswith("postgresql://"):
            return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

        if raw_url.startswith("postgres://"):
            return raw_url.replace("postgres://", "postgresql+psycopg://", 1)

        return raw_url


@lru_cache
def get_settings() -> Settings:
    """SECCIÓN: SETTINGS CACHE — Evita releer variables en cada solicitud."""
    return Settings()


settings = get_settings()
