"""SECCIÓN: DEEPSEEK SERVICE — Redacta el resultado sin elegir productos."""

import json
from openai import OpenAI

from app.core.config import settings
from app.services.recommendation_service import Candidate


def fallback_summary(profile: dict, candidates: list[Candidate]) -> str:
    """SECCIÓN: AI FALLBACK — Explicación segura cuando DeepSeek no está disponible."""
    primary = candidates[0]
    reasons = " ".join(primary.reasons[:3])
    return (
        f"De acuerdo con tus respuestas, {primary.product.name} es la opción más compatible. "
        f"{reasons}"
    )


def generate_profile_summary(profile: dict, candidates: list[Candidate]) -> str:
    """SECCIÓN: AI SUMMARY — DeepSeek redacta usando candidatos ya validados."""
    if not settings.deepseek_api_key:
        return fallback_summary(profile, candidates)

    allowed_products = [
        {
            "sku": candidate.product.sku,
            "name": candidate.product.name,
            "score": candidate.score,
            "reasons": candidate.reasons,
            "technical_profile": candidate.product.technical_profile,
        }
        for candidate in candidates
    ]

    system_prompt = """
SECCIÓN: DEEPSEEK SYSTEM PROMPT — Reglas del redactor del diagnóstico.
Eres el redactor de un diagnóstico comercial de sensores MASTER.
El motor de reglas ya eligió los únicos productos permitidos.
No cambies el orden, no inventes SKU, funciones, compatibilidades, precios ni inventario.
Redacta en español de México, con tono claro y comercial.
Devuelve JSON con una única clave "profile_summary".
Extensión máxima: 110 palabras.
"""

    user_payload = {
        "profile": profile,
        "allowed_products": allowed_products,
        "required_json_example": {
            "profile_summary": "Texto personalizado del diagnóstico."
        },
    }

    try:
        client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        response = client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Genera el resultado en JSON:\n" + json.dumps(user_payload, ensure_ascii=False),
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=settings.deepseek_max_tokens,
            extra_body={"thinking": {"type": "disabled"}},
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        summary = parsed.get("profile_summary")
        if not summary:
            return fallback_summary(profile, candidates)
        return str(summary)
    except Exception:
        # SECCIÓN: AI ERROR HANDLING — El Quiz nunca se detiene por una falla externa.
        return fallback_summary(profile, candidates)
