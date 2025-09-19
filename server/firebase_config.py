# server/firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore, storage

# Path to service account
cred = credentials.Certificate(r"C:\Users\hp\Desktop\DAIRY FARM\dairy-farm-backend\server\serviceAccountKey.json")

# Initialize app if not already
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        "storageBucket": "dairy-farm-ffe74.appspot.com"  # ✅ bucket name without gs://
    })

# Firestore DB
db = firestore.client()

# Firebase Storage bucket
bucket = storage.bucket()
