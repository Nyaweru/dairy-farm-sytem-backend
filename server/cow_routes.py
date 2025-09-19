# server/cow_routes.py
from flask import Blueprint, request, jsonify
from firebase_config import db, bucket
from datetime import datetime
import uuid

cow_api = Blueprint("cow_api", __name__)

# --- Util: Compute age in months
def compute_age_months(dob_str):
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    today = datetime.today()
    return (today.year - dob.year) * 12 + (today.month - dob.month)

# --- Util: Map category & status to type (feeding)
def map_category_to_type(category, daily_milk_avg, status):
    milk = daily_milk_avg or 0
    cat = (category or "").lower()
    stat = (status or "").lower()
    if cat == "calf":
        return "calf"
    if cat == "heifer":
        return "heifer" if milk == 0 else "milker"
    if cat == "cow":
        if milk > 0 and stat != "dry":
            return "milker"
        if stat == "dry":
            return "dry"
        return "dry"
    if cat == "bull":
        return "bull"
    if cat == "steer":
        return "steer"
    return "unknown"

# --- Route: Register a cow
@cow_api.route("/api/cows", methods=["POST"])
def register_cow():
    data = request.json
    try:
        tag_id = data.get("tag_id")
        if not tag_id:
            return jsonify({"error": "Tag ID is required"}), 400

        age_months = compute_age_months(data["dob"]) if data.get("dob") else None
        cow_type = map_category_to_type(
            data.get("category"), data.get("daily_milk_avg"), data.get("status")
        )

        cow_data = {
            "tag_id": tag_id,
            "name": data.get("name") or tag_id,
            "dob": data.get("dob"),
            "age_months": age_months,
            "breed": data.get("breed"),
            "color": data.get("color"),
            "gender": data.get("gender"),
            "category": data.get("category"),
            "status": data.get("status"),
            "type": cow_type,
            "origin": data.get("origin"),
            "location": data.get("location"),
            "sire": data.get("sire"),
            "dam": data.get("dam"),
            "daily_milk_avg": data.get("daily_milk_avg") or 0,
            "sick_flag": (data.get("status") or "").lower() == "sick",
            "dead_flag": (data.get("status") or "").lower() == "dead",
            "createdAt": datetime.utcnow()
        }

        db.collection("cows").document(tag_id).set(cow_data)
        return jsonify({"message": "✅ Cow registered successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Route: Get all cows
@cow_api.route("/api/cows", methods=["GET"])
def get_all_cows():
    try:
        cows_ref = db.collection("cows").stream()
        cow_list = [{**doc.to_dict(), "id": doc.id} for doc in cows_ref]
        return jsonify(cow_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Route: Update cow
@cow_api.route("/api/cows/<tag_id>", methods=["PUT"])
def update_cow(tag_id):
    try:
        data = request.json
        if "dob" in data:
            data["age_months"] = compute_age_months(data["dob"])
        if "category" in data or "daily_milk_avg" in data or "status" in data:
            data["type"] = map_category_to_type(
                data.get("category"), data.get("daily_milk_avg"), data.get("status")
            )
        # Update flags
        if "status" in data:
            status_lower = (data["status"] or "").lower()
            data["sick_flag"] = status_lower == "sick"
            data["dead_flag"] = status_lower == "dead"

        db.collection("cows").document(tag_id).update(data)
        return jsonify({"message": "✅ Cow updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Route: Delete cow
@cow_api.route("/api/cows/<tag_id>", methods=["DELETE"])
def delete_cow(tag_id):
    try:
        db.collection("cows").document(tag_id).delete()
        return jsonify({"message": f"✅ Cow {tag_id} deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
