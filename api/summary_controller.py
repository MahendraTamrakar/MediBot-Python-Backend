from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
import os, shutil, uuid

from core.agents.ocr_agent import OCRAgent
from core.agents.diagnosis_agent import DiagnosisAgent
from core.agents.compliance_agent import ComplianceAgent
from core.orchestrator.diagnosis_orchestrator import DiagnosisOrchestrator
from infrastructure.llm.gemini_llm import GeminiLLM
from core.services.pdf_service import generate_doctor_summary_pdf

router = APIRouter()

@router.post("/export-doctor-summary")
async def export_doctor_summary(file: UploadFile = File(...)):
    os.makedirs("temp", exist_ok=True)

    input_path = f"temp/{uuid.uuid4()}_{file.filename}"
    output_path = f"temp/doctor_summary_{uuid.uuid4()}.pdf"

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    orchestrator = DiagnosisOrchestrator(
        OCRAgent(),
        DiagnosisAgent(GeminiLLM()),
        ComplianceAgent()
    )

    analysis = await orchestrator.process(input_path)

    generate_doctor_summary_pdf(analysis, output_path)

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="doctor_summary.pdf"
    )