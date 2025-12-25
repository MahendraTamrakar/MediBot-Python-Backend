from fastapi import APIRouter, UploadFile, File, HTTPException
import os, shutil
from infrastructure.llm.gemini_llm import GeminiLLM
from core.agents.ocr_agent import OCRAgent
from core.agents.diagnosis_agent import DiagnosisAgent
from core.agents.compliance_agent import ComplianceAgent
from core.orchestrator.diagnosis_orchestrator import DiagnosisOrchestrator

router = APIRouter()

@router.post("/ai-diagnosis")
async def ai_diagnosis(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
        raise HTTPException(400, "Unsupported file type")

    os.makedirs("temp", exist_ok=True)
    path = f"temp/{file.filename}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    orchestrator = DiagnosisOrchestrator(
        OCRAgent(),
        DiagnosisAgent(GeminiLLM()),
        ComplianceAgent()
    )

    return await orchestrator.process(path)