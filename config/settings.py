import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGO_URI = os.getenv(
    "MONGO_URI",
)

# Firebase
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

assert not MODEL_NAME.startswith("models/"), "Do NOT include 'models/' prefix"

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set")