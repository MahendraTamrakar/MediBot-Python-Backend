from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from core.auth import firebase_auth

router = APIRouter(prefix="/auth", tags=["auth"])


class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    id_token: str  # Google ID token obtained from Firebase Google sign-in


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/signup/email", status_code=status.HTTP_201_CREATED)
async def signup_with_email(body: EmailLoginRequest):
    """Register a new user with email/password and return tokens."""
    try:
        result = await firebase_auth.sign_up_with_email_password(body.email, body.password)
        return {
            "idToken": result.get("idToken"),
            "refreshToken": result.get("refreshToken"),
            "expiresIn": int(result.get("expiresIn", 0)) if result.get("expiresIn") else None,
            "uid": result.get("localId"),
            "emailVerified": result.get("emailVerified", False),
        }
    except firebase_auth.FirebaseAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/login/email", status_code=status.HTTP_200_OK)
async def login_with_email(body: EmailLoginRequest):
    """Authenticate with Firebase email/password and return tokens."""
    try:
        result = await firebase_auth.sign_in_with_email_password(body.email, body.password)
        return {
            "idToken": result.get("idToken"),
            "refreshToken": result.get("refreshToken"),
            "expiresIn": int(result.get("expiresIn", 0)) if result.get("expiresIn") else None,
            "uid": result.get("localId"),
            "emailVerified": result.get("emailVerified", False),
        }
    except firebase_auth.FirebaseAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/login/google", status_code=status.HTTP_200_OK)
async def login_with_google(body: GoogleLoginRequest):
    """Exchange a Google ID token for Firebase tokens."""
    try:
        result = await firebase_auth.sign_in_with_google(body.id_token)
        return {
            "idToken": result.get("idToken"),
            "refreshToken": result.get("refreshToken"),
            "expiresIn": int(result.get("expiresIn", 0)) if result.get("expiresIn") else None,
            "uid": result.get("localId"),
            "email": result.get("email"),
            "provider": "google.com",
        }
    except firebase_auth.FirebaseAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(body: ForgotPasswordRequest):
    """Send a password reset email to the user."""
    try:
        await firebase_auth.send_password_reset_email(body.email)
        return {
            "message": "Password reset email sent successfully",
            "email": body.email
        }
    except firebase_auth.FirebaseAuthError as exc:
        error_message = str(exc)
        # Provide user-friendly error messages
        if "EMAIL_NOT_FOUND" in error_message:
            raise HTTPException(
                status_code=404,
                detail="No account found with this email address"
            )
        elif "INVALID_EMAIL" in error_message:
            raise HTTPException(
                status_code=400,
                detail="Invalid email address"
            )
        elif "USER_DISABLED" in error_message:
            raise HTTPException(
                status_code=403,
                detail="This account has been disabled"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Unable to send password reset email. Please try again"
            )
