from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from datetime import datetime

from core.auth.dependencies import get_current_user
from db.mongodb import users_collection
from db.user_details import SavePersonalDetailsRequest
from core.services.profile_photo_service import ProfilePhotoService

router = APIRouter(prefix="/user", tags=["User Profile"])

# Initialize profile photo service
photo_service = ProfilePhotoService()

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


@router.post("/profile/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    firebase_uid: str = Depends(get_current_user)
):
    """
    Upload a profile photo for the authenticated user.
    
    - Accepts image files: jpg, jpeg, png, webp
    - Maximum file size: 5MB
    - Automatically deletes old profile photo if exists
    """
    try:
        # Get current profile to check for existing photo
        user = await users_collection.find_one(
            {"firebase_uid": firebase_uid},
            {"_id": 0, "personal_details.profile_photo_url": 1}
        )
        
        old_photo_url = None
        if user and user.get("personal_details"):
            old_photo_url = user["personal_details"].get("profile_photo_url")
        
        # Save new photo
        photo_url = await photo_service.save_photo(file, firebase_uid)
        
        # Update database
        await users_collection.update_one(
            {"firebase_uid": firebase_uid},
            {
                "$set": {
                    "personal_details.profile_photo_url": photo_url,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Delete old photo after successful upload
        if old_photo_url:
            await photo_service.delete_photo(old_photo_url)
        
        return {"profile_photo_url": photo_url}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to upload profile photo: {str(e)}")


@router.delete("/profile/photo")
async def delete_profile_photo(
    firebase_uid: str = Depends(get_current_user)
):
    """
    Delete the profile photo for the authenticated user.
    
    - Removes the photo from storage
    - Sets profile_photo_url to null in the database
    - Returns success even if no photo exists (idempotent operation)
    """
    try:
        # Get current profile photo URL
        user = await users_collection.find_one(
            {"firebase_uid": firebase_uid},
            {"_id": 0, "personal_details.profile_photo_url": 1}
        )
        
        photo_url = None
        if user and user.get("personal_details"):
            photo_url = user["personal_details"].get("profile_photo_url")
        
        # If no photo exists, return success (idempotent delete)
        if not photo_url:
            return {"message": "No profile photo to delete"}
        
        # Delete from storage
        await photo_service.delete_photo(photo_url)
        
        # Update database
        await users_collection.update_one(
            {"firebase_uid": firebase_uid},
            {
                "$set": {
                    "personal_details.profile_photo_url": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Profile photo deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to delete profile photo: {str(e)}")


@router.get("/medical-profile")
async def get_medical_profile(
    firebase_uid: str = Depends(get_current_user)
):
    """
    Get the medical profile for the authenticated user.
    
    Returns medical profile data including:
    - allergies
    - chronic_conditions
    - active_medications
    - medical_summary
    - age
    - gender
    
    Returns empty object {} if no medical profile exists.
    """
    try:
        user = await users_collection.find_one(
            {"firebase_uid": firebase_uid},
            {"_id": 0, "profile": 1}
        )
        
        if user and user.get("profile"):
            return user["profile"]
        
        return {}
    
    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve medical profile: {str(e)}")