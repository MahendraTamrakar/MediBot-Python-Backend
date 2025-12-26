from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class PersonalDetails(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    phone: Optional[str] = None
    profile_photo_url: Optional[str] = None

class SavePersonalDetailsRequest(BaseModel):
    personal_details: PersonalDetails