from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import logging

from core.auth.dependencies import get_current_user
from core.services.account_deletion_service import AccountDeletionService

router = APIRouter()
logger = logging.getLogger(__name__)

deletion_service = AccountDeletionService()


@router.delete("/account", status_code=status.HTTP_200_OK)
async def delete_account(firebase_uid: str = Depends(get_current_user)):
    """Hard delete the current user's account and associated data."""
    try:
        result = await deletion_service.delete_user_account(firebase_uid)
        return JSONResponse(status_code=200, content={
            "message": "Account deleted successfully",
            "result": result
        })
    except HTTPException:
        raise
    except Exception:
        logger.exception("Account deletion failed")
        raise HTTPException(status_code=500, detail="Account deletion failed")
