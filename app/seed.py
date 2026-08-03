"""SECCIÓN: SEED DATA — Carga idempotente de productos y árbol inicial."""

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.models import Product, QuizOption, QuizQuestion


PRODUCTS = [
    {
        "sku": "EASY-WATERPRO",
        "name": "EASY-WATERPRO",
        "category": "agua",
        "short_description": "Medidor local de nivel de agua con pantalla RGB y cable de 15 metros.",
        "technical_profile": {
            "measurement_target": "water_level",
            "compatible_deposits": ["tinaco"],
            "connection_sensor_receiver": "wired_15m",
            "wired_distance_m": 15,
            "local_display": True,
            "wifi_available": True,
            "wifi_included": False,
            "wifi_accessory_sku": "EASY-WIFI",
            "measurement_points": [0, 25, 50, 75, 100],
            "overflow_detection": True,
            "power": "5V_DC_2A_USB_C",
            "warranty_months": 12,
        },
        "active": True,
    },
    {
        "sku": "CONNECT-WATERPRO",
        "name": "CONNECT-WATERPRO",
        "category": "agua",
        "short_description": "Sistema inalámbrico de nivel de agua con pantalla, WiFi y alertas.",
        "technical_profile": {
            "measurement_target": "water_level",
            "compatible_deposits": ["tinaco", "cisterna", "aljibe", "deposito_elevado"],
            "connection_sensor_receiver": "rf",
            "rf_range_claimed_m": 500,
            "rf_range_status": "pending_confirmation",
            "local_display": True,
            "wifi_available": True,
            "wifi_included": True,
            "remote_monitoring": True,
            "valve_control_supported": True,
            "valve_included": False,
            "valve_accessory_sku": "EASY-VALVE-WATER",
            "warranty_months": 18,
        },
        "active": True,
    },
    {
        "sku": "EASY-GASPRO",
        "name": "EASY-GASPRO",
        "category": "gas",
        "short_description": "Medidor local de nivel para tanque estacionario con cable de 15 metros.",
        "technical_profile": {
            "measurement_target": "gas_lp",
            "compatible_tanks": ["tanque_estacionario"],
            "connection_sensor_receiver": "wired_15m",
            "wired_distance_m": 15,
            "local_display": True,
            "wifi_available": True,
            "wifi_included": False,
            "wifi_accessory_sku": "EASY-WIFI",
            "gas_leak_detection": False,
            "power": "5V_DC_2A_USB_C",
            "warranty_months": 12,
        },
        "active": True,
    },
    {
        "sku": "CONNECT-GASPRO",
        "name": "CONNECT-GASPRO",
        "category": "gas",
        "short_description": "Medición de nivel y detección de fugas para tanque estacionario de gas LP.",
        "technical_profile": {
            "measurement_target": "gas_lp",
            "compatible_tanks": ["tanque_estacionario"],
            "connection_sensor_receiver": "rf",
            "rf_range_claimed_m": 500,
            "local_display": True,
            "wifi_available": True,
            "wifi_included": True,
            "remote_monitoring": True,
            "gas_leak_detection": True,
            "valve_control_supported": True,
            "valve_included": False,
            "valve_accessory_sku": "EASY-VALVE-GAS",
            "warranty_months": 18,
        },
        "active": True,
    },
]


