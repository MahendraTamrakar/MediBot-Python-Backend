from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from api.report_controller import router as report_router
from api.chat_controller import router as chat_router
from api.health_controller import router as health_router
from api.doctor_summary_controller import router as doctor_summary_router
from api.user_profile_controller import router as user_profile_router
from api.chat_document_controller import router as chat_document_router
from api.account_controller import router as account_router
from api.auth_controller import router as auth_router

app = FastAPI(title="MediBot – AI Medical Assistant")

# Mount static files for uploaded profile photos
uploads_dir = Path("uploads")
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(chat_document_router)
app.include_router(report_router)
app.include_router(doctor_summary_router)
app.include_router(user_profile_router)
app.include_router(account_router)
app.include_router(auth_router)