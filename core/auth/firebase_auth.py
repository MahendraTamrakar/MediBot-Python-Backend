import firebase_admin
from firebase_admin import auth, credentials

cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)

def verify_firebase_token(id_token: str) -> str:
    decoded = auth.verify_id_token(id_token)
    return decoded["uid"]   # stable user identifier