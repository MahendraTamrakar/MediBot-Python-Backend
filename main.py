from fastapi import FastAPI
from api.report_controller import router as report_router
from api.chat_controller import router as chat_router
from api.health_controller import router as health_router
from api.doctor_summary_controller import router as doctor_summary_router
from api.user_profile_controller import router as user_profile_router
from api.chat_document_controller import router as chat_document_router
from api.account_controller import router as account_router

app = FastAPI(title="MediBot – AI Medical Assistant")

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(chat_document_router)
app.include_router(report_router)
app.include_router(doctor_summary_router)
app.include_router(user_profile_router)
app.include_router(account_router)