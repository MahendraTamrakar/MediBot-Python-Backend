from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from core.auth.dependencies import get_current_user
from core.services.doctor_pdf_service import DoctorSummaryPDFService
from db.mongodb import users_collection, medical_reports_collection

router = APIRouter()
pdf_service = DoctorSummaryPDFService()

@router.get("/doctor-summary-pdf")
async def export_doctor_summary(
    firebase_uid: str = Depends(get_current_user)
):
    user = await users_collection.find_one({"firebase_uid": firebase_uid})
    if not user:
        raise HTTPException(404, "User not found")

    report = await medical_reports_collection.find_one(
        {"firebase_uid": firebase_uid},
        sort=[("created_at", -1)]
    )

    if not report:
        raise HTTPException(404, "No reports found")

    pdf_bytes = pdf_service.generate_pdf(
        profile=user["profile"],
        report_analysis=report["analysis"]
    )

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=doctor_summary.pdf"
        }
    )