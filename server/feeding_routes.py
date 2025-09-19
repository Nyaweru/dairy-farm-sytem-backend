from flask import Blueprint, jsonify, request
import firebase_admin
from firebase_admin import firestore
from datetime import datetime

db = firestore.client()
feeding_bp = Blueprint("feeding", __name__)

def calculate_feeding(cow, milk_record=None):
    cow_type = cow.get("type")
    cow_name = cow.get("name")
    dob = cow.get("dob")
    today = datetime.today()
    feeding_plan = {}

    # Age in months
    age_months = None
    if dob:
        dob_date = datetime.strptime(dob, "%Y-%m-%d")
        age_months = (today.year - dob_date.year) * 12 + (today.month - dob_date.month)

    if cow_type == "milker":
        production = milk_record.get("total") if milk_record else 0
        dairy_meal = max((production - 7) / 2, 0)
        feeding_plan = {
            "cow": cow_name,
            "category": "Milker",
            "dairy_meal_kg": round(dairy_meal, 2),
            "salt_g": 250,
            "silage_kg": 5,
            "hay": "Unlimited",
            "notes": "Formula (Production-7)/2 applied"
        }
    elif cow_type == "calf" and age_months is not None:
        if age_months == 0:
            feeding_plan = {
                "cow": cow_name,
                "category": "Calf (1st month)",
                "milk_l": 6,
                "calf_meal_kg": 0,
                "water_l": 0,
                "hay": 0,
                "salt_g": 100,
                "notes": "Newborn calf feeding"
            }
        elif age_months == 1:
            feeding_plan = {
                "cow": cow_name,
                "category": "Calf (2nd month)",
                "milk_l": 4,
                "calf_meal_kg": 1,
                "water_l": 1,
                "hay": 1,
                "salt_g": 100,
                "notes": "Transition stage"
            }
        elif age_months == 2:
            feeding_plan = {
                "cow": cow_name,
                "category": "Calf (3rd month)",
                "milk_l": 2,
                "calf_meal_kg": 2,
                "water_l": 1,
                "hay": 1,
                "salt_g": 100,
                "notes": "Weaning stage"
            }
        else:
            feeding_plan = {
                "cow": cow_name,
                "category": f"Calf ({age_months+1} months+)",
                "milk_l": 0,
                "calf_meal_kg": 4,
                "water_l": 2,
                "hay": 1,
                "salt_g": 100,
                "notes": "Post-weaning, up to insemination"
            }
    elif cow_type == "dry":
        feeding_plan = {
            "cow": cow_name,
            "category": "Dry Cow",
            "silage_kg": 5,
            "hay": 1,
            "salt_g": 200,
            "notes": "Dry cow feeding"
        }

    feeding_plan["date"] = today.strftime("%Y-%m-%d")
    return feeding_plan

# Generate feeding for a single cow
@feeding_bp.route("/generate/<cow_id>", methods=["POST"])
def generate_single(cow_id):
    cow_doc = db.collection("cows").document(cow_id).get()
    if not cow_doc.exists:
        return jsonify({"error": "Cow not found"}), 404
    cow = cow_doc.to_dict()
    milk_record_doc = db.collection("milk_records").document(cow_id).get()
    milk_record = milk_record_doc.to_dict() if milk_record_doc.exists else None

    plan = calculate_feeding(cow, milk_record)
    db.collection("feeding_records").add(plan)
    plan["id"] = "temp"  # optional, Firestore auto-generated ID
    return jsonify({"message": "Feeding record generated", "record": plan}), 201

# Generate for all cows (already in your code)
@feeding_bp.route("/generate_and_save", methods=["POST"])
def generate_and_save():
    cows_ref = db.collection("cows").stream()
    milk_records_ref = db.collection("milk_records").stream()
    milk_map = {m.id: m.to_dict() for m in milk_records_ref}
    feeding_records = []

    for cow_doc in cows_ref:
        cow = cow_doc.to_dict()
        cow_id = cow_doc.id
        milk_record = milk_map.get(cow_id)
        plan = calculate_feeding(cow, milk_record)
        if plan:
            db.collection("feeding_records").add(plan)
            feeding_records.append(plan)

    return jsonify({"message": "Feeding records generated and saved", "records": feeding_records}), 201

# Fetch all feeding records
@feeding_bp.route("/records", methods=["GET"])
def get_feeding_records():
    records = []
    docs = db.collection("feeding_records").order_by("date", direction=firestore.Query.DESCENDING).stream()
    for doc in docs:
        record = doc.to_dict()
        record["id"] = doc.id
        records.append(record)
    return jsonify(records), 200

# Delete record
@feeding_bp.route("/records/<record_id>", methods=["DELETE"])
def delete_record(record_id):
    db.collection("feeding_records").document(record_id).delete()
    return jsonify({"message": f"Feeding record {record_id} deleted"}), 200

# Stock summary
@feeding_bp.route("/stock_summary", methods=["GET"])
def stock_summary():
    totals = {}
    docs = db.collection("feeding_records").stream()
    for doc in docs:
        record = doc.to_dict()
        # iterate over feed items
        for key, value in record.items():
            if key in ["cow", "category", "notes", "date", "id"]:
                continue
            if isinstance(value, (int, float)):
                if key not in totals:
                    totals[key] = {"amount": 0, "unit": "kg" if "kg" in key else "g" if "g" in key else "L"}
                totals[key]["amount"] += value
    return jsonify(totals), 200
