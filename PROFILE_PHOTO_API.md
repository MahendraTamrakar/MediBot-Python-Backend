# Profile Photo API Documentation

This document describes the profile photo upload and delete functionality added to the MediBot FastAPI backend.

## Features

✅ **Upload profile photos** with automatic validation  
✅ **Delete profile photos** from storage and database  
✅ **Retrieve medical profile** data  
✅ **Automatic old photo deletion** when uploading a new one  
✅ **File type validation** (jpg, jpeg, png, webp only)  
✅ **File size validation** (max 5MB)  
✅ **Secure authentication** required for all endpoints  

---

## Database Schema

The `profile_photo_url` field has been added to the user profile model:

```json
{
  "firebase_uid": "user123",
  "personal_details": {
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "dob": "1990-01-01",
    "gender": "male",
    "blood_group": "O+",
    "phone": "+1234567890",
    "profile_photo_url": "/uploads/profile-photos/user123_abc123def456.jpg"
  },
  "profile": {
    "age": 34,
    "gender": "male",
    "allergies": ["Peanuts"],
    "chronic_conditions": ["Hypertension"],
    "active_medications": ["Lisinopril"],
    "medical_summary": "Patient history..."
  }
}
```

---

## API Endpoints

### 1. Upload Profile Photo

**Endpoint:** `POST /user/profile/photo`

**Description:** Upload a profile photo for the authenticated user.

**Authentication:** Required (Bearer token)

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with file field

**Accepted file types:**
- image/jpeg (.jpg, .jpeg)
- image/png (.png)
- image/webp (.webp)

**Maximum file size:** 5MB

**Response (200 OK):**
```json
{
  "profile_photo_url": "/uploads/profile-photos/user123_abc123def456.jpg"
}
```

**Error Responses:**

- `400 Bad Request` - Invalid file type or file too large
```json
{
  "detail": "Invalid file type. Only image/jpeg, image/jpg, image/png, image/webp are allowed."
}
```

- `400 Bad Request` - File too large
```json
{
  "detail": "File too large. Maximum size is 5.0MB."
}
```

- `401 Unauthorized` - Missing or invalid authentication token

- `500 Internal Server Error` - Server error during upload

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/user/profile/photo" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/photo.jpg"
```

**Example (Python/httpx):**
```python
import httpx

async with httpx.AsyncClient() as client:
    with open("photo.jpg", "rb") as f:
        response = await client.post(
            "http://localhost:8000/user/profile/photo",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": f}
        )
    print(response.json())
```

**Example (Postman):**
1. Method: POST
2. URL: `http://localhost:8000/user/profile/photo`
3. Headers: `Authorization: Bearer YOUR_TOKEN`
4. Body: form-data
   - Key: `file` (type: File)
   - Value: Select your image file

---

### 2. Delete Profile Photo

**Endpoint:** `DELETE /user/profile/photo`

**Description:** Delete the profile photo for the authenticated user.

**Authentication:** Required (Bearer token)

**Response (200 OK):**
```json
{
  "message": "Profile photo deleted successfully"
}
```

**Error Responses:**

- `404 Not Found` - No profile photo found
```json
{
  "detail": "No profile photo found"
}
```

- `401 Unauthorized` - Missing or invalid authentication token

- `500 Internal Server Error` - Server error during deletion

**Example (cURL):**
```bash
curl -X DELETE "http://localhost:8000/user/profile/photo" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example (Python/httpx):**
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.delete(
        "http://localhost:8000/user/profile/photo",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(response.json())
```

---

### 3. Get Medical Profile

**Endpoint:** `GET /user/medical-profile`

**Description:** Get the medical profile for the authenticated user.

**Authentication:** Required (Bearer token)

**Response (200 OK):**
```json
{
  "age": 34,
  "gender": "male",
  "allergies": ["Peanuts", "Penicillin"],
  "chronic_conditions": ["Hypertension"],
  "active_medications": ["Lisinopril 10mg"],
  "medical_summary": "Patient with well-controlled hypertension..."
}
```

**Response when no medical profile exists:**
```json
{}
```

**Error Responses:**

- `401 Unauthorized` - Missing or invalid authentication token

- `500 Internal Server Error` - Server error

**Example (cURL):**
```bash
curl -X GET "http://localhost:8000/user/medical-profile" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example (Python/httpx):**
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/user/medical-profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(response.json())
```

