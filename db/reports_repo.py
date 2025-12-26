from datetime import datetime
from typing import Dict

class MedicalReportRepository:
    def __init__(self, collection):
        self.collection = collection

    async def save_report(
        self,
        firebase_uid: str,
        filename: str,
        report_type: str,
        extracted_text: str,
        analysis: Dict
    ):
        document = {
            "firebase_uid": firebase_uid,
            "original_filename": filename,
            "report_type": report_type,  # "pdf" | "image"
            "extracted_text": extracted_text,
            "analysis": analysis,
            "created_at": datetime.utcnow()
        }

        await self.collection.insert_one(document)
        return document