"""SECCIÓN: SEGURIDAD — Protección inicial del panel administrativo."""

import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings

security = HTTPBasic()


def require_admin(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """SECCIÓN: ADMIN AUTH — Valida usuario y contraseña mediante comparación segura."""
    valid_user = secrets.compare_digest(credentials.username, settings.admin_username)
    valid_password = secrets.compare_digest(credentials.password, settings.admin_password)

    if not (valid_user and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales administrativas inválidas.",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
