from flask import Blueprint, request, jsonify
from firebase_config import db
from datetime import datetime
import uuid

vaccination_api = Blueprint("vaccination_api", __name__)

# ✅ Create vaccination record
@vaccination_api.route("/api/vaccinations", methods=["POST"])
def add_vaccination():
    try:
        data = request.json
        vac_id = str(uuid.uuid4())

        vaccination_data = {
            "id": vac_id,
            "cow_id": data.get("cow_id"),
            "vaccine": data.get("vaccine"),
            "dosage": data.get("dosage"),
            "method": data.get("method"),
            "date_given": data.get("date_given", datetime.utcnow().strftime("%Y-%m-%d")),
            "next_booster": data.get("next_booster"),  # YYYY-MM-DD
            "vet": data.get("vet"),
            "notes": data.get("notes"),
            "createdAt": datetime.utcnow()
        }

        db.collection("vaccinations").document(vac_id).set(vaccination_data)

        # If next_booster exists, create a notification
        if vaccination_data["next_booster"]:
            notification_data = {
                "id": str(uuid.uuid4()),
                "cow_id": vaccination_data["cow_id"],
                "title": "Booster Due",
                "message": f"Booster for cow {vaccination_data['cow_id']} scheduled on {vaccination_data['next_booster']}",
                "date": vaccination_data["next_booster"],
                "read": False,
                "createdAt": datetime.utcnow()
            }
            db.collection("notifications").document(notification_data["id"]).set(notification_data)

        return jsonify({"message": "✅ Vaccination added successfully", "vaccination": vaccination_data}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Get all vaccinations
@vaccination_api.route("/api/vaccinations", methods=["GET"])
def get_vaccinations():
    try:
        vac_ref = db.collection("vaccinations").stream()
        vaccinations = []
        for doc in vac_ref:
            d = doc.to_dict()
            d["id"] = d.get("id", doc.id)
            vaccinations.append(d)
        return jsonify(vaccinations), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Get vaccinations by cow
@vaccination_api.route("/api/vaccinations/cow/<cow_id>", methods=["GET"])
def get_vaccinations_by_cow(cow_id):
    try:
        vac_ref = db.collection("vaccinations").where("cow_id", "==", cow_id).stream()
        vaccinations = [doc.to_dict() for doc in vac_ref]
        return jsonify(vaccinations), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Update vaccination
@vaccination_api.route("/api/vaccinations/<vac_id>", methods=["PUT"])
def update_vaccination(vac_id):
    try:
        data = request.json
        update_payload = {
            "cow_id": data.get("cow_id"),
            "vaccine": data.get("vaccine"),
            "dosage": data.get("dosage"),
            "method": data.get("method"),
            "date_given": data.get("date_given"),
            "next_booster": data.get("next_booster"),
            "vet": data.get("vet"),
            "notes": data.get("notes"),
            "updatedAt": datetime.utcnow()
        }

        update_payload = {k: v for k, v in update_payload.items() if v is not None}
        db.collection("vaccinations").document(vac_id).update(update_payload)

        updated_doc = db.collection("vaccinations").document(vac_id).get()
        updated_data = updated_doc.to_dict()
        updated_data["id"] = updated_data.get("id", vac_id)

        # If booster updated, create a notification
        if data.get("next_booster"):
            notification_data = {
                "id": str(uuid.uuid4()),
                "cow_id": data.get("cow_id"),
                "title": "Booster Due",
                "message": f"Booster for cow {data.get('cow_id')} scheduled on {data.get('next_booster')}",
                "date": data.get("next_booster"),
                "read": False,
                "createdAt": datetime.utcnow()
            }
            db.collection("notifications").document(notification_data["id"]).set(notification_data)

        return jsonify({"message": "✅ Vaccination updated", "vaccination": updated_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Delete vaccination
@vaccination_api.route("/api/vaccinations/<vac_id>", methods=["DELETE"])
def delete_vaccination(vac_id):
    try:
        db.collection("vaccinations").document(vac_id).delete()
        return jsonify({"message": f"✅ Vaccination {vac_id} deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🚨 Get vaccination alerts (boosters due within 7 days)
@vaccination_api.route("/api/vaccination-alerts", methods=["GET"])
def get_vaccination_alerts():
    try:
        vac_ref = db.collection("vaccinations").stream()
        alerts = []
        today = datetime.utcnow().date()

        for doc in vac_ref:
            data = doc.to_dict()
            if not data.get("next_booster"):
                continue

            try:
                booster_date = datetime.strptime(data["next_booster"], "%Y-%m-%d").date()
                diff_days = (booster_date - today).days

                if 0 <= diff_days <= 7:
                    alerts.append({
                        "id": data.get("id", doc.id),
                        "cow_id": data.get("cow_id"),
                        "vaccine": data.get("vaccine"),
                        "next_booster": data["next_booster"],
                        "daysRemaining": diff_days
                    })
            except Exception:
                continue  # skip invalid date format

        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
