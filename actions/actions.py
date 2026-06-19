"""
SmartGarage - Actions personnalisées Rasa
"""
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict
import logging

logger = logging.getLogger(__name__)

MAINTENANCE_INTERVALS = {
    "oil_change_km": 10000,
    "tire_rotation_km": 10000,
    "brake_pads_km": 40000,
    "air_filter_km": 15000,
    "spark_plugs_km": 30000,
    "timing_belt_km": 60000,
}

SERVICE_COSTS = {
    "oil_change": {"min": 60, "max": 120, "unit": "€"},
    "tire_rotation": {"min": 20, "max": 40, "unit": "€"},
    "brake_pads_front": {"min": 150, "max": 300, "unit": "€"},
    "battery": {"min": 100, "max": 250, "unit": "€"},
    "full_service": {"min": 250, "max": 500, "unit": "€"},
}

WARNING_LIGHTS = {
    "rouge": {
        "description": "🔴 DANGER - Arrêtez immédiatement !",
        "action": "Garez-vous en sécurité et appelez une assistance.",
        "examples": "Pression huile, température moteur critique.",
        "urgency": "immediate"
    },
    "orange": {
        "description": "🟠 ATTENTION - Intervention nécessaire sous peu",
        "action": "Prenez rendez-vous dans les 48h au garage.",
        "examples": "Voyant moteur, pression pneu (TPMS).",
        "urgency": "soon"
    },
    "jaune": {
        "description": "🟡 AVERTISSEMENT - À surveiller",
        "action": "Faites vérifier lors du prochain entretien.",
        "examples": "Lave-glace bas, filtre à particules.",
        "urgency": "monitor"
    },
    "bleu": {
        "description": "🔵 INFORMATION - Voyant de service",
        "action": "Aucune action urgente requise.",
        "examples": "Feux de route allumés.",
        "urgency": "info"
    },
    "vert": {
        "description": "🟢 NORMAL - Système actif",
        "action": "Tout va bien.",
        "examples": "Clignotant, régulateur de vitesse.",
        "urgency": "ok"
    },
}


class ValidateVehicleInfoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_vehicle_info_form"

    def validate_vehicle_brand(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value:
            return {"vehicle_brand": slot_value.strip().capitalize()}
        return {"vehicle_brand": None}

    def validate_vehicle_model(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value:
            return {"vehicle_model": slot_value.strip().capitalize()}
        return {"vehicle_model": None}

    def validate_vehicle_year(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value:
            digits = "".join(filter(str.isdigit, str(slot_value)))
            if digits and 1900 <= int(digits) <= 2026:
                return {"vehicle_year": digits}
        dispatcher.utter_message(
            text="Année invalide. Entrez une année entre 1900 et 2026, ex: 2015"
        )
        return {"vehicle_year": None}

    def validate_mileage(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value:
            digits = "".join(filter(str.isdigit, str(slot_value)))
            if digits and int(digits) > 0:
                return {"mileage": digits}
        dispatcher.utter_message(
            text="Kilométrage invalide. Entrez un nombre, ex: 85000"
        )
        return {"mileage": None}


class ActionCheckMaintenanceDue(Action):
    def name(self) -> Text:
        return "action_check_maintenance_due"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        vehicle_brand = tracker.get_slot("vehicle_brand") or "votre véhicule"
        vehicle_model = tracker.get_slot("vehicle_model") or ""
        vehicle_year  = tracker.get_slot("vehicle_year") or ""
        mileage_str   = tracker.get_slot("mileage")

        vehicle_name = f"{vehicle_brand} {vehicle_model}".strip()
        if vehicle_year:
            vehicle_name += f" ({vehicle_year})"

        if not mileage_str:
            dispatcher.utter_message(
                text=f"Pour {vehicle_name}, quel est le kilométrage actuel ?"
            )
            return []

        try:
            mileage = int("".join(filter(str.isdigit, str(mileage_str))))
        except (ValueError, TypeError):
            dispatcher.utter_message(text="Kilométrage invalide. Entrez un nombre, ex: 85000")
            return []

        checks = [
            ("Vidange d'huile",         MAINTENANCE_INTERVALS["oil_change_km"]),
            ("Rotation des pneus",       MAINTENANCE_INTERVALS["tire_rotation_km"]),
            ("Filtre à air",             MAINTENANCE_INTERVALS["air_filter_km"]),
            ("Plaquettes de frein",      MAINTENANCE_INTERVALS["brake_pads_km"]),
            ("Bougies d'allumage",       MAINTENANCE_INTERVALS["spark_plugs_km"]),
            ("Courroie de distribution", MAINTENANCE_INTERVALS["timing_belt_km"]),
        ]

        due_services      = []
        upcoming_services = []

        for service_name, interval in checks:
            remainder     = mileage % interval
            km_since_last = remainder if remainder != 0 else interval
            km_until_next = interval - remainder if remainder != 0 else 0

            if km_since_last >= interval * 0.9 or km_until_next == 0:
                due_services.append(f"⚠️ **{service_name}** — À faire maintenant")
            elif km_until_next <= 2000:
                upcoming_services.append(
                    f"🔔 **{service_name}** — Dans {km_until_next} km"
                )

        msg_parts = [
            f"📋 **Bilan de maintenance — {vehicle_name}**",
            f"Kilométrage actuel : **{mileage} km**\n",
        ]

        if due_services:
            msg_parts.append("**Entretiens à effectuer maintenant :**")
            msg_parts.extend(due_services)
        else:
            msg_parts.append("✅ Aucun entretien urgent n'est dû.")

        if upcoming_services:
            msg_parts.append("\n**Entretiens à venir :**")
            msg_parts.extend(upcoming_services)

        msg_parts.append("\nSouhaitez-vous prendre un rendez-vous taper un rendez-vous ?")
        dispatcher.utter_message(text="\n".join(msg_parts))
        return []


class ActionEstimateServiceCost(Action):
    def name(self) -> Text:
        return "action_estimate_service_cost"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        last_intent   = tracker.latest_message.get("intent", {}).get("name", "")
        vehicle_brand = tracker.get_slot("vehicle_brand") or ""

        cost_map = {
            "ask_oil_change":    ("Vidange d'huile", "oil_change"),
            "ask_tire_check":    ("Rotation/équilibrage pneus", "tire_rotation"),
            "ask_brake_check":   ("Remplacement plaquettes (avant)", "brake_pads_front"),
            "ask_battery_check": ("Remplacement batterie", "battery"),
        }

        if last_intent in cost_map:
            service_label, cost_key = cost_map[last_intent]
            cost = SERVICE_COSTS[cost_key]
        else:
            service_label = "Révision complète"
            cost = SERVICE_COSTS["full_service"]

        brand_note = ""
        premium_brands = ["BMW", "Mercedes", "Audi", "Porsche", "Lexus"]
        if vehicle_brand and any(b.lower() in vehicle_brand.lower() for b in premium_brands):
            brand_note = "\n⚠️ Pour votre marque premium, prévoir le haut de la fourchette."

        msg = (
            f"💰 **Estimation — {service_label}**\n\n"
            f"Fourchette : **{cost['min']} à {cost['max']} {cost['unit']}**\n"
            f"(Pièces + main d'œuvre incluses){brand_note}\n\n"
            "📞 Appelez-nous au **+33 1 23 45 67 89** pour un devis précis."
        )
        dispatcher.utter_message(text=msg)
        return []


class ActionDiagnoseWarningLight(Action):
    def name(self) -> Text:
        return "action_diagnose_warning_light"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Try to get color from entities first
        entities = tracker.latest_message.get("entities", [])
        color = None
        for entity in entities:
            if entity.get("entity") == "warning_light_color":
                color = entity.get("value", "").lower()
                break

        # Fallback: check if the raw text IS a color word
        if not color:
            raw_text = tracker.latest_message.get("text", "").lower().strip()
            known_colors = ["rouge", "orange", "jaune", "bleu", "vert"]
             # Also handle common variations
            color_map = {
                "rouge": "rouge",
                "red": "rouge",
                "orange": "orange",
                "jaune": "jaune",
                "yellow": "jaune",
                "bleu": "bleu",
                "blue": "bleu",
                "vert": "vert",
                "green": "vert",
            }
            if raw_text in color_map:
                color = color_map[raw_text]

        if not color or color not in WARNING_LIGHTS:
            dispatcher.utter_message(
                text="Quelle est la couleur du voyant ?\n🔴 Rouge | 🟠 Orange | 🟡 Jaune | 🔵 Bleu | 🟢 Vert"
            )
            return []

        light_info = WARNING_LIGHTS[color]
        msg = (
            f"{light_info['description']}\n\n"
            f"**Que faire :** {light_info['action']}\n"
            f"**Exemples :** {light_info['examples']}\n"
        )
        if light_info["urgency"] == "immediate":
            msg += "\n🚨 **Appelez immédiatement le garage ou une assistance.**"
        elif light_info["urgency"] == "soon":
            msg += "\n📞 Contactez-nous au +33 1 23 45 67 89."

        dispatcher.utter_message(text=msg)
        return []

class ActionCalculateNextOilChange(Action):

    def name(self) -> Text:
        return "action_calculate_next_oil_change"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        mileage_str = tracker.get_slot("mileage")

        if not mileage_str:
            dispatcher.utter_message(
                text="s'il vous plait saisser le mot 'vidange' pour commencer le bilan de maintenance"
            )
            return []

        try:
            mileage = int("".join(filter(str.isdigit, str(mileage_str))))
        except (ValueError, TypeError):
            dispatcher.utter_message(text="Kilométrage invalide. Ex: 85000")
            return []

        interval = MAINTENANCE_INTERVALS["oil_change_km"]
        next_oil_change = ((mileage // interval) + 1) * interval

        msg = (
            f"🛢️ **Prochaine vidange recommandée**\n\n"
            f"Kilométrage actuel : **{mileage} km**\n"
            f"Prochaine vidange à : **{next_oil_change} km**\n"
            f"Dans : **{next_oil_change - mileage} km**\n\n"
            "⚠️ Au minimum une fois par an même si vous roulez peu.\n"
            "Souhaitez-vous prendre rendez-vous ?"
        )
        dispatcher.utter_message(text=msg)
        return []
