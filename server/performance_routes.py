from flask import Blueprint, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

performance_api = Blueprint("performance_api", __name__)

# ✅ Initialize Firebase app only once
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
performance_collection = db.collection("performance")

# ✅ Get all performance records
@performance_api.route("/api/performance", methods=["GET"])
def get_performance():
    try:
        docs = performance_collection.order_by("date", direction=firestore.Query.DESCENDING).stream()
        records = [{**doc.to_dict(), "id": doc.id} for doc in docs]
        return jsonify(records), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Add new performance record
@performance_api.route("/api/performance", methods=["POST"])
def add_performance():
    try:
        data = request.json
        if "date" not in data:
            data["date"] = datetime.datetime.now().isoformat()

        doc_ref = performance_collection.add(data)
        return jsonify({"message": "✅ Performance record added", "id": doc_ref[1].id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Update performance record
@performance_api.route("/api/performance/<string:record_id>", methods=["PUT"])
def update_performance(record_id):
    try:
        data = request.json
        performance_collection.document(record_id).update(data)
        return jsonify({"message": "✅ Performance record updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Delete performance record
@performance_api.route("/api/performance/<string:record_id>", methods=["DELETE"])
def delete_performance(record_id):
    try:
        performance_collection.document(record_id).delete()
        return jsonify({"message": "✅ Performance record deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
