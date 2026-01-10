# Medical ChatBot - Postman Testing Guide

## Overview
This guide explains how to test document upload and document-based chat using Postman.

---

## Prerequisites

1. **Get Firebase Auth Token**
   - Log in to your app using Firebase
   - Get the `idToken` from browser console:
     ```javascript
     firebase.auth().currentUser.getIdToken(true).then(token => console.log(token))
     ```
   - Copy this token for all API requests

2. **Base URL**
   ```
   http://localhost:8000
   ```

---

## Test Flow

### Step 1: Create a Chat Session (Optional - auto-created)
This is optional since sessions auto-create, but useful for testing.

**Endpoint:** `POST /analyze-symptoms`

**Headers:**
```
Authorization: Bearer {your_firebase_token}
Content-Type: application/json
```

**Body:**
```json
{
  "symptoms": "I have been experiencing chest pain and shortness of breath for 3 days",
  "session_id": null
}
```

**Expected Response:**
```json
{
  "session_id": "session_123abc",
  "type": "medical_chat",
  "message": "...",
  "title": "Chest pain and shortness of breath",
  "is_new_session": true
}
```

**Save the `session_id`** - you'll need it for document upload.

---

### Step 2: Upload a Document (PDF or Image)
This is the KEY test to verify document integration.

**Endpoint:** `POST /chat/upload-document`

**Headers:**
```
Authorization: Bearer {your_firebase_token}
```

**Body (form-data):**
| Key | Value | Type |
|-----|-------|------|
| `session_id` | `session_123abc` | Text |
| `file` | `your_medical_report.pdf` | File |

**Steps in Postman:**
1. Select **POST** method
2. Enter URL: `http://localhost:8000/chat/upload-document`
3. Go to **Headers** tab → Add `Authorization: Bearer {token}`
4. Go to **Body** tab → Select **form-data**
5. Add:
   - Key: `session_id`, Value: `session_123abc`, Type: **Text**
   - Key: `file`, Value: Upload your PDF/Image, Type: **File**
6. Click **Send**

**Expected Response:**
```json
{
  "message": "Document attached to chat",
  "document_id": "doc_456def",
  "text_length": 2543,
  "session_id": "session_123abc"
}
```

**What Happens Behind the Scenes:**
- OCR extracts text from the PDF/Image
- Text is converted to embeddings
- Embeddings are stored in FAISS vector database
- Associated with your `user_id` and `session_id`

---

### Step 3: Ask a Question Based on the Uploaded Document

**Endpoint:** `POST /analyze-symptoms`

**Headers:**
```
Authorization: Bearer {your_firebase_token}
Content-Type: application/json
```

**Body:**
```json
{
  "session_id": "session_123abc",
  "symptoms": "What does my blood pressure reading say?"
}
```

**Expected Behavior:**
- The system retrieves relevant text chunks from your uploaded document
- LLM references your document when answering
- Response should be specific to YOUR document content

**Expected Response:**
```json
{
  "session_id": "session_123abc",
  "type": "document_chat",
  "message": "Based on your uploaded report, your blood pressure reading is..."
}
```

---

## Testing Checklist

| Test | Expected Result | Status |
|------|-----------------|--------|
| Step 1: Create session | Session created successfully | ✓ |
| Step 2: Upload PDF document | Document extracted, text_length > 0 | ✓ |
| Step 3: Ask about document | Response references document content | ✓ |
| Upload multiple documents | All documents searchable | ✓ |
| Ask vague question | System retrieves relevant doc chunks | ✓ |
| Ask non-related question | System returns best match from document | ✓ |

---

## Sample Test Documents

### Test Case 1: Blood Report
**Document Content:**
```
BLOOD TEST REPORT
Patient: John Doe
Date: January 8, 2026

Hemoglobin: 14.5 g/dL (Normal: 13.5-17.5)
Red Blood Cells: 4.8 million/µL
White Blood Cells: 7,200/µL
Platelets: 250,000/µL

Blood Sugar: 95 mg/dL (Fasting)
Cholesterol: 180 mg/dL
```

