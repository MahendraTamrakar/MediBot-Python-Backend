from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from core.auth.dependencies import get_current_user
from db.mongodb import users_collection
from db.user_details import SavePersonalDetailsRequest

router = APIRouter(prefix="/user", tags=["User Profile"])

@router.post("/profile")
async def save_profile(
    req: SavePersonalDetailsRequest,
    firebase_uid: str = Depends(get_current_user)
):
    try:
        await users_collection.update_one(
            {"firebase_uid": firebase_uid},
            {
                "$set": {
                    "personal_details": req.personal_details.dict(exclude_none=True),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "firebase_uid": firebase_uid,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        return {"message": "Profile saved successfully"}

    except Exception:
        raise HTTPException(500, "Failed to save profile")


@router.get("/profile")
async def get_profile(
    firebase_uid: str = Depends(get_current_user)
):
    user = await users_collection.find_one(
        {"firebase_uid": firebase_uid},
        {"_id": 0, "personal_details": 1}
    )
    return user.get("personal_details", {})