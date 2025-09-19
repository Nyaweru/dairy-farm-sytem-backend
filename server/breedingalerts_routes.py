from flask import Blueprint, jsonify
from firebase_config import db
from datetime import datetime, timedelta

alerts_api = Blueprint("alerts_api", __name__)

@alerts_api.route("/api/breeding-alerts", methods=["GET"])
def get_breeding_alerts():
    try:
        today = datetime.utcnow().date()
        alerts = []

        breeding_ref = db.collection("breeding").stream()
        for doc in breeding_ref:
            record = doc.to_dict()
            cowname = record.get("cowname") or record.get("cow")

            # Birth alert: 7 days before expected birth
            if record.get("expectedBirth"):
                expected_birth = datetime.strptime(record["expectedBirth"], "%Y-%m-%d").date()
                days_remaining = (expected_birth - today).days
                if 0 <= days_remaining <= 7:
                    alerts.append({
                        "cow_id": record["cow"],
                        "cowname": cowname,
                        "type": "birth",
                        "message": f"Cow {cowname} is expected to calve on {record['expectedBirth']}.",
                        "days_remaining": days_remaining
                    })

            # Repeat AI alert
            if record.get("repeatDate"):
                repeat_date = datetime.strptime(record["repeatDate"], "%Y-%m-%d").date()
                days_remaining = (repeat_date - today).days
                if 0 <= days_remaining <= 7:
                    alerts.append({
                        "cow_id": record["cow"],
                        "cowname": cowname,
                        "type": "repeat",
                        "message": f"Cow {cowname} is due for repeat breeding on {record['repeatDate']}.",
                        "days_remaining": days_remaining
                    })

        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
