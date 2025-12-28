from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi import Form
import logging

# Auth
from core.auth.dependencies import get_current_user

# Services
from core.services.ocr_service import OCRService
from core.services.report_analysis_service import ReportAnalysisService
from core.services.profile_update_service import ProfileUpdateService

# Infrastructure
from infrastructure.llm.gemini_llm import GeminiLLM

# DB
from db.mongodb import medical_reports_collection, users_collection
from db.reports_repo import MedicalReportRepository

router = APIRouter()
logger = logging.getLogger(__name__)

# ----------------------------
# Initialize dependencies
# ----------------------------
llm = GeminiLLM()
ocr_service = OCRService()
analysis_service = ReportAnalysisService(llm)
reports_repo = MedicalReportRepository(medical_reports_collection)
profile_update_service = ProfileUpdateService(llm, users_collection)

# ----------------------------
# API Endpoint
# ----------------------------

@router.post("/analyze-report", status_code=status.HTTP_200_OK)
async def analyze_report(
    file: UploadFile = File(...),
    consent: bool = Form(False),
    firebase_uid: str = Depends(get_current_user)
):
    """
    Upload PDF or image medical report.
    Performs OCR → Analysis → Save to DB.
    Optionally merges summary into medical profile if consent=true.
    """

    try:
        # 1️⃣ Validate file type
        if not (
            file.content_type.startswith("application/pdf")
            or file.content_type.startswith("image/")
        ):
            raise HTTPException(
                status_code=400,
                detail="Only PDF or image files are supported."
            )

        file_bytes = await file.read()

        # 2️⃣ OCR Extraction
        if file.content_type.startswith("image/"):
            extracted_text = await ocr_service.extract_from_image(file_bytes)
            report_type = "image"
        else:
            extracted_text = await ocr_service.extract_from_pdf(file_bytes)
            report_type = "pdf"

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Unable to extract text from the uploaded report."
            )

        # 3️⃣ LLM Analysis
        analysis = await analysis_service.analyze(extracted_text)

        # 4️⃣ Save report to MongoDB
        await reports_repo.save_report(
            firebase_uid=firebase_uid,
            filename=file.filename,
            report_type=report_type,
            extracted_text=extracted_text,
            analysis=analysis
        )

        # 5️⃣ Optional: Merge into medical profile (CONSENT REQUIRED)
        if consent:
            await profile_update_service.merge_report_into_profile(
                firebase_uid=firebase_uid,
                report_analysis=analysis
            )

        # 6️⃣ Response
        return JSONResponse(
            status_code=200,
            content={
                "message": "Report analyzed successfully",
                "report_type": report_type,
                "extracted_text_preview": extracted_text[:2000],
                "analysis": analysis,
                "profile_updated": consent
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception("Unexpected error during report analysis")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while analyzing the report."
        )


@router.get("/reports/history", status_code=status.HTTP_200_OK)
async def get_report_history(
    limit: int = 50,
    order: str = "desc",
    firebase_uid: str = Depends(get_current_user)
):
    """Return the current user's report history only."""
    try:
        reports = await reports_repo.list_reports_by_user_sorted(firebase_uid=firebase_uid, limit=limit, order=order)

        # Minimize payload by omitting large raw text unless needed
        sanitized = [
            {
                "id": r.get("id"),
                "original_filename": r.get("original_filename"),
                "report_type": r.get("report_type"),
                "created_at": r.get("created_at"),
                "analysis": r.get("analysis"),
            }
            for r in reports
        ]
        return JSONResponse(status_code=200, content={"items": sanitized, "count": len(sanitized), "order": order})
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch report history")
        raise HTTPException(status_code=500, detail="Failed to fetch report history")


@router.get("/reports/{report_id}", status_code=status.HTTP_200_OK)
async def get_report_by_id(
    report_id: str,
    firebase_uid: str = Depends(get_current_user)
):
    """Return a single report if it belongs to the current user."""
    try:
        doc = await reports_repo.get_report_by_id_for_user(firebase_uid=firebase_uid, report_id=report_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Report not found")

        # Present a consistent payload
        payload = {
            "id": doc.get("id"),
            "original_filename": doc.get("original_filename"),
            "report_type": doc.get("report_type"),
            "created_at": doc.get("created_at"),
            "analysis": doc.get("analysis"),
            # Expose raw extracted text only on single fetch to avoid heavy history payloads
            "extracted_text": doc.get("extracted_text"),
        }
        return JSONResponse(status_code=200, content=payload)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch report")
        raise HTTPException(status_code=500, detail="Failed to fetch report")