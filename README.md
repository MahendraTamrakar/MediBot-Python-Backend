# 🏥 MediBot - AI Medical Assistant Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A sophisticated AI-powered medical chatbot backend built with FastAPI, featuring real-time chat capabilities, medical report analysis, RAG-based knowledge retrieval, and multi-agent orchestration for accurate medical assistance.

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Endpoints](#-api-endpoints)
- [Docker Deployment](#-docker-deployment)
- [Services Overview](#-services-overview)
- [Agents Architecture](#-agents-architecture)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### Core Capabilities
- 🤖 **AI-Powered Medical Chat** - Real-time streaming responses with context-aware conversations
- 📄 **Medical Report Analysis** - OCR-based extraction and analysis of medical reports (PDF/Images)
- 🧠 **RAG Implementation** - Retrieval-Augmented Generation with FAISS vector store
- 👨‍⚕️ **Multi-Agent System** - Specialized agents for diagnosis, compliance, and OCR
- 🔒 **Firebase Authentication** - Secure user authentication and authorization
- 💾 **Persistent Memory** - Redis-based chat history and context management
- 📊 **User Profile Management** - Dynamic medical profile updates from conversations
- 🚨 **Emergency Detection** - Automatic identification of critical medical situations
- 📚 **Document Management** - Upload and manage medical documents per chat session
- 🏥 **Doctor Summary Generation** - Comprehensive patient summaries for healthcare providers

### Advanced Features
- **Context-Aware Responses** - Maintains conversation history and user medical context
- **Follow-up Question Generation** - Intelligent follow-up suggestions
- **Safety & Compliance** - Medical ethics and safety validation layer
- **OCR Processing** - Tesseract-based text extraction from medical documents
- **Streaming Responses** - Server-Sent Events (SSE) for real-time communication
- **Health Monitoring** - Built-in health check endpoints for monitoring

## 🛠️ Tech Stack

### Backend Framework
- **FastAPI** - High-performance async web framework
- **Python 3.11** - Modern Python with type hints and async support
- **Uvicorn** - ASGI server for production deployment

### AI & Machine Learning
- **Google Gemini API** - Large Language Model for medical understanding
- **FAISS** - Facebook AI Similarity Search for vector embeddings
- **Tesseract OCR** - Optical Character Recognition for document processing

### Databases & Storage
- **MongoDB Atlas** - NoSQL database for user data and chat sessions
- **Redis Cloud** - In-memory cache for chat history and context
- **FAISS Store** - Vector database for RAG implementation

### Authentication & Security
- **Firebase Admin SDK** - User authentication and authorization
- **Firebase Auth** - Token-based authentication

### Document Processing
- **PDFPlumber** - PDF text extraction and parsing
- **Pillow (PIL)** - Image processing and manipulation
- **ReportLab** - PDF generation for reports

### DevOps & Deployment
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** (optional) - Reverse proxy and load balancing

## 🏗️ Architecture

The application follows a clean architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│  API Layer          │  Controllers (REST Endpoints)          │
├─────────────────────────────────────────────────────────────┤
│  Core Layer         │  Agents, Orchestrators, Services      │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure     │  LLM, Vector Store, External Services  │
├─────────────────────────────────────────────────────────────┤
│  Database Layer     │  MongoDB, Redis, FAISS Repositories   │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Agent System
```
User Request
     │
     ▼
┌──────────────────┐
│  Orchestrator    │
└────────┬─────────┘
         │
    ┌────┴────────────────┐
    │                     │
    ▼                     ▼
┌─────────┐         ┌──────────┐
│Diagnosis│         │Compliance│
│ Agent   │         │  Agent   │
└─────────┘         └──────────┘
    │                     │
    └──────────┬──────────┘
               ▼
        Final Response
```

## 📁 Project Structure

```
backend/
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker container configuration
├── docker-compose.yml               # Docker Compose setup
├── firebase-service-account.json    # Firebase credentials (DO NOT COMMIT)
├── .env                            # Environment variables (DO NOT COMMIT)
│
├── api/                            # API Controllers (REST Endpoints)
│   ├── chat_controller.py          # Chat endpoints with streaming
│   ├── chat_document_controller.py # Document upload for chat sessions
│   ├── chat_history_controller.py  # Chat history management
│   ├── report_controller.py        # Medical report analysis
│   ├── doctor_summary_controller.py # Doctor summary generation
│   ├── user_profile_controller.py  # User profile CRUD
│   ├── feedback_controller.py      # User feedback collection
│   └── health_controller.py        # Health check endpoint
│
├── core/                           # Core Business Logic
│   ├── agents/                     # Specialized AI Agents
│   │   ├── base_agent.py           # Abstract base agent
│   │   ├── diagnosis_agent.py      # Medical diagnosis agent
│   │   ├── compliance_agent.py     # Safety & compliance agent
│   │   └── ocr_agent.py            # OCR processing agent
│   │
│   ├── orchestrator/               # Multi-Agent Orchestration
│   │   └── diagnosis_orchestrator.py # Coordinates multiple agents
│   │
│   ├── services/                   # Business Services
│   │   ├── chat_service.py         # Main chat logic
│   │   ├── chat_history_service.py # History management
│   │   ├── context_service.py      # Context building
│   │   ├── emergency_service.py    # Emergency detection
│   │   ├── followup_service.py     # Follow-up questions
│   │   ├── compliance_service.py   # Compliance checking
│   │   ├── safety_service.py       # Safety validation
│   │   ├── ocr_service.py          # OCR processing
│   │   ├── report_analysis_service.py # Report analysis
│   │   ├── doctor_pdf_service.py   # PDF generation
│   │   ├── profile_update_service.py # Profile updates
│   │   ├── pdf_service.py          # PDF utilities
│   │   ├── faiss_service.py        # FAISS vector store
│   │   │
│   │   ├── documents/              # Document Services
│   │   │   └── chat_document_service.py
│   │   │
│   │   ├── memory/                 # Memory Services
│   │   │   └── redis_chat_memory.py
│   │   │
│   │   ├── rag/                    # RAG Implementation
│   │   │   └── rag_service.py
│   │   │
│   │   └── vector/                 # Vector Services
│   │       ├── embedding_service.py
│   │       └── faiss_store.py
│   │
│   ├── auth/                       # Authentication
│   │   ├── firebase_auth.py        # Firebase integration
│   │   └── dependencies.py         # Auth dependencies
│   │
│   └── interfaces/                 # Abstract Interfaces
│       ├── llm_interface.py        # LLM interface
│       └── safety_interface.py     # Safety interface
│
├── infrastructure/                 # External Services
│   └── llm/
│       └── gemini_llm.py          # Google Gemini integration
│
├── db/                            # Database Layer
│   ├── mongodb.py                 # MongoDB connection
│   ├── models.py                  # Database models
│   ├── users_repo.py              # User repository
│   ├── reports_repo.py            # Reports repository
│   ├── faiss_repo.py              # FAISS repository
│   └── user_details.py            # User details models
│
├── config/                        # Configuration
│   └── settings.py                # Application settings
│
├── prompts/                       # AI Prompts
│   ├── medical_prompt.py          # Medical chat prompts
│   ├── diagnosis_prompt.py        # Diagnosis prompts
│   └── profile_update_prompt.py   # Profile update prompts
│
└── faiss_store/                   # FAISS Vector Indexes
    └── *.index                    # User-specific FAISS indexes
```

## 📦 Prerequisites

### Required
- **Python 3.11+**
- **Docker & Docker Compose** (for containerized deployment)
- **MongoDB Atlas Account** (or local MongoDB instance)
- **Redis Cloud Account** (or local Redis instance)
- **Google Gemini API Key**
- **Firebase Project** with Admin SDK credentials

### Optional
- **Tesseract OCR** (for local development)
- **CUDA-enabled GPU** (for faster embeddings, optional)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/MahendraTamrakar/MediBot-Python-Backend.git
cd MediBot-Python-Backend
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Tesseract OCR (Local Development)

#### Windows:
```bash
# Download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH: C:\Program Files\Tesseract-OCR
```

#### macOS:
```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

## ⚙️ Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```env
# MongoDB Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/medibot?retryWrites=true&w=majority

# Redis Configuration
REDIS_URL=redis://username:password@redis-host:port

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-1.5-flash-latest

# Firebase Configuration
FIREBASE_PROJECT_ID=your_firebase_project_id

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 2. Firebase Service Account

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project → Project Settings → Service Accounts
3. Click "Generate New Private Key"
4. Save as `firebase-service-account.json` in the project root

**⚠️ SECURITY WARNING**: Never commit this file to version control!

### 3. MongoDB Setup

1. Create a [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) account
2. Create a new cluster
3. Create a database user
4. Whitelist your IP address (or use 0.0.0.0/0 for development)
5. Get your connection string and add to `.env`

### 4. Redis Setup

1. Create a [Redis Cloud](https://redis.com/try-free/) account
2. Create a new database
3. Get your connection URL and add to `.env`

## 🏃 Running the Application

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# Run with Uvicorn workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🐳 Docker Deployment

### Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Build Docker Image Only

```bash
# Build image
docker build -t medibot-api:latest .

# Run container
docker run -d \
  --name medibot-api \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/faiss_store:/app/faiss_store \
  -v $(pwd)/firebase-service-account.json:/app/firebase-service-account.json:ro \
  medibot-api:latest
```

### Health Check

```bash
# Check container health
docker ps

# Check API health
curl http://localhost:8000/health
```

## 📡 API Endpoints

### Health & Status
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Health check | No |

### Chat
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/chat/stream` | Streaming chat with AI | Yes |
| GET | `/chat/history` | Get chat history | Yes |
| DELETE | `/chat/history/{chat_id}` | Delete chat session | Yes |

### Documents
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/chat-documents/upload` | Upload document to chat | Yes |
| GET | `/chat-documents/{chat_id}` | Get chat documents | Yes |
| DELETE | `/chat-documents/{document_id}` | Delete document | Yes |

### Medical Reports
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/analyze-report` | Upload & analyze report | Yes |
| GET | `/reports` | Get user reports | Yes |
| GET | `/reports/{report_id}` | Get specific report | Yes |
| DELETE | `/reports/{report_id}` | Delete report | Yes |

### User Profile
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/profile` | Get user profile | Yes |
| PUT | `/profile` | Update user profile | Yes |
| DELETE | `/profile` | Delete user profile | Yes |

### Doctor Summary
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/doctor-summary` | Generate doctor summary | Yes |
| GET | `/doctor-summary/{summary_id}` | Get summary PDF | Yes |

### Request/Response Examples

#### Chat Stream Request
```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have been experiencing headaches for 3 days",
    "chat_id": "chat_001"
  }'
```

#### Analyze Report Request
```bash
curl -X POST "http://localhost:8000/analyze-report" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -F "file=@report.pdf" \
  -F "consent=true"
```

## 🔧 Services Overview

### Chat Service
Manages real-time chat interactions with streaming responses, context management, and emergency detection.

**Key Features:**
- Streaming SSE responses
- Context-aware conversations
- Emergency keyword detection
- Follow-up question generation
- Safety and compliance validation

### RAG Service
Implements Retrieval-Augmented Generation for knowledge-based responses.

**Components:**
- **FAISS Vector Store**: Similarity search for relevant documents
- **Embedding Service**: Text-to-vector conversion using Gemini
- **Document Indexing**: Automatic indexing of uploaded documents

### OCR Service
Extracts text from medical reports (PDF and images).

**Capabilities:**
- PDF text extraction with PDFPlumber
- Image OCR with Tesseract
- Multi-page document processing
- Text cleanup and formatting

### Report Analysis Service
Analyzes medical reports and extracts structured information.

**Output:**
- Report summary
- Key findings and abnormalities
- Recommendations
- Diagnostic insights

### Profile Update Service
Dynamically updates user medical profiles from conversations.

**Features:**
- Intelligent extraction of medical information
- Merge with existing profile data
- Consent-based updates
- Structured data storage

## 🤖 Agents Architecture

### Base Agent
Abstract base class for all specialized agents.

```python
class BaseAgent(ABC):
    @abstractmethod
    async def process(self, input_data: Dict) -> Dict:
        pass
```

### Diagnosis Agent
Provides medical diagnosis suggestions based on symptoms.

**Responsibilities:**
- Symptom analysis
- Differential diagnosis
- Severity assessment
- Treatment recommendations

### Compliance Agent
Ensures responses meet medical ethics and safety standards.

**Checks:**
- Medical disclaimer inclusion
- Appropriate language
- Emergency escalation triggers
- Regulatory compliance

### OCR Agent
Processes medical documents and extracts relevant information.

**Functions:**
- Document type detection
- Text extraction
- Data normalization
- Information categorization

### Diagnosis Orchestrator
Coordinates multiple agents for comprehensive responses.

**Flow:**
```
User Input → Context Building → Diagnosis Agent → Compliance Agent → Response
```

## 🔒 Authentication

The API uses Firebase Authentication with JWT tokens.

### Authentication Flow

1. **Client**: Authenticate with Firebase (Frontend/Mobile App)
2. **Client**: Get Firebase ID Token
3. **Client**: Send token in `Authorization` header
4. **Backend**: Verify token with Firebase Admin SDK
5. **Backend**: Extract user ID and process request

### Protected Endpoints

All endpoints except `/health` require authentication.

**Example Header:**
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

## 📊 Monitoring & Logging

### Health Check
```bash
curl http://localhost:8000/health
```

### Container Logs
```bash
# View logs
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Python Logging
Logs are configured in each module:
- **INFO**: General information
- **WARNING**: Warning messages
- **ERROR**: Error messages with stack traces

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the Repository**
2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit Your Changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push to the Branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open a Pull Request**

### Code Style Guidelines
- Follow PEP 8 for Python code
- Use type hints
- Write docstrings for functions and classes
- Add unit tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern web framework
- **Google Gemini** - Advanced AI capabilities
- **Firebase** - Authentication and security
- **MongoDB** - Flexible data storage
- **Redis** - Fast in-memory caching
- **FAISS** - Efficient vector similarity search

## 📞 Support

For questions or issues:
- **GitHub Issues**: [Report Bug](https://github.com/MahendraTamrakar/MediBot-Python-Backend/issues)
- **Email**: support@medibot.example.com

## 🔄 Roadmap

- [ ] Voice input/output support
- [ ] Multi-language support
- [ ] Integration with EHR systems
- [ ] Advanced analytics dashboard
- [ ] Mobile SDK
- [ ] Telemedicine integration
- [ ] Prescription management
- [ ] Appointment scheduling

---

**⚕️ Disclaimer**: MediBot is an AI assistant for informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified health providers with any questions regarding medical conditions.

**Made with ❤️ by the MediBot Team**
