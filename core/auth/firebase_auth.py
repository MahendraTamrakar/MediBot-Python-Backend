"""Firebase Auth helper utilities."""

import firebase_admin
from firebase_admin import auth, credentials
import httpx

from config import settings

cred = credentials.Certificate("firebase-service-account.json")
if not firebase_admin._apps:  # type: ignore[attr-defined]
    firebase_admin.initialize_app(cred)


class FirebaseAuthError(Exception):
    """Raised when Firebase auth REST APIs respond with an error."""


def verify_firebase_token(id_token: str) -> str:
    """Verify a Firebase ID token and return the stable UID."""
    decoded = auth.verify_id_token(id_token)
    return decoded["uid"]


def _ensure_api_key() -> str:
    api_key = settings.FIREBASE_WEB_API_KEY
    if not api_key:
        raise FirebaseAuthError("FIREBASE_WEB_API_KEY is not configured")
    return api_key


def _handle_response(response: httpx.Response) -> dict:
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.is_success:
        return payload

    message = payload.get("error", {}).get("message") or "Firebase auth failed"
    raise FirebaseAuthError(message)


async def sign_up_with_email_password(email: str, password: str) -> dict:
    """Register a new user with email/password using Firebase Identity Toolkit REST API."""
    api_key = _ensure_api_key()
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload)
    return _handle_response(response)


async def sign_in_with_email_password(email: str, password: str) -> dict:
    """Sign in with email/password using Firebase Identity Toolkit REST API."""
    api_key = _ensure_api_key()
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload)
    return _handle_response(response)


async def sign_in_with_google(id_token: str) -> dict:
    """Exchange a Google ID token for a Firebase session via Identity Toolkit."""
    api_key = _ensure_api_key()
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}"
    payload = {
        "postBody": f"id_token={id_token}&providerId=google.com",
        "requestUri": "https://medibot-fa365.web.app",  # must match authorized domains
        "returnIdpCredential": True,
        "returnSecureToken": True,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload)
    return _handle_response(response)