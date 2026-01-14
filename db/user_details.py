from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class PersonalDetails(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_type: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_photo_url: Optional[str] = None

class SavePersonalDetailsRequest(BaseModel):
    personal_details: PersonalDetails