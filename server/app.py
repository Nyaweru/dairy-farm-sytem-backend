# server/app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
from firebase_config import db
from cow_routes import cow_api 
from milkrecords_routes import milk_bp
from treatments_routes import treatment_api
from notification_routes import notification_api
from vaccinations_routes import vaccination_api
from health_routes import health_api
from breeding_routes import breeding_api
from breedingalerts_routes import alerts_api
from employees_routes import employees_api
from duties_routes import duties_api
from performance_routes import performance_api
from feeding_routes import feeding_bp

app = Flask(__name__)
CORS(app)

# Routes
app.register_blueprint(cow_api)
#app.register_blueprint(milk_bp)
app.register_blueprint(milk_bp, url_prefix="/api")
app.register_blueprint(treatment_api)
app. register_blueprint (notification_api)
app.register_blueprint(vaccination_api)
app.register_blueprint(health_api)
app.register_blueprint(breeding_api)
app.register_blueprint(alerts_api)
app.register_blueprint(employees_api)
app.register_blueprint(duties_api)
app.register_blueprint(performance_api)
app.register_blueprint(feeding_bp)
@app.route("/")
def index():
    return jsonify({"message": "Dairy Farm Flask API running"}), 200

# Example: Save user data (optional)
@app.route("/api/save_user", methods=["POST"])
def save_user():
    data = request.json
    user_id = data.get("uid")
    user_data = {
        "name": data.get("name"),
        "phone": data.get("phone"),
        "email": data.get("email"),
        "createdAt": data.get("createdAt")
    }
    db.collection("users").document(user_id).set(user_data)
    return jsonify({"message": "User saved"}), 200

if __name__ == "__main__":
    app.run(debug=True)