QUESTIONS = [
    {
        "code": "main_need",
        "section_code": "need",
        "title": "¿Qué necesitas monitorear o prevenir?",
        "help_text": "Elige la necesidad principal de tu casa, negocio o propiedad.",
        "answer_type": "single_choice",
        "display_order": 10,
        "options": [
            ("Nivel de agua", "water", "water_deposit", "💧"),
            ("Nivel de gas LP", "gas_level", "gas_tank_type", "🔥"),
            ("Fugas de gas LP", "gas_leak", "gas_tank_type", "⚠️"),
        ],
    },
    {
        "code": "water_deposit",
        "section_code": "water_installation",
        "title": "¿Dónde almacenas el agua?",
        "help_text": "Esto permite descartar equipos no documentados para ese depósito.",
        "answer_type": "single_choice",
        "display_order": 20,
        "options": [
            ("Tinaco", "tinaco", "distance", "🏠"),
            ("Cisterna", "cisterna", "distance", "⬇️"),
            ("Aljibe", "aljibe", "distance", "💧"),
            ("Depósito elevado", "elevated", "distance", "⬆️"),
            ("Otro depósito", "other", "distance", "❓"),
        ],
    },
    {
        "code": "gas_tank_type",
        "section_code": "gas_installation",
        "title": "¿Qué tipo de recipiente de gas utilizas?",
        "help_text": "Los productos analizados están diseñados para tanque estacionario.",
        "answer_type": "single_choice",
        "display_order": 30,
        "options": [
            ("Tanque estacionario", "stationary", "gas_feature", "🛢️"),
            ("Cilindro portátil", "portable", None, "⛔"),
            ("No estoy seguro", "unknown", None, "❓"),
        ],
    },
    {
        "code": "gas_feature",
        "section_code": "gas",
        "title": "¿Qué necesitas conocer o prevenir?",
        "help_text": "CONNECT-GASPRO agrega detección de fuga de gas LP.",
        "answer_type": "single_choice",
        "display_order": 40,
        "options": [
            ("Solo saber cuánto gas queda", "level_only", "distance", "📊"),
            ("Nivel y detección de fugas", "level_and_leak", "distance", "🛡️"),
            ("Principalmente detectar fugas", "leak_only", "distance", "⚠️"),
        ],
    },
    {
        "code": "distance",
        "section_code": "water",
        "title": "¿Qué distancia hay entre el sensor y el lugar donde quieres ver la información?",
        "help_text": "Los modelos EASY utilizan cable de 15 m; los CONNECT comunican módulos por radiofrecuencia.",
        "answer_type": "single_choice",
        "display_order": 50,
        "options": [
            ("Hasta 15 metros", "up_to_15m", "cable_possible", "📏"),
            ("Más de 15 metros", "more_than_15m", "cable_possible", "↔️"),
            ("No lo sé", "unknown", "cable_possible", "❓"),
        ],
    },
    {
        "code": "cable_possible",
        "section_code": "water",
        "title": "¿Puedes instalar un cable entre el sensor y la pantalla?",
        "help_text": "No necesitas conocer términos técnicos; piensa en el recorrido físico.",
        "answer_type": "single_choice",
        "display_order": 60,
        "options": [
            ("Sí, no hay problema", "yes", "monitoring_mode", "🔌"),
            ("Preferiría evitar cableado", "prefer_no", "monitoring_mode", "📡"),
            ("No es posible", "impossible", "monitoring_mode", "🚫"),
        ],
    },
    {
        "code": "monitoring_mode",
        "section_code": "connectivity",
        "title": "¿Dónde quieres consultar la información?",
        "help_text": "La consulta remota necesita internet y WiFi 2.4 GHz.",
        "answer_type": "single_choice",
        "display_order": 70,
        "options": [
            ("Solo en una pantalla local", "local", "wifi_available", "🖥️"),
            ("En pantalla y celular", "screen_and_phone", "wifi_available", "📱"),
            ("Desde cualquier lugar", "remote", "wifi_available", "🌎"),
        ],
    },
    {
        "code": "wifi_available",
        "section_code": "connectivity",
        "title": "¿Tienes WiFi 2.4 GHz en la propiedad?",
        "help_text": "Sin WiFi, los equipos compatibles pueden seguir operando localmente.",
        "answer_type": "single_choice",
        "display_order": 80,
        "options": [
            ("Sí", "yes", "dynamic_final", "✅"),
            ("No", "no", "dynamic_final", "❌"),
            ("No estoy seguro", "unknown", "dynamic_final", "❓"),
        ],
    },
    {
        "code": "water_control",
        "section_code": "features",
        "title": "¿También necesitas controlar el paso del agua?",
        "help_text": "Los accesorios de válvula se venden por separado.",
        "answer_type": "single_choice",
        "display_order": 90,
        "options": [
            ("No, solo monitoreo", "monitor_only", None, "👁️"),
            ("Sí, controlar una válvula", "valve", None, "🔄"),
            ("También controlar una bomba", "pump", None, "⚙️"),
        ],
    },
    {
        "code": "gas_valve",
        "section_code": "features",
        "title": "¿Quieres cerrar el paso del gas de forma remota o ante una fuga?",
        "help_text": "EASY-VALVE GAS se contempla como accesorio vendido por separado.",
        "answer_type": "single_choice",
        "display_order": 100,
        "options": [
            ("No", "no", None, "👁️"),
            ("Sí", "yes", None, "🛡️"),
            ("No estoy seguro", "unknown", None, "❓"),
        ],
    },
]


def resolve_dynamic_next(question_code: str, profile_hint: str) -> str:
    """SECCIÓN: SEED DYNAMIC NOTE — Documenta la transición final usada por el código."""
    return profile_hint


def seed() -> None:
    """SECCIÓN: SEED EXECUTION — Inserta registros faltantes sin duplicar."""
    with SessionLocal() as db:
        for data in PRODUCTS:
            if not db.scalar(select(Product).where(Product.sku == data["sku"])):
                db.add(Product(**data))
        db.commit()

        for item in QUESTIONS:
            question = db.scalar(select(QuizQuestion).where(QuizQuestion.code == item["code"]))
            if not question:
                question = QuizQuestion(
                    code=item["code"],
                    section_code=item["section_code"],
                    title=item["title"],
                    help_text=item["help_text"],
                    answer_type=item["answer_type"],
                    display_order=item["display_order"],
                    active=True,
                )
                db.add(question)
                db.flush()

                for order, (label, value, next_code, icon) in enumerate(item["options"], start=1):
                    # SECCIÓN: DYNAMIC FINAL TRANSITIONS — Se corrigen según rama.
                    if next_code == "dynamic_final":
                        next_code = None
                    db.add(
                        QuizOption(
                            question_id=question.id,
                            label=label,
                            value=value,
                            next_question_code=next_code,
                            icon=icon,
                            display_order=order,
                            metadata_json={},
                        )
                    )
        db.commit()

        # SECCIÓN: FINAL ROUTE PATCH — El mismo WiFi dirige a pregunta final según necesidad.
        # Esta transición se resuelve en runtime con el perfil; no en una sola fila.
        print("Seed completado correctamente.")


if __name__ == "__main__":
    seed()
