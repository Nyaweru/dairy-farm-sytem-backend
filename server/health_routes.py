from flask import Blueprint, request, jsonify
from firebase_config import db
from datetime import datetime
import uuid

health_api = Blueprint("health_api", __name__)

# ✅ Comprehensive list of diseases that require flagging
FLAG_CONDITIONS = [
    # Infectious
    "mastitis", "foot rot", "brucellosis", "tuberculosis", "bovine viral diarrhea",
    "blackleg", "anthrax", "leptospirosis", "rabies", "pinkeye", "lumpy skin disease",
    "campylobacteriosis", "salmonellosis", "clostridial infection",

    # Metabolic / nutritional
    "milk fever", "ketosis", "bloat", "displaced abomasum", "grass tetany",
    "hypocalcemia", "ruminal acidosis",

    # Parasitic / protozoal
    "ticks", "helminthiasis", "coccidiosis", "trypanosomiasis",

    # Reproductive / miscellaneous
    "retained placenta", "uterine infection", "dystocia", "pneumonia",
]

# ✅ Utility: determine if a diagnosis should be flagged
def is_flagged(diagnosis: str) -> bool:
    diagnosis_lower = diagnosis.lower()
    return any(condition in diagnosis_lower for condition in FLAG_CONDITIONS)

# ✅ Utility: auto-create treatment
def create_treatment_from_healthcheck(health_data):
    try:
        treat_id = str(uuid.uuid4())
        treatment_data = {
            "id": treat_id,
            "cow": health_data.get("cow"),
            "cowname": health_data.get("cowname"),
            "disease": health_data.get("diagnosis"),
            "treatment": "Pending vet prescription",
            "medicine": "TBD",
            "dosage": "",
            "vet": health_data.get("vet"),
            "start_date": health_data.get("date"),
            "follow_up_date": "",
            "notes": f"Auto-created from health check. Symptoms: {health_data.get('symptoms')}",
            "createdAt": datetime.utcnow(),
        }
        db.collection("treatments").document(treat_id).set(treatment_data)
        return treatment_data
    except Exception as e:
        print("❌ Error auto-creating treatment:", str(e))
        return None

# ==================== CREATE HEALTH CHECK ====================
@health_api.route("/api/health", methods=["POST"])
def add_health_check():
    try:
        data = request.json
        hc_id = str(uuid.uuid4())

        # Flagging
        diagnosis = data.get("diagnosis") or ""
        flagged = is_flagged(diagnosis)

        health_data = {
            "id": hc_id,
            "cow": data.get("cow"),
            "cowname": data.get("cowname") or data.get("cow"),
            "date": data.get("date") or datetime.utcnow().strftime("%Y-%m-%d"),
            "temperature": data.get("temperature"),
            "weight": data.get("weight"),
            "symptoms": data.get("symptoms"),
            "diagnosis": data.get("diagnosis"),
            "vet": data.get("vet"),
            "notes": data.get("notes"),
            "flagged": flagged,
            "createdAt": datetime.utcnow(),
        }

        db.collection("healthchecks").document(hc_id).set(health_data)

        created_treatment = None
        if flagged:
            created_treatment = create_treatment_from_healthcheck(health_data)

            notification_data = {
                "id": str(uuid.uuid4()),
                "cow_id": health_data["cow"],
                "title": "Observation & Treatment Required",
                "message": f"Cow {health_data['cow']} diagnosed with {health_data['diagnosis']}. Treatment auto-created.",
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "read": False,
                "createdAt": datetime.utcnow(),
            }
            db.collection("notifications").document(notification_data["id"]).set(notification_data)

        return jsonify({
            "message": "✅ Health check added successfully",
            "healthcheck": health_data,
            "treatment": created_treatment
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== GET ALL HEALTH CHECKS ====================
@health_api.route("/api/health", methods=["GET"])
def get_health_checks():
    try:
        hc_ref = db.collection("healthchecks").stream()
        health_checks = []
        for doc in hc_ref:
            hc = doc.to_dict()
            hc["id"] = hc.get("id", doc.id)
            hc["cowname"] = hc.get("cowname", hc.get("cow", ""))
            hc["flagged"] = hc.get("flagged", False)
            health_checks.append(hc)
        return jsonify(health_checks), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== UPDATE HEALTH CHECK ====================
@health_api.route("/api/health/<hc_id>", methods=["PUT"])
def update_health_check(hc_id):
    try:
        data = request.json
        diagnosis = data.get("diagnosis") or ""
        flagged = is_flagged(diagnosis)

        update_payload = {
            "cow": data.get("cow"),
            "cowname": data.get("cowname") or data.get("cow"),
            "date": data.get("date"),
            "temperature": data.get("temperature"),
            "weight": data.get("weight"),
            "symptoms": data.get("symptoms"),
            "diagnosis": data.get("diagnosis"),
            "vet": data.get("vet"),
            "notes": data.get("notes"),
            "flagged": flagged,
            "updatedAt": datetime.utcnow(),
        }
        update_payload = {k: v for k, v in update_payload.items() if v is not None}

        db.collection("healthchecks").document(hc_id).update(update_payload)

        updated_doc = db.collection("healthchecks").document(hc_id).get()
        updated_data = updated_doc.to_dict()
        updated_data["id"] = updated_data.get("id", hc_id)
        updated_data["cowname"] = updated_data.get("cowname", updated_data.get("cow", ""))
        updated_data["flagged"] = updated_data.get("flagged", False)

        created_treatment = None
        if flagged:
            created_treatment = create_treatment_from_healthcheck(updated_data)

            notification_data = {
                "id": str(uuid.uuid4()),
                "cow_id": updated_data["cow"],
                "title": "Observation & Treatment Required",
                "message": f"Cow {updated_data['cow']} diagnosed with {updated_data['diagnosis']}. Treatment auto-created.",
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "read": False,
                "createdAt": datetime.utcnow(),
            }
            db.collection("notifications").document(notification_data["id"]).set(notification_data)

        return jsonify({
            "message": "✅ Health check updated",
            "healthcheck": updated_data,
            "treatment": created_treatment
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== DELETE HEALTH CHECK ====================
@health_api.route("/api/health/<hc_id>", methods=["DELETE"])
def delete_health_check(hc_id):
    try:
        # Delete associated treatment if exists
        treatments_ref = db.collection("treatments").where("cow", "==", hc_id).stream()
        for treat_doc in treatments_ref:
            db.collection("treatments").document(treat_doc.id).delete()

        # Delete health check
        db.collection("healthchecks").document(hc_id).delete()
        return jsonify({"message": f"✅ Health check {hc_id} and associated treatment deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
