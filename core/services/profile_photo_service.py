import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException

class ProfilePhotoService:
    """Service for handling profile photo uploads and deletions"""
    
    UPLOAD_DIR = Path("uploads/profile-photos")
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    }
    
    def __init__(self):
        """Initialize the service and ensure upload directory exists"""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    async def validate_image(self, file: UploadFile) -> None:
        """
        Validate the uploaded file
        
        Args:
            file: The uploaded file
            
        Raises:
            HTTPException: If validation fails
        """
        # Check content type
        if file.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only {', '.join(self.ALLOWED_CONTENT_TYPES)} are allowed."
            )
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file extension. Only {', '.join(self.ALLOWED_EXTENSIONS)} are allowed."
            )
        
        # Check file size
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {self.MAX_FILE_SIZE / (1024*1024):.1f}MB."
            )
        
        # Reset file pointer for later reading
        await file.seek(0)
    
    def generate_unique_filename(self, original_filename: str, firebase_uid: str) -> str:
        """
        Generate a unique filename to avoid conflicts
        
        Args:
            original_filename: The original filename
            firebase_uid: The user's Firebase UID
            
        Returns:
            A unique filename
        """
        file_ext = Path(original_filename).suffix.lower()
        unique_id = uuid.uuid4().hex[:12]
        return f"{firebase_uid}_{unique_id}{file_ext}"
    
    async def save_photo(self, file: UploadFile, firebase_uid: str) -> str:
        """
        Save the uploaded photo to storage
        
        Args:
            file: The uploaded file
            firebase_uid: The user's Firebase UID
            
        Returns:
            The URL/path of the saved photo
        """
        # Validate the file
        await self.validate_image(file)
        
        # Generate unique filename
        filename = self.generate_unique_filename(file.filename, firebase_uid)
        file_path = self.UPLOAD_DIR / filename
        
        # Save the file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Return the URL (relative path)
        # In production, you would return the full URL from your cloud storage
        return f"/uploads/profile-photos/{filename}"
    
    async def delete_photo(self, photo_url: Optional[str]) -> None:
        """
        Delete a photo from storage
        
        Args:
            photo_url: The URL/path of the photo to delete
        """
        if not photo_url:
            return
        
        try:
            # Extract filename from URL
            # Handle both full URLs and relative paths
            if photo_url.startswith("http"):
                # For cloud storage URLs, implement cloud-specific deletion
                # For now, we'll skip cloud deletion
                pass
            else:
                # For local storage
                filename = photo_url.split("/")[-1]
                file_path = self.UPLOAD_DIR / filename
                
                if file_path.exists():
                    file_path.unlink()
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error deleting photo: {e}")
