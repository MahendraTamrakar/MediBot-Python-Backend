from fastapi import APIRouter

router = APIRouter()

@router.post("/feedback")
async def feedback(response_id: str, helpful: bool):
    return {"status": "saved"}