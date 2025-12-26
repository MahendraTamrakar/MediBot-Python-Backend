from fastapi import FastAPI
from api.report_controller import router as report_router
from api.doctor_summary_controller import router as summary_router
from api.chat_controller import router as chat_router
from api.health_controller import router as health_router
from api.doctor_summary_controller import router as doctor_summary_router

app = FastAPI(title="MediBot – AI Medical Assistant")

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(report_router)
app.include_router(summary_router)
app.include_router(doctor_summary_router)