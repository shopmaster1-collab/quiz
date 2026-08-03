# SECCIÓN: DOCKER BASE — Imagen oficial de Python
FROM python:3.12-slim

# SECCIÓN: DOCKER WORKDIR — Carpeta interna de la aplicación
WORKDIR /app

# SECCIÓN: DOCKER DEPENDENCIAS — Instalación de paquetes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# SECCIÓN: DOCKER CÓDIGO — Copia del proyecto
COPY . .

# SECCIÓN: DOCKER ARRANQUE — Servidor ASGI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
