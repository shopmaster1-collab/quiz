"""SECCIÓN: RECOMMENDATION ENGINE — Aplica exclusiones, compatibilidad y puntuación."""

from dataclasses import dataclass, field
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.models.models import Product, QuizRecommendation, QuizSession


@dataclass
class Candidate:
    """SECCIÓN: CANDIDATE STATE — Puntaje y razones de un producto."""
    product: Product
    score: int = 0
    excluded: bool = False
    reasons: list[str] = field(default_factory=list)


def add(candidate: Candidate, points: int, reason: str) -> None:
    """SECCIÓN: SCORE HELPER — Suma puntos y registra explicación."""
    candidate.score += points
    candidate.reasons.append(reason)


def exclude(candidate: Candidate, reason: str) -> None:
    """SECCIÓN: EXCLUSION HELPER — Elimina un producto por incompatibilidad crítica."""
    candidate.excluded = True
    candidate.reasons.append(reason)


def evaluate_products(db: Session, quiz_session: QuizSession) -> list[Candidate]:
    """SECCIÓN: EVALUATION — Evalúa los cuatro productos iniciales."""
    profile = quiz_session.profile_json or {}
    products = db.scalars(select(Product).where(Product.active.is_(True))).all()
    candidates = {product.sku: Candidate(product=product) for product in products}

    need = profile.get("main_need")
    distance = profile.get("distance")
    cable = profile.get("cable_possible")
    monitoring = profile.get("monitoring_mode")
    wifi = profile.get("wifi_available")

    # SECCIÓN: CATEGORY EXCLUSIONS — Agua y gas no se mezclan.
    for sku, candidate in candidates.items():
        target = candidate.product.technical_profile.get("measurement_target")
        if need == "water" and target != "water_level":
            exclude(candidate, "No corresponde a monitoreo de agua.")
        elif need in {"gas_level", "gas_leak"} and target != "gas_lp":
            exclude(candidate, "No corresponde a monitoreo de gas LP.")

    if need == "water":
        deposit = profile.get("water_deposit")
        control = profile.get("water_control")

        easy = candidates.get("EASY-WATERPRO")
        connect = candidates.get("CONNECT-WATERPRO")

        if easy and not easy.excluded:
            if deposit == "tinaco":
                add(easy, 30, "Compatible con tinaco.")
            else:
                add(easy, 5, "La documentación disponible confirma principalmente uso en tinaco.")
            if distance == "up_to_15m" and cable == "yes":
                add(easy, 35, "La instalación admite su cable de 15 metros.")
            if monitoring == "local":
                add(easy, 25, "La pantalla local cubre la forma de consulta elegida.")
            if monitoring in {"screen_and_phone", "remote"}:
                add(easy, 10, "Puede añadir conectividad mediante EASY-WIFI.")
                candidate_accessory = "Requiere EASY-WIFI para consulta remota."
                easy.reasons.append(candidate_accessory)

        if connect and not connect.excluded:
            if deposit in {"tinaco", "cisterna", "aljibe", "elevated", "other"}:
                add(connect, 30, "Compatible con el tipo de depósito indicado.")
            if distance == "more_than_15m" or cable in {"prefer_no", "impossible"}:
                add(connect, 35, "Evita tender cable entre el depósito y el receptor.")
            if monitoring in {"screen_and_phone", "remote"}:
                add(connect, 25, "Ofrece pantalla local y monitoreo mediante aplicación.")
            if control == "valve":
                add(connect, 10, "Admite control de válvula mediante accesorio.")
                connect.reasons.append("Requiere EASY-VALVE WATER, vendido por separado.")

    if need in {"gas_level", "gas_leak"}:
        gas_feature = profile.get("gas_feature")
        valve = profile.get("gas_valve")

        easy = candidates.get("EASY-GASPRO")
        connect = candidates.get("CONNECT-GASPRO")

        if easy and not easy.excluded:
            if gas_feature == "level_only":
                add(easy, 35, "Cubre la lectura local del nivel de gas.")
            if distance == "up_to_15m" and cable == "yes":
                add(easy, 30, "La instalación admite su cable de 15 metros.")
            if monitoring == "local":
                add(easy, 25, "La pantalla integrada cubre la consulta local.")
            if gas_feature in {"level_and_leak", "leak_only"}:
                exclude(easy, "Los documentos entregados no confirman detección de fugas.")

        if connect and not connect.excluded:
            if gas_feature in {"level_and_leak", "leak_only"} or need == "gas_leak":
                add(connect, 45, "Incluye medición y detección de fuga de gas LP.")
            else:
                add(connect, 25, "Permite medir el nivel del tanque estacionario.")
            if distance == "more_than_15m" or cable in {"prefer_no", "impossible"}:
                add(connect, 30, "Utiliza comunicación inalámbrica entre transmisor y receptor.")
            if monitoring in {"screen_and_phone", "remote"}:
                add(connect, 25, "Ofrece monitoreo local y remoto.")
            if valve == "yes":
                add(connect, 10, "Admite cierre con EASY-VALVE GAS.")
                connect.reasons.append("La válvula se vende por separado.")

    # SECCIÓN: WIFI CLARIFICATION — No excluye funcionamiento local.
    if wifi == "no":
        for candidate in candidates.values():
            if not candidate.excluded:
                candidate.reasons.append(
                    "Sin WiFi funcionará localmente; la consulta remota no estará disponible."
                )

    ranked = sorted(
        [candidate for candidate in candidates.values() if not candidate.excluded],
        key=lambda candidate: candidate.score,
        reverse=True,
    )

    if not ranked:
        raise ValueError("No existe un producto compatible con las respuestas actuales.")

    # SECCIÓN: RECOMMENDATION PERSISTENCE — Guarda hasta tres resultados.
    db.execute(
        delete(QuizRecommendation).where(
            QuizRecommendation.session_id == quiz_session.id
        )
    )
    for index, candidate in enumerate(ranked[:3], start=1):
        db.add(
            QuizRecommendation(
                session_id=quiz_session.id,
                product_id=candidate.product.id,
                score=candidate.score,
                ranking=index,
                reasons_json=candidate.reasons,
            )
        )
    db.commit()

    return ranked[:3]
