# Actualización V1 — Diagnóstico de soluciones

## Cambios incluidos

- La aplicación se identifica como **MASTER Diagnóstico de Soluciones**.
- Shopify/master.mx funciona como fuente de verdad para nombre, descripción, imagen, precio, disponibilidad, variante y carrito.
- Nuevo endpoint administrativo: `POST /api/v1/admin/catalog/sync`.
- Nuevo resumen de consultas: `GET /api/v1/admin/analytics/summary`.
- Las reglas técnicas del Quiz permanecen separadas en `technical_profile`.
- Se conserva el almacenamiento de sesiones, respuestas y recomendaciones.

## Variables nuevas en Render

```env
SHOPIFY_STORE_URL=https://master.mx
SHOPIFY_SYNC_TIMEOUT=30
SHOPIFY_SYNC_MAX_PAGES=10
```

## Verificación después del despliegue

1. Abrir `/health` y confirmar `status: ok`.
2. Abrir `/docs` e iniciar sesión con las credenciales administrativas.
3. Ejecutar `POST /api/v1/admin/catalog/sync`.
4. Ejecutar `GET /api/v1/admin/products` y comprobar precio, imagen y URL dentro de `technical_profile.commerce`.
5. Ejecutar `GET /api/v1/admin/analytics/summary`.
6. Abrir `/test/quiz` y completar una sesión.

No usar `deactivate_missing=true` en la primera prueba.
