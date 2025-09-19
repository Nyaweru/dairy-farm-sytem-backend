from flask import Blueprint, request, jsonify
from firebase_config import db
from datetime import datetime
import uuid

duties_api = Blueprint("duties_api", __name__)

# ✅ Create new duty
@duties_api.route("/api/duties", methods=["POST"])
def add_duty():
    try:
        data = request.json
        duty_id = str(uuid.uuid4())

        # fetch employee to get department
        emp_doc = db.collection("employees").document(data.get("employee_id")).get()
        if not emp_doc.exists:
            return jsonify({"error": "Employee not found"}), 404

        emp_data = emp_doc.to_dict()

        duty_data = {
            "id": duty_id,
            "employee_id": data.get("employee_id"),
            "employee_name": emp_data.get("name"),
            "task": data.get("task"),
            "department": emp_data.get("department"),
            "date": data.get("date"),
            "status": data.get("status", "pending"),
            "createdAt": datetime.utcnow()
        }

        db.collection("duties").document(duty_id).set(duty_data)
        return jsonify({"message": "✅ Duty assigned", "duty": duty_data}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Get all duties
@duties_api.route("/api/duties", methods=["GET"])
def get_duties():
    try:
        duties_ref = db.collection("duties").stream()
        duties = []
        for doc in duties_ref:
            d = doc.to_dict()
            d["id"] = d.get("id", doc.id)
            duties.append(d)
        return jsonify(duties), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Get duties by employee
@duties_api.route("/api/duties/employee/<emp_id>", methods=["GET"])
def get_duties_by_employee(emp_id):
    try:
        duties_ref = db.collection("duties").where("employee_id", "==", emp_id).stream()
        duties = [doc.to_dict() for doc in duties_ref]
        return jsonify(duties), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Update duty
@duties_api.route("/api/duties/<duty_id>", methods=["PUT"])
def update_duty(duty_id):
    try:
        data = request.json
        update_payload = {
            "task": data.get("task"),
            "date": data.get("date"),
            "status": data.get("status"),
            "updatedAt": datetime.utcnow()
        }
        update_payload = {k: v for k, v in update_payload.items() if v is not None}

        db.collection("duties").document(duty_id).update(update_payload)
        updated_doc = db.collection("duties").document(duty_id).get()
        updated_data = updated_doc.to_dict()

        return jsonify({"message": "✅ Duty updated", "duty": updated_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Delete duty
@duties_api.route("/api/duties/<duty_id>", methods=["DELETE"])
def delete_duty(duty_id):
    try:
        db.collection("duties").document(duty_id).delete()
        return jsonify({"message": f"✅ Duty {duty_id} deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
