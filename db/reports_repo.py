from datetime import datetime
from typing import Dict
from typing import List, Optional
from bson import ObjectId

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

    async def list_reports_by_user(self, firebase_uid: str, limit: int = 50) -> List[Dict]:
        """Return recent reports for a given user, newest first."""
        cursor = (
            self.collection
            .find({"firebase_uid": firebase_uid})
            .sort("created_at", -1)
            .limit(limit)
        )

        results: List[Dict] = []
        async for doc in cursor:
            # Normalize id to string for API friendliness
            if "_id" in doc:
                doc["id"] = str(doc["_id"])  # non-breaking addition
            results.append(doc)
        return results

    async def list_reports_by_user_sorted(self, firebase_uid: str, limit: int = 50, order: str = "desc") -> List[Dict]:
        """Return reports for a given user sorted by created_at ascending/descending."""
        sort_dir = -1 if order.lower() == "desc" else 1
        cursor = (
            self.collection
            .find({"firebase_uid": firebase_uid})
            .sort("created_at", sort_dir)
            .limit(limit)
        )
        results: List[Dict] = []
        async for doc in cursor:
            if "_id" in doc:
                doc["id"] = str(doc["_id"]) 
            results.append(doc)
        return results

    async def get_report_by_id_for_user(self, firebase_uid: str, report_id: str) -> Optional[Dict]:
        """Fetch a single report ensuring it belongs to the requesting user."""
        try:
            oid = ObjectId(report_id)
        except Exception:
            return None

        doc = await self.collection.find_one({"_id": oid, "firebase_uid": firebase_uid})
        if doc is None:
            return None
        doc["id"] = str(doc["_id"])  # convenience field
        return doc