**Test Question:** "What is my hemoglobin level?"
**Expected Answer:** Should mention "14.5 g/dL" from the document

---

### Test Case 2: Prescription Report
**Document Content:**
```
PRESCRIPTION
Patient: John Doe
Doctor: Dr. Smith
Date: January 5, 2026

1. Metformin 500mg - Twice daily for diabetes
2. Lisinopril 10mg - Once daily for hypertension
3. Atorvastatin 20mg - Once daily for cholesterol
```

**Test Question:** "What medications am I taking?"
**Expected Answer:** Should list all three medications with dosages

---

## Verification Steps

### 1. Check Document Ingestion
Look at the backend terminal output:
```
INFO: Document uploaded successfully
INFO: Text length: 2543 characters
INFO: Embeddings created: 5 chunks
```

### 2. Check Vector Store
Verify FAISS index was created:
```bash
ls -la faiss_store/
# Should show: user_id_session_id_docs.index
# Should show: user_id_session_id_docs.index.meta
```

### 3. Monitor Document Retrieval
Ask a question and check logs for RAG retrieval:
```
DEBUG: Retrieved 5 document chunks
DEBUG: Similarity scores: [0.92, 0.87, 0.81, 0.76, 0.71]
```

---

## Common Issues & Solutions

### Issue: "File is empty"
**Solution:** Make sure you're uploading an actual file, not an empty file

### Issue: "No text extracted"
**Solution:** 
- Verify PDF is readable (not scanned image without OCR)
- For images, ensure text is clearly visible
- Check image quality

### Issue: Responses don't reference document
**Solution:**
- Verify `session_id` matches between upload and query
- Check that document upload response shows `text_length > 0`
- Ask more specific questions about the document

### Issue: FAISS warning about centroids
**Solution:** This is expected initially. To fix:
1. Upload 4+ documents per session, OR
2. Modify `core/services/vector/faiss_store.py`:
   ```python
   # Change from 1000 to 3900 training points
   self.index.train(np.random.random((3900, dim)).astype("float32"))
   ```

---

## API Response Types

### When Document is Available (`type: "document_chat"`)
- System searches uploaded documents first
- References specific sections
- Provides evidence from documents

### When No Document (`type: "medical_chat"`)
- Uses general medical knowledge
- May provide disclaimers
- Follows safety guidelines

---

## Postman Collection Template

Save this as `MediBot_Collection.json`:

```json
{
  "info": {
    "name": "MediBot API Tests",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "1. Create Session",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{firebase_token}}",
            "type": "text"
          },
          {
            "key": "Content-Type",
            "value": "application/json",
            "type": "text"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"symptoms\": \"I have chest pain\",\n  \"session_id\": null\n}"
        },
        "url": {
          "raw": "{{base_url}}/analyze-symptoms",
          "host": ["{{base_url}}"],
          "path": ["analyze-symptoms"]
        }
      }
    },
    {
      "name": "2. Upload Document",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{firebase_token}}",
            "type": "text"
          }
        ],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "session_id",
              "value": "{{session_id}}",
              "type": "text"
            },
            {
              "key": "file",
              "type": "file",
              "src": "/path/to/medical_report.pdf"
            }
          ]
        },
        "url": {
          "raw": "{{base_url}}/chat/upload-document",
          "host": ["{{base_url}}"],
          "path": ["chat", "upload-document"]
        }
      }
    },
    {
      "name": "3. Query Document",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{firebase_token}}",
            "type": "text"
          },
          {
            "key": "Content-Type",
            "value": "application/json",
            "type": "text"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"symptoms\": \"What does my report say?\",\n  \"session_id\": \"{{session_id}}\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/analyze-symptoms",
          "host": ["{{base_url}}"],
          "path": ["analyze-symptoms"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "firebase_token",
      "value": ""
    },
    {
      "key": "session_id",
      "value": ""
    }
  ]
}
```

