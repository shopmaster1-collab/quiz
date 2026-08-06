"""Sincronización controlada del catálogo público de master.mx.

La tienda es la fuente de verdad para datos volátiles: nombre comercial, precio,
imágenes, disponibilidad, URL y variante. La base del Quiz conserva únicamente
una copia operativa para búsqueda y presentación; las reglas de diagnóstico se
mantienen en ``technical_profile`` y están orientadas a necesidades/soluciones.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re
from urllib.parse import urljoin

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Product


_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


@dataclass(slots=True)
class SyncReport:
    fetched: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    deactivated: int = 0

    def as_dict(self) -> dict:
        return {
            "fetched": self.fetched,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "deactivated": self.deactivated,
        }


def _plain_text(value: str | None, limit: int = 1200) -> str | None:
    if not value:
        return None
    text = unescape(_TAG_RE.sub(" ", value))
    text = _SPACE_RE.sub(" ", text).strip()
    return text[:limit] or None


def _category(product: dict) -> str:
    source = " ".join(
        str(product.get(key, ""))
        for key in ("title", "product_type", "tags", "handle")
    ).lower()
    if any(token in source for token in ("gas", "lp", "monoxido", "monóxido")):
        return "gas"
    if any(token in source for token in ("agua", "water", "tinaco", "cisterna", "bomba", "flow")):
        return "agua"
    if any(token in source for token in ("energia", "energía", "electric", "corriente")):
        return "electricidad"
    if any(token in source for token in ("humo", "ruido", "co2", "ambiente", "aire")):
        return "ambiente"
    return "otras_soluciones"


def _variant(product: dict) -> dict:
    variants = product.get("variants") or []
    available = [item for item in variants if item.get("available")]
    return (available or variants or [{}])[0]


def fetch_public_catalog() -> list[dict]:
    """Descarga todas las páginas del endpoint público ``products.json``."""
    base = settings.shopify_store_url.rstrip("/") + "/"
    products: list[dict] = []
    page = 1
    with httpx.Client(timeout=settings.shopify_sync_timeout, follow_redirects=True) as client:
        while page <= settings.shopify_sync_max_pages:
            response = client.get(
                urljoin(base, "products.json"),
                params={"limit": 250, "page": page},
                headers={"User-Agent": "MASTER-Solution-Quiz/1.0"},
            )
            response.raise_for_status()
            batch = response.json().get("products", [])
            products.extend(batch)
            if len(batch) < 250:
                break
            page += 1
    return products


def sync_catalog(db: Session, deactivate_missing: bool = False) -> SyncReport:
    """Crea o actualiza la copia operativa del catálogo de Shopify."""
    source_products = fetch_public_catalog()
    report = SyncReport(fetched=len(source_products))
    seen_skus: set[str] = set()

    for source in source_products:
        variant = _variant(source)
        sku = str(variant.get("sku") or source.get("handle") or "").strip()
        if not sku:
            report.skipped += 1
            continue

        seen_skus.add(sku)
        product = db.scalar(select(Product).where(Product.sku == sku))
        created = product is None
        if created:
            product = Product(sku=sku, name=str(source.get("title") or sku), category=_category(source))
            db.add(product)

        images = source.get("images") or []
        product.name = str(source.get("title") or product.name)
        product.category = product.category or _category(source)
        product.short_description = _plain_text(source.get("body_html"))
        product.shopify_url = urljoin(settings.shopify_store_url.rstrip("/") + "/", f"products/{source.get('handle')}")
        product.shopify_variant_id = str(variant.get("id") or "") or None
        product.image_url = (images[0].get("src") if images else None)
        product.active = bool(variant.get("available", True))

        profile = dict(product.technical_profile or {})
        profile["commerce"] = {
            "price": variant.get("price"),
            "compare_at_price": variant.get("compare_at_price"),
            "available": bool(variant.get("available", True)),
            "vendor": source.get("vendor"),
            "product_type": source.get("product_type"),
            "handle": source.get("handle"),
            "source": "shopify_public_catalog",
        }
        product.technical_profile = profile
        report.created += int(created)
        report.updated += int(not created)

    if deactivate_missing:
        products = db.scalars(select(Product).where(Product.active.is_(True))).all()
        for product in products:
            commerce = (product.technical_profile or {}).get("commerce", {})
            if commerce.get("source") == "shopify_public_catalog" and product.sku not in seen_skus:
                product.active = False
                report.deactivated += 1

    db.commit()
    return report
