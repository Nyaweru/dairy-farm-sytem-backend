from flask import Blueprint, request, jsonify
from firebase_config import db
from datetime import datetime
import uuid

treatment_api = Blueprint("treatment_api", __name__)

# ✅ Create treatment record
@treatment_api.route("/api/treatments", methods=["POST"])
def add_treatment():
    try:
        data = request.json
        treatment_id = str(uuid.uuid4())

        treatment_data = {
            "id": treatment_id,
            "cow_id": data.get("cow"),  # from dropdown in frontend
            "disease": data.get("disease"),
            "drug": data.get("drug"),
            "dosage": data.get("dosage"),
            "method": data.get("method"),
            "vet": data.get("vet"),
            "notes": data.get("notes"),
            "date_given": data.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
            "next_followup": data.get("followUp"),  # YYYY-MM-DD string
            "createdAt": datetime.utcnow()
        }

        # Save treatment in Firestore
        db.collection("treatments").document(treatment_id).set(treatment_data)

        # If follow-up exists, create a notification
        if data.get("followUp"):
            notification_data = {
                "id": str(uuid.uuid4()),
                "cow_id": data.get("cow"),
                "title": "Follow-up Required",
                "message": f"Follow-up treatment for cow {data.get('cow')} scheduled on {data.get('followUp')}",
                "date": data.get("followUp"),
                "read": False,
                "createdAt": datetime.utcnow()
            }
            db.collection("notifications").document(notification_data["id"]).set(notification_data)

        return jsonify({"message": "✅ Treatment added successfully", "treatment": treatment_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Get all treatments
@treatment_api.route("/api/treatments", methods=["GET"])
def get_treatments():
    try:
        treatments_ref = db.collection("treatments").stream()
        treatments = [doc.to_dict() for doc in treatments_ref]
        return jsonify(treatments), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Get treatments by cow
@treatment_api.route("/api/treatments/cow/<cow_id>", methods=["GET"])
def get_treatments_by_cow(cow_id):
    try:
        treatments_ref = db.collection("treatments").where("cow_id", "==", cow_id).stream()
        treatments = [doc.to_dict() for doc in treatments_ref]
        return jsonify(treatments), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Update treatment
# ✅ Update treatment
@treatment_api.route("/api/treatments/<treatment_id>", methods=["PUT"])
def update_treatment(treatment_id):
    try:
        data = request.json
        db.collection("treatments").document(treatment_id).update(data)
        updated_doc = db.collection("treatments").document(treatment_id).get()
        return jsonify({"message": "✅ Treatment updated", "treatment": updated_doc.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ✅ Delete treatment
@treatment_api.route("/api/treatments/<treatment_id>", methods=["DELETE"])
def delete_treatment(treatment_id):
    try:
        db.collection("treatments").document(treatment_id).delete()
        return jsonify({"message": f"✅ Treatment {treatment_id} deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
