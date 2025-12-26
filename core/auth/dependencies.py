from fastapi import Header, HTTPException, Depends
from core.auth.firebase_auth import verify_firebase_token

def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid Authorization header")

    token = authorization.replace("Bearer ", "")
    try:
        return verify_firebase_token(token)
    except Exception:
        raise HTTPException(401, "Invalid Firebase token")

#dev mode remove it after, only for testing purpose
""" def get_current_user(authorization: str = Header(None)) -> str:
    if authorization is None:
        # DEV MODE fallback
        return "test_user_dev"

    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid Authorization header")

    token = authorization.replace("Bearer ", "")
    return verify_firebase_token(token) """