---

---

# Complete API Endpoints Reference

## 1. Authentication Endpoints (`/auth`)

### 1.1 Sign Up with Email
**Endpoint:** `POST /auth/signup/email`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (201):**
```json
{
  "idToken": "eyJhbGciOiJSUzI1NiIs...",
  "refreshToken": "AMf-vByX...",
  "expiresIn": 3600,
  "uid": "user123",
  "emailVerified": false
}
```

---

### 1.2 Login with Email
**Endpoint:** `POST /auth/login/email`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "idToken": "eyJhbGciOiJSUzI1NiIs...",
  "refreshToken": "AMf-vByX...",
  "expiresIn": 3600,
  "uid": "user123",
  "emailVerified": true
}
```

---

### 1.3 Login with Google
**Endpoint:** `POST /auth/login/google`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjExIn0..."
}
```

**Response (200):**
```json
{
  "idToken": "eyJhbGciOiJSUzI1NiIs...",
  "refreshToken": "AMf-vByX...",
  "expiresIn": 3600,
  "uid": "user123",
  "email": "user@gmail.com",
  "provider": "google.com"
}
```

---

### 1.4 Forgot Password
**Endpoint:** `POST /auth/forgot-password`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "Password reset email sent successfully",
  "email": "user@example.com"
}
```

---

## 2. Health Check Endpoint

### 2.1 Health Check
**Endpoint:** `GET /health`

**Response (200):**
```json
{
  "status": "healthy",
  "service": "MediBot API",
  "version": "v2"
}
```

---

## 3. Chat Endpoints

### 3.1 Analyze Symptoms (Chat)
**Endpoint:** `POST /analyze-symptoms`

**Headers:**
```
Authorization: Bearer {firebase_token}
Content-Type: application/json
```

**Body:**
```json
{
  "session_id": "session_123abc",
  "symptoms": "I have chest pain and shortness of breath"
}
```

**Response (200):**
```json
{
  "session_id": "session_123abc",
  "type": "medical_chat",
  "message": "Based on your symptoms, I recommend..."
}
```

**Response (200 - New Session):**
```json
{
  "session_id": "session_new456",
  "type": "medical_chat",
  "message": "Based on your symptoms...",
  "title": "Chest pain and shortness of breath",
  "is_new_session": true
}
```

---

### 3.2 List All Chat Sessions
**Endpoint:** `GET /chats`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**Response (200):**
```json
[
  {
    "session_id": "session_123abc",
    "title": "Chest pain and shortness of breath",
    "created_at": "2026-01-10T10:30:00Z",
    "updated_at": "2026-01-10T11:45:00Z",
    "message_count": 5
  },
  {
    "session_id": "session_456def",
    "title": "Headache and dizziness",
    "created_at": "2026-01-09T14:20:00Z",
    "updated_at": "2026-01-09T15:10:00Z",
    "message_count": 3
  }
]
```

---

### 3.3 Get Chat Messages
**Endpoint:** `GET /chats/{session_id}/messages`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | The session ID |

**Response (200):**
```json
[
  {
    "role": "user",
    "content": "I have chest pain",
    "timestamp": "2026-01-10T10:30:00Z"
  },
  {
    "role": "assistant",
    "content": "Chest pain can be...",
    "timestamp": "2026-01-10T10:30:30Z"
  },
  {
    "role": "user",
    "content": "What should I do?",
    "timestamp": "2026-01-10T10:31:00Z"
  },
  {
    "role": "assistant",
    "content": "I recommend you...",
    "timestamp": "2026-01-10T10:31:30Z"
  }
]
```

---

### 3.4 End Chat Session
**Endpoint:** `POST /end-chat`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**Response (200):**
```json
{
  "message": "Profile updated successfully",
  "profile": {
    "medical_history": "updated",
    "last_symptoms": "chest pain, shortness of breath",
    "last_updated": "2026-01-10T11:45:00Z"
  }
}
```

---

### 3.5 Delete Specific Chat Session
**Endpoint:** `DELETE /chats/{session_id}`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | The session ID to delete |

**Response (200):**
```json
{
  "message": "Chat session deleted",
  "session_id": "session_123abc"
}
```

---

### 3.6 Delete All Chat History
**Endpoint:** `DELETE /chats`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**Response (200):**
```json
{
  "message": "All chat history deleted successfully",
  "deleted_sessions": 5
}
```

---

## 4. Document Upload & Chat

### 4.1 Upload Document to Chat
**Endpoint:** `POST /chat/upload-document`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**Body (form-data):**
| Key | Value | Type |
|-----|-------|------|
| `session_id` | `session_123abc` | Text |
| `file` | `medical_report.pdf` | File |

**Response (200):**
```json
{
  "message": "Document attached to chat",
  "document_id": "doc_456def",
  "text_length": 2543,
  "session_id": "session_123abc"
}
```

**Usage:** Ask questions after uploading:
```
Q: "What does my report say?"
A: "Based on your uploaded report, your blood pressure is..."
```

---

## 5. Report Analysis Endpoints

### 5.1 Upload & Analyze Medical Report
**Endpoint:** `POST /analyze-report`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**Body (form-data):**
| Key | Value | Type |
|-----|-------|------|
| `file` | `lab_report.pdf` | File |
| `consent` | `true` | Text |

**Response (200):**
```json
{
  "message": "Report analyzed successfully",
  "report_type": "pdf",
  "extracted_text_preview": "BLOOD TEST REPORT\nPatient: John Doe\nHemoglobin: 14.5 g/dL...",
  "analysis": {
    "summary": "Blood test shows normal values",
    "key_findings": [
      "Hemoglobin: Normal (14.5 g/dL)",
      "Blood Sugar: Normal (95 mg/dL)",
      "Cholesterol: Normal (180 mg/dL)"
    ],
    "recommendations": "Continue regular checkups"
  },
  "profile_updated": true
}
```

---

### 5.2 Get Report History
**Endpoint:** `GET /reports/history`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Max number of reports |
| `order` | string | desc | Sort order (asc/desc) |

**Response (200):**
```json
{
  "items": [
    {
      "id": "report_123",
      "original_filename": "blood_test_2026-01-10.pdf",
      "report_type": "pdf",
      "created_at": "2026-01-10T10:30:00Z",
      "analysis": {
        "summary": "Blood test shows normal values",
        "key_findings": [...]
      }
    }
  ],
  "count": 1,
  "order": "desc"
}
```

---

### 5.3 Get Specific Report
**Endpoint:** `GET /reports/{report_id}`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `report_id` | string | The report ID |

**Response (200):**
```json
{
  "id": "report_123",
  "original_filename": "blood_test_2026-01-10.pdf",
  "report_type": "pdf",
  "created_at": "2026-01-10T10:30:00Z",
  "analysis": {
    "summary": "Blood test shows normal values",
    "key_findings": [...]
  },
  "extracted_text": "BLOOD TEST REPORT\nPatient: John Doe\n..."
}
```

---

## 6. User Profile Endpoints

### 6.1 Save User Profile
**Endpoint:** `POST /user/profile`

**Headers:**
```
Authorization: Bearer {firebase_token}
Content-Type: application/json
```

**Body:**
```json
{
  "personal_details": {
    "age": 35,
    "gender": "Male",
    "blood_type": "O+",
    "allergies": ["Peanuts", "Penicillin"],
    "chronic_conditions": ["Hypertension"],
    "medications": ["Lisinopril 10mg"],
    "emergency_contact": "555-1234"
  }
}
```

**Response (200):**
```json
{
  "message": "Profile saved successfully"
}
```

---

### 6.2 Get User Profile
**Endpoint:** `GET /user/profile`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**Response (200):**
```json
{
  "age": 35,
  "gender": "Male",
  "blood_type": "O+",
  "allergies": ["Peanuts", "Penicillin"],
  "chronic_conditions": ["Hypertension"],
  "medications": ["Lisinopril 10mg"],
  "emergency_contact": "555-1234"
}
```

---

## 7. Doctor Summary Endpoint

### 7.1 Export Doctor Summary as PDF
**Endpoint:** `GET /doctor-summary-pdf`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**Response (200):**
- File download: `doctor_summary.pdf`
- Content includes: User profile + latest report analysis

**Postman Steps:**
1. Set method to **GET**
2. Add URL: `http://localhost:8000/doctor-summary-pdf`
3. Go to **Headers** → Add `Authorization: Bearer {token}`
4. Click **Send**
5. File will be downloaded automatically

