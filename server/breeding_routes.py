from flask import Blueprint, request, jsonify
from firebase_config import db
from datetime import datetime, timedelta
import uuid

breeding_api = Blueprint("breeding_api", __name__)

# ✅ Utility to auto-calc expected birth and repeat date
def calculate_dates(breeding_date_str, method="natural"):
    breeding_date = datetime.strptime(breeding_date_str, "%Y-%m-%d")
    expected_birth = breeding_date + timedelta(days=283)  # gestation ~283 days
    repeat_date = None
    if method.lower() == "ai":
        repeat_date = breeding_date + timedelta(days=21)
    return expected_birth.strftime("%Y-%m-%d"), repeat_date.strftime("%Y-%m-%d") if repeat_date else ""

# ✅ Check inbreeding: cow and bull should not share sire or dam
def check_inbreeding(cow, bull):
    if not cow or not bull:
        return False
    return (cow.get("sire") and bull.get("sire") and cow["sire"] == bull["sire"]) or \
           (cow.get("dam") and bull.get("dam") and cow["dam"] == bull["dam"])

# ✅ Create breeding record
@breeding_api.route("/api/breeding", methods=["POST"])
def add_breeding():
    try:
        data = request.json
        rec_id = str(uuid.uuid4())

        # Fetch cow & bull details from cows collection if IDs provided
        cow_doc = db.collection("cows").document(data.get("cow")).get()
        cow_data = cow_doc.to_dict() if cow_doc.exists else {}

        bull_doc = None
        bull_data = {}
        if data.get("bull") and data.get("method") != "AI":
            bull_doc = db.collection("cows").document(data.get("bull")).get()
            bull_data = bull_doc.to_dict() if bull_doc.exists else {}

        expected_birth, repeat_date = calculate_dates(
            data.get("breedingDate"),
            data.get("method", "natural")
        )

        record = {
            "id": rec_id,
            "cow": data.get("cow"),
            "cowname": cow_data.get("cowid") or cow_data.get("name") or data.get("cowname"),
            "dam": cow_data.get("dam") or data.get("dam"),
            "sire": cow_data.get("sire") or data.get("sire"),
            "method": data.get("method"),
            "bull": data.get("bull") or "",
            "bullDam": bull_data.get("dam") or data.get("bullDam", ""),
            "bullSire": bull_data.get("sire") or data.get("bullSire", ""),
            "breedingDate": data.get("breedingDate"),
            "expectedBirth": expected_birth,
            "repeatDate": repeat_date,
            "vet": data.get("vet"),
            "notes": data.get("notes"),
            "createdAt": datetime.utcnow(),
        }

        # Inbreeding check
        if check_inbreeding(cow_data, {"sire": record["bullSire"], "dam": record["bullDam"]}):
            record["inbreedingWarning"] = True

        db.collection("breeding").document(rec_id).set(record)
        return jsonify({"message": "Breeding record added", "record": record}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Get all breeding records
@breeding_api.route("/api/breeding", methods=["GET"])
def get_breeding():
    try:
        recs_ref = db.collection("breeding").stream()
        records = []
        today = datetime.utcnow()
        for doc in recs_ref:
            rec = doc.to_dict()
            rec["id"] = rec.get("id", doc.id)

            # Alert if expected birth is within 7 days
            if rec.get("expectedBirth"):
                expected = datetime.strptime(rec["expectedBirth"], "%Y-%m-%d")
                delta = (expected - today).days
                rec["deliveryAlert"] = delta <= 7 and delta >= 0
            else:
                rec["deliveryAlert"] = False

            records.append(rec)
        return jsonify(records), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Update breeding record
@breeding_api.route("/api/breeding/<rec_id>", methods=["PUT"])
def update_breeding(rec_id):
    try:
        data = request.json
        update_payload = {}

        for field in [
            "cow", "cowname", "dam", "sire", "method",
            "bull", "bullDam", "bullSire", "breedingDate",
            "expectedBirth", "repeatDate", "vet", "notes"
        ]:
            if field in data:
                update_payload[field] = data[field]

        # Recalculate dates if breedingDate changed
        if "breedingDate" in update_payload or "method" in update_payload:
            method = update_payload.get("method", data.get("method"))
            date = update_payload.get("breedingDate", data.get("breedingDate"))
            expected_birth, repeat_date = calculate_dates(date, method)
            update_payload["expectedBirth"] = expected_birth
            update_payload["repeatDate"] = repeat_date

        db.collection("breeding").document(rec_id).update(update_payload)
        updated_doc = db.collection("breeding").document(rec_id).get()
        updated_data = updated_doc.to_dict()
        updated_data["id"] = updated_data.get("id", rec_id)
        return jsonify({"message": "Breeding record updated", "record": updated_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Delete breeding record
@breeding_api.route("/api/breeding/<rec_id>", methods=["DELETE"])
def delete_breeding(rec_id):
    try:
        db.collection("breeding").document(rec_id).delete()
        return jsonify({"message": f"Breeding record {rec_id} deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
