from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from core.auth.dependencies import get_current_user
from core.services.ocr_service import OCRService
from core.services.vector.faiss_store import FaissVectorStore
from core.services.vector.embedding_service import EmbeddingService
from core.services.documents.chat_document_service import ChatDocumentService
from infrastructure.llm.gemini_llm import GeminiLLM
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chat/upload-document", status_code=200)
async def upload_doc(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    try:
        # Read file bytes
        file_bytes = await file.read()
        
        if not file_bytes:
            raise HTTPException(status_code=400, detail="File is empty")

        # Initialize OCR service and extract text based on file type
        ocr = OCRService()
        if (file.content_type and "pdf" in file.content_type.lower()) or (file.filename and file.filename.lower().endswith(".pdf")):
            text = await ocr.extract_from_pdf(file_bytes)
        else:
            text = await ocr.extract_from_image(file_bytes)

        if not text:
            raise HTTPException(status_code=400, detail="No text extracted from document")

        # Initialize LLM and embedder
        llm = GeminiLLM()
        embedder = EmbeddingService(llm=llm)

        # Get embedding dimension from sample embedding
        sample_text = text[:500] if text else " "
        sample_vec = await embedder.embed(sample_text)
        dim = len(sample_vec) if sample_vec else 768

        # Create vector store per user/session
        index_path = f"faiss_store/{user_id}_{session_id}_docs.index"
        vector_store = FaissVectorStore(dim=dim, index_path=index_path)

        # Ingest document text into vector store with metadata
        chat_doc_service = ChatDocumentService(vector_store=vector_store, embedder=embedder)
        document_id = await chat_doc_service.ingest_document(
            user_id=user_id, 
            chat_session_id=session_id, 
            text=text
        )

        return {
            "message": "Document attached to chat",
            "document_id": document_id,
            "text_length": len(text),
            "session_id": session_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error uploading document")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")