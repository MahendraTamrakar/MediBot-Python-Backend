import ssl
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import MONGO_URI

client = AsyncIOMotorClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(), 
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
    socketTimeoutMS=30000
)

db = client.medibot_db

#core collections
medical_reports_collection = db.medical_reports
users_collection = db.users
chat_sessions_collection = db.chat_sessions

# FAISS metadata collection
faiss_indexes_collection = db.faiss_indexes