---

## 8. Feedback Endpoint

### 8.1 Submit Feedback
**Endpoint:** `POST /feedback`

**Headers:**
```
Content-Type: application/json
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `response_id` | string | ID of the response |
| `helpful` | boolean | Was response helpful? |

**Example URL:**
```
POST /feedback?response_id=resp_123&helpful=true
```

**Response (200):**
```json
{
  "status": "saved"
}
```

---

## 9. Account Management

### 9.1 Delete Account
**Endpoint:** `DELETE /account`

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**Response (200):**
```json
{
  "message": "Account deleted successfully",
  "result": {
    "chat_history_deleted": 5,
    "reports_deleted": 3,
    "profile_deleted": true
  }
}
```

**⚠️ WARNING:** This is a permanent operation. All user data will be deleted.

---

# Complete Testing Checklist

| # | Endpoint | Method | Status | Notes |
|---|----------|--------|--------|-------|
| 1 | `/auth/signup/email` | POST | ✓ | Register new user |
| 2 | `/auth/login/email` | POST | ✓ | Login with email |
| 3 | `/auth/login/google` | POST | ✓ | Login with Google |
| 4 | `/auth/forgot-password` | POST | ✓ | Reset password |
| 5 | `/health` | GET | ✓ | Health check |
| 6 | `/analyze-symptoms` | POST | ✓ | Chat with AI |
| 7 | `/chats` | GET | ✓ | List chat sessions |
| 8 | `/chats/{session_id}/messages` | GET | ✓ | Get chat history |
| 9 | `/end-chat` | POST | ✓ | End session & update profile |
| 10 | `/chats/{session_id}` | DELETE | ✓ | Delete one session |
| 11 | `/chats` | DELETE | ✓ | Delete all chats |
| 12 | `/chat/upload-document` | POST | ✓ | Upload document |
| 13 | `/analyze-report` | POST | ✓ | Upload & analyze report |
| 14 | `/reports/history` | GET | ✓ | Get report history |
| 15 | `/reports/{report_id}` | GET | ✓ | Get single report |
| 16 | `/user/profile` | POST | ✓ | Save profile |
| 17 | `/user/profile` | GET | ✓ | Get profile |
| 18 | `/doctor-summary-pdf` | GET | ✓ | Download summary PDF |
| 19 | `/feedback` | POST | ✓ | Submit feedback |
| 20 | `/account` | DELETE | ✓ | Delete account |

---

## Debugging

### Enable Verbose Logging
Add to your `config/settings.py`:
```python
LOG_LEVEL = "DEBUG"
```

### Monitor Document Retrieval
Check [core/services/rag/rag_service.py](core/services/rag/rag_service.py) for:
- Vector similarity scores
- Retrieved document chunks
- Relevance filtering

### Test Without Documents
Ask a question without uploading documents to compare responses:
- `type` should be `"medical_chat"`
- Response should be generic medical advice
