from flask import Blueprint, request, jsonify
from firebase_config import db
from datetime import datetime
import uuid

notification_api = Blueprint("notification_api", __name__)

# ✅ Get all notifications
@notification_api.route("/api/notifications", methods=["GET"])
def get_notifications():
    try:
        notifications_ref = db.collection("notifications").order_by("createdAt", direction="DESCENDING").stream()
        notifications = [{**doc.to_dict(), "id": doc.id} for doc in notifications_ref]
        return jsonify(notifications), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Mark notification as read
@notification_api.route("/api/notifications/<notification_id>/read", methods=["PUT"])
def mark_as_read(notification_id):
    try:
        db.collection("notifications").document(notification_id).update({"read": True})
        return jsonify({"message": "✅ Notification marked as read"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Create manual notification
@notification_api.route("/api/notifications", methods=["POST"])
def create_notification():
    try:
        data = request.json
        notification_id = str(uuid.uuid4())
        notification_data = {
            "id": notification_id,
            "cow_id": data.get("cow_id"),
            "title": data.get("title"),
            "message": data.get("message"),
            "date": data.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
            "read": False,
            "createdAt": datetime.utcnow()
        }
        db.collection("notifications").document(notification_id).set(notification_data)
        return jsonify({"message": "✅ Notification created", "notification": notification_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
