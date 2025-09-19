from flask import Flask, jsonify
from google.cloud import firestore
from collections import defaultdict
from datetime import datetime,timedelta 
import calendar
from flask import Blueprint, request, jsonify
from google.cloud import firestore
import os

# If not set globally
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/hp/Desktop/DAIRY FARM/dairy-farm-backend/server/serviceAccountKey.json"


db = firestore.Client()
milk_bp = Blueprint("milk_bp", __name__)

# GET /cows
@milk_bp.route("/cows", methods=["GET"])
def get_cows():
    docs = db.collection("cows").stream()
    cows = []
    for d in docs:
        obj = d.to_dict()
        obj["id"] = d.id
        cows.append(obj)
    return jsonify(cows)

# GET /milk-records?date=YYYY-MM-DD
# POST /milk-records
@milk_bp.route("/milk-records", methods=["GET", "POST"])
def milk_records():
    if request.method == "GET":
        date = request.args.get("date")
        if date:
            docs = db.collection("milk_records").where("date", "==", date).stream()
        else:
            docs = db.collection("milk_records").limit(500).stream()
        recs = []
        for d in docs:
            obj = d.to_dict()
            obj["id"] = d.id
            recs.append(obj)
        return jsonify(recs)

    # POST: create or update a record
    payload = request.get_json()
    cow_id = payload.get("cow_id")
    date = payload.get("date")
    if not cow_id or not date:
        return jsonify({"error": "cow_id and date required"}), 400

    morning = float(payload.get("morning", 0))
    noon = float(payload.get("noon", 0))
    evening = float(payload.get("evening", 0))
    milker = payload.get("milker", "")

    daily_total = morning + noon + evening
    doc_id = f"{cow_id}_{date}"  # deterministic id so we update same doc
    doc_ref = db.collection("milk_records").document(doc_id)
    doc_ref.set({
        "cow_id": cow_id,
        "date": date,
        "morning": morning,
        "noon": noon,
        "evening": evening,
        "milker": milker,
        "daily_total": daily_total,
        "updated_at": firestore.SERVER_TIMESTAMP
    }, merge=True)
    return jsonify({"ok": True, "doc_id": doc_id})

# GET /milk-summary?date=YYYY-MM-DD&range=day|week|month|month_series
@milk_bp.route("/milk-summary", methods=["GET"])
def milk_summary():
    date_str = request.args.get("date") or datetime.utcnow().strftime("%Y-%m-%d")
    r = request.args.get("range", "day")
    # parse date
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return jsonify({"error": "invalid date"}), 400

    if r == "day":
        docs = db.collection("milk_records").where("date", "==", date_str).stream()
    elif r == "week":
        # week Monday..Sunday
        start = d - timedelta(days=d.weekday())
        end = start + timedelta(days=6)
        start_s = start.strftime("%Y-%m-%d")
        end_s = end.strftime("%Y-%m-%d")
        docs = db.collection("milk_records").where("date", ">=", start_s).where("date", "<=", end_s).stream()
    elif r == "month":
        start = d.replace(day=1)
        last_day = calendar.monthrange(d.year, d.month)[1]
        end = d.replace(day=last_day)
        start_s = start.strftime("%Y-%m-%d")
        end_s = end.strftime("%Y-%m-%d")
        docs = db.collection("milk_records").where("date", ">=", start_s).where("date", "<=", end_s).stream()
    elif r == "month_series":
        months = int(request.args.get("months", 12))
        # produce series of last `months` totals: month format YYYY-MM
        series = []
        for i in range(months - 1, -1, -1):
            ym = (d.replace(day=1) - timedelta(days=1)).replace(day=1)  # temporary
            # compute year-month by shifting months
            year = d.year
            month = d.month - i
            while month <= 0:
                year -= 1
                month += 12
            start = datetime(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end = datetime(year, month, last_day)
            start_s = start.strftime("%Y-%m-%d")
            end_s = end.strftime("%Y-%m-%d")
            q = db.collection("milk_records").where("date", ">=", start_s).where("date", "<=", end_s).stream()
            total = 0
            for rdoc in q:
                rd = rdoc.to_dict()
                total += float(rd.get("daily_total", 0))
            series.append({"month": f"{start.year}-{start.month:02d}", "total": total})
        return jsonify(series)

    else:
        return jsonify({"error": "range must be day|week|month|month_series"}), 400

    total = 0.0
    cows_totals = {}
    for ddoc in docs:
        rdoc = ddoc.to_dict()
        total += float(rdoc.get("daily_total", 0))
        cid = rdoc.get("cow_id")
        cows_totals[cid] = cows_totals.get(cid, 0) + float(rdoc.get("daily_total", 0))

    return jsonify({"range": r, "date": date_str, "total": total, "by_cow": cows_totals,
                    "week_total": total if r == "week" else None,
                    "month_total": total if r == "month" else None})
