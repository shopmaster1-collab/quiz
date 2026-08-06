"""Sincronización controlada del catálogo público de master.mx."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
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
_HREF_RE = re.compile(r"href=[\"']([^\"']+)[\"']", re.IGNORECASE)
_DOCUMENT_HINTS = ("manual", "ficha", "instructivo", "datasheet", "spec", ".pdf")


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


def _document_url(body_html: str | None) -> str | None:
    if not body_html:
        return None
    for href in _HREF_RE.findall(body_html):
        normalized = href.lower()
        if any(hint in normalized for hint in _DOCUMENT_HINTS):
            return urljoin(settings.shopify_store_url.rstrip("/") + "/", href)
    return None


def _category(product: dict) -> str:
    source = " ".join(str(product.get(key, "")) for key in ("title", "product_type", "tags", "handle")).lower()
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
    base = settings.shopify_store_url.rstrip("/") + "/"
    products: list[dict] = []
    with httpx.Client(
        timeout=settings.shopify_sync_timeout,
        follow_redirects=True,
        headers={"User-Agent": "MASTER-Solution-Quiz/1.1"},
    ) as client:
        for page in range(1, settings.shopify_sync_max_pages + 1):
            response = client.get(urljoin(base, "products.json"), params={"limit": 250, "page": page})
            response.raise_for_status()
            batch = response.json().get("products", [])
            if not isinstance(batch, list):
                raise ValueError("Shopify devolvió un catálogo con formato inesperado.")
            products.extend(batch)
            if len(batch) < 250:
                break
    return products


def sync_catalog(db: Session, deactivate_missing: bool = False) -> SyncReport:
    source_products = fetch_public_catalog()
    report = SyncReport(fetched=len(source_products))
    seen_skus: set[str] = set()
    synchronized_at = datetime.now(timezone.utc).isoformat()
    store_base = settings.shopify_store_url.rstrip("/") + "/"

    for source in source_products:
        variant = _variant(source)
        handle = str(source.get("handle") or "").strip()
        sku = str(variant.get("sku") or handle).strip()
        if not sku or not handle:
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
        product.short_description = _plain_text(source.get("body_html"))
        product.shopify_url = urljoin(store_base, f"products/{handle}")
        product.shopify_variant_id = str(variant.get("id") or "") or None
        product.image_url = images[0].get("src") if images else None
        product.manual_url = _document_url(source.get("body_html")) or product.manual_url
        product.active = bool(variant.get("available", True))

        profile = dict(product.technical_profile or {})
        previous_commerce = profile.get("commerce") or {}
        if created or previous_commerce.get("source") == "shopify_public_catalog":
            product.category = _category(source)

        variant_id = product.shopify_variant_id
        profile["commerce"] = {
            "price": variant.get("price"),
            "compare_at_price": variant.get("compare_at_price"),
            "currency": "MXN",
            "available": bool(variant.get("available", True)),
            "vendor": source.get("vendor"),
            "product_type": source.get("product_type"),
            "handle": handle,
            "shopify_product_id": source.get("id"),
            "variant_title": variant.get("title"),
            "cart_url": urljoin(store_base, f"cart/add?id={variant_id}") if variant_id else None,
            "source": "shopify_public_catalog",
            "synchronized_at": synchronized_at,
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