---

### 4. Get User Profile (Updated)

**Endpoint:** `GET /user/profile`

**Description:** Get personal details for the authenticated user, now includes `profile_photo_url`.

**Authentication:** Required (Bearer token)

**Response (200 OK):**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "dob": "1990-01-01",
  "gender": "male",
  "blood_group": "O+",
  "phone": "+1234567890",
  "profile_photo_url": "/uploads/profile-photos/user123_abc123def456.jpg"
}
```

---

## Technical Implementation

### File Storage

- **Development/Local:** Files are stored in `uploads/profile-photos/` directory
- **Production:** Can be configured to use cloud storage (AWS S3, Google Cloud Storage, Azure Blob Storage)

### File Naming

Files are renamed with a unique identifier to prevent conflicts:
- Format: `{firebase_uid}_{unique_id}.{extension}`
- Example: `user123_abc123def456.jpg`

### Security Features

1. **Authentication:** All endpoints require valid Firebase authentication token
2. **File Type Validation:** Only image files are accepted
3. **File Size Validation:** Maximum 5MB to prevent abuse
4. **Unique Filenames:** Prevents conflicts and overwrites
5. **Old Photo Cleanup:** Automatically deletes old photo when uploading new one

### Error Handling

- Comprehensive error handling with appropriate HTTP status codes
- Detailed error messages for debugging
- Graceful failure for non-critical operations (e.g., deleting old photos)

---

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The following new dependency has been added:
- `aiofiles` - For async file operations

### 2. Run the Application

```bash
uvicorn main:app --reload
```

---

## Testing

### Manual Testing with Postman

See [POSTMAN_TESTING_GUIDE.md](POSTMAN_TESTING_GUIDE.md) for detailed testing instructions.

### Testing Workflow

1. **Get authentication token** from Firebase
2. **Upload a profile photo:**
   - Use POST /user/profile/photo
   - Attach an image file
3. **Verify the upload:**
   - Use GET /user/profile
   - Check that profile_photo_url is populated
4. **Access the photo:**
   - Open the URL in browser (e.g., http://localhost:8000/uploads/profile-photos/filename.jpg)
5. **Upload a new photo:**
   - Use POST /user/profile/photo again
   - Verify old photo is deleted
6. **Delete the photo:**
   - Use DELETE /user/profile/photo
   - Verify photo is removed from storage and database

---

## Migrating to Cloud Storage

To use cloud storage instead of local storage, modify [core/services/profile_photo_service.py](core/services/profile_photo_service.py):

### AWS S3 Example:

```python
import boto3
from botocore.exceptions import ClientError

class ProfilePhotoService:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = 'your-bucket-name'
    
    async def save_photo(self, file: UploadFile, firebase_uid: str) -> str:
        await self.validate_image(file)
        filename = self.generate_unique_filename(file.filename, firebase_uid)
        
        # Upload to S3
        content = await file.read()
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=f"profile-photos/{filename}",
            Body=content,
            ContentType=file.content_type
        )
        
        # Return S3 URL
        return f"https://{self.bucket_name}.s3.amazonaws.com/profile-photos/{filename}"
    
    async def delete_photo(self, photo_url: str) -> None:
        if not photo_url:
            return
        
        # Extract key from URL
        key = photo_url.split('.com/')[-1]
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
        except ClientError as e:
            print(f"Error deleting from S3: {e}")
```

---

## File Structure

```
backend/
├── api/
│   └── user_profile_controller.py  # Updated with new endpoints
├── core/
│   └── services/
│       └── profile_photo_service.py  # New service for photo handling
├── db/
│   └── user_details.py  # PersonalDetails model (already had profile_photo_url)
├── uploads/
│   └── profile-photos/  # Local storage directory
├── main.py  # Updated to serve static files
├── requirements.txt  # Added aiofiles
└── PROFILE_PHOTO_API.md  # This documentation
```

---

## Notes

- The `profile_photo_url` field was already present in the `PersonalDetails` model
- The uploads directory is excluded from git (.gitignore)
- Static files are served at `/uploads` path
- All operations are async for optimal performance
- File validation happens before any database or storage operations

---

## Support

For issues or questions, please refer to the main [README.md](README.md) or contact the development team.
