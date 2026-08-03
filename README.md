# MASTER Sensor Quiz

Sistema de diagnóstico escalonado para recomendar sensores MASTER según las necesidades del usuario.

## 1. Arquitectura del proyecto

- **Frontend del Quiz:** HTML, CSS y JavaScript alojados por FastAPI.
- **Backend:** FastAPI.
- **Base de datos:** PostgreSQL en Render.
- **IA:** DeepSeek API.
- **Panel administrativo:** interfaz sencilla protegida con usuario y contraseña.
- **Página de pruebas:** `/test/quiz`.
- **Integración futura en Shopify:** carga del widget desde una página `pages`.

## 2. Estructura

```text
master_sensor_quiz/
├── app/
│   ├── api/                  # Endpoints del Quiz y administración
│   ├── core/                 # Configuración, seguridad y base de datos
│   ├── models/               # Tablas SQLAlchemy
│   ├── schemas/              # Validaciones Pydantic
│   ├── services/             # Recomendador, DeepSeek y lógica del Quiz
│   ├── static/               # JavaScript, CSS y páginas de prueba
│   ├── main.py               # Arranque de FastAPI
│   └── seed.py               # Carga inicial idempotente
├── alembic/                  # Migraciones de PostgreSQL
├── tests/                    # Pruebas automatizadas
├── render.yaml               # Blueprint de Render
├── requirements.txt
├── .env.example
└── Dockerfile
```

## 3. Ejecución local

### Requisitos

- Python 3.12+
- PostgreSQL 15+ o Docker
- Git

### Preparación

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instala dependencias:

```bash
pip install -r requirements.txt
```

Copia variables:

```bash
cp .env.example .env
```

En Windows puedes copiar manualmente `.env.example` como `.env`.

### Base local con Docker

```bash
docker compose up -d db
```

### Migraciones y datos iniciales

```bash
alembic upgrade head
python -m app.seed
```

### Ejecutar

```bash
uvicorn app.main:app --reload
```

Páginas:

- Quiz de prueba: `http://localhost:8000/test/quiz`
- Panel administrativo: `http://localhost:8000/admin`
- Documentación API: `http://localhost:8000/docs`
- Salud del sistema: `http://localhost:8000/health`

## 4. Variables obligatorias

Consulta `.env.example`.

No guardes claves reales en GitHub.

## 5. Flujo del Quiz

1. El navegador solicita el inicio del Quiz.
2. La API crea una sesión.
3. El usuario responde preguntas.
4. El backend decide la siguiente pregunta según las opciones configuradas.
5. Al finalizar, el motor aplica exclusiones y puntuaciones.
6. Selecciona producto principal y alternativas.
7. DeepSeek redacta una explicación usando únicamente productos aprobados.
8. La página muestra el resultado y los enlaces de compra.
9. El correo es opcional y se almacena con consentimiento.

## 6. Integración futura con Shopify

En una página de Shopify se insertará:

```html
<div id="master-sensor-quiz"></div>

<link
  rel="stylesheet"
  href="https://TU-SERVICIO.onrender.com/static/quiz-widget.css"
>

<script
  src="https://TU-SERVICIO.onrender.com/static/quiz-widget.js"
  data-api-base="https://TU-SERVICIO.onrender.com"
  data-container-id="master-sensor-quiz"
  defer>
</script>
```

La prueba debe hacerse primero con la URL de Render. Después puede asignarse un subdominio, por ejemplo:

```text
https://diagnostico.master.mx
```

## 7. Despliegue en Render

### Opción recomendada: Blueprint

1. Sube este repositorio a GitHub.
2. En Render selecciona **New > Blueprint**.
3. Conecta el repositorio.
4. Render leerá `render.yaml`.
5. Confirma la creación del Web Service y PostgreSQL.
6. Captura manualmente las variables secretas:
   - `DEEPSEEK_API_KEY`
   - `ADMIN_USERNAME`
   - `ADMIN_PASSWORD`
7. Actualiza `ALLOWED_ORIGINS` con el dominio real de Shopify.
8. Ejecuta una vez el comando de carga:
   ```bash
   python -m app.seed
   ```
   Puede ejecutarse desde Render Shell o agregarse temporalmente al build.

### Variables de Render

| Variable | Uso |
|---|---|
| `DATABASE_URL` | Render la genera desde PostgreSQL |
| `DEEPSEEK_API_KEY` | Clave privada de DeepSeek |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` |
| `ALLOWED_ORIGINS` | Dominios permitidos para CORS |
| `ADMIN_USERNAME` | Usuario del panel |
| `ADMIN_PASSWORD` | Contraseña del panel |
| `APP_ENV` | `production` |
| `PUBLIC_BASE_URL` | URL pública del servicio |

## 8. Datos pendientes antes de producción

- URL real de cada producto Shopify.
- `variant_id` de cada producto.
- Imágenes oficiales.
- Videos de YouTube o TikTok.
- Confirmación de alcance de CONNECT-WATERPRO.
- Confirmación de compatibilidad de EASY-WIFI.
- Confirmación del nombre actual de la aplicación móvil.
- Confirmación de accesorios y kits.
