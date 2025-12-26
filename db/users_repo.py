from datetime import datetime

async def ensure_user_exists(users_collection, firebase_uid: str):
    await users_collection.update_one(
        {"firebase_uid": firebase_uid},
        {
            "$setOnInsert": {
                "firebase_uid": firebase_uid,
                "profile": {
                    "age": None,
                    "gender": None,
                    "allergies": [],
                    "chronic_conditions": [],
                    "active_medications": [],
                    "medical_summary": ""
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )