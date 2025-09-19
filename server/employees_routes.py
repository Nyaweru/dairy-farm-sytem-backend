from flask import Blueprint, request, jsonify
from firebase_config import db
from datetime import datetime
import uuid

employees_api = Blueprint("employees_api", __name__)

# ✅ Create new employee
@employees_api.route("/api/employees", methods=["POST"])
def add_employee():
    try:
        data = request.json
        emp_id = str(uuid.uuid4())

        employee_data = {
            "id": emp_id,
            "name": data.get("name"),
            "department": data.get("department"),
            "role": data.get("role"),
            "contact": data.get("contact"),
            "createdAt": datetime.utcnow()
        }

        db.collection("employees").document(emp_id).set(employee_data)
        return jsonify({"message": "✅ Employee added", "employee": employee_data}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Get all employees
@employees_api.route("/api/employees", methods=["GET"])
def get_employees():
    try:
        emp_ref = db.collection("employees").stream()
        employees = []
        for doc in emp_ref:
            d = doc.to_dict()
            d["id"] = d.get("id", doc.id)
            employees.append(d)
        return jsonify(employees), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Get single employee
@employees_api.route("/api/employees/<emp_id>", methods=["GET"])
def get_employee(emp_id):
    try:
        doc = db.collection("employees").document(emp_id).get()
        if not doc.exists:
            return jsonify({"error": "Employee not found"}), 404
        return jsonify(doc.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Update employee
@employees_api.route("/api/employees/<emp_id>", methods=["PUT"])
def update_employee(emp_id):
    try:
        data = request.json
        update_payload = {
            "name": data.get("name"),
            "department": data.get("department"),
            "role": data.get("role"),
            "contact": data.get("contact"),
            "updatedAt": datetime.utcnow()
        }

        # remove None values
        update_payload = {k: v for k, v in update_payload.items() if v is not None}

        db.collection("employees").document(emp_id).update(update_payload)
        updated_doc = db.collection("employees").document(emp_id).get()
        updated_data = updated_doc.to_dict()

        return jsonify({"message": "✅ Employee updated", "employee": updated_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Delete employee
@employees_api.route("/api/employees/<emp_id>", methods=["DELETE"])
def delete_employee(emp_id):
    try:
        db.collection("employees").document(emp_id).delete()
        return jsonify({"message": f"✅ Employee {emp_id} deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
