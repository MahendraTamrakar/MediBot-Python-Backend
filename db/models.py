from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime

class ChatSession(BaseModel):
    firebase_uid: str
    messages: List[ChatMessage]
    created_at: datetime

class MedicalProfile(BaseModel):
    age: Optional[int]
    gender: Optional[str]
    allergies: List[str]
    chronic_conditions: List[str]
    active_medications: List[str]
    medical_summary: str

class User(BaseModel):
    firebase_uid: str
    profile: MedicalProfile
    created_at: datetime
    updated_at: datetime