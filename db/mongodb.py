from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client.medibot_db

users_collection = db.users
chat_sessions_collection = db.chat_sessions