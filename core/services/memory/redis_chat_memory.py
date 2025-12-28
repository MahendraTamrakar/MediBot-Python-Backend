import json
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

class RedisChatMemory:
    def __init__(self, url: str):
        self.client = redis.from_url(url, decode_responses=True)
        self.connected = None  # Will be set on first operation

    async def _ensure_connection(self):
        """Check if Redis is available"""
        if self.connected is None:
            try:
                await self.client.ping()
                self.connected = True
                logger.info("Redis connection established")
            except Exception as e:
                self.connected = False
                logger.warning(f"Redis unavailable: {e}. Continuing without Redis memory.")
        return self.connected

    async def save_message(self, user_id: str, session_id: str, role: str, content: str):
        if not await self._ensure_connection():
            return  # Silently skip if Redis unavailable
        
        try:
            key = f"chat:{user_id}:{session_id}"
            await self.client.rpush(key, json.dumps({
                "role": role,
                "content": content
            }))
            await self.client.expire(key, 60 * 60 * 24)  # 24h TTL
        except Exception as e:
            logger.warning(f"Failed to save message to Redis: {e}")

    async def get_recent_messages(self, user_id: str, session_id: str, limit=6):
        if not await self._ensure_connection():
            return []  # Return empty list if Redis unavailable
        
        try:
            key = f"chat:{user_id}:{session_id}"
            messages = await self.client.lrange(key, -limit, -1)
            return [json.loads(m) for m in messages]
        except Exception as e:
            logger.warning(f"Failed to get messages from Redis: {e}")
            return []

    async def clear(self, user_id: str, session_id: str):
        """Clear all messages for a session from Redis"""
        if not await self._ensure_connection():
            return  # Silently skip if Redis unavailable
        
        try:
            key = f"chat:{user_id}:{session_id}"
            await self.client.delete(key)
            logger.info(f"Cleared Redis memory for session: {session_id}")
        except Exception as e:
            logger.warning(f"Failed to clear Redis memory: {e}")

    async def clear_all_for_user(self, user_id: str):
        """Clear all sessions for a user from Redis"""
        if not await self._ensure_connection():
            return  # Silently skip if Redis unavailable
        
        try:
            pattern = f"chat:{user_id}:*"
            cursor = 0
            deleted_count = 0
            
            # Use SCAN to iterate through keys matching the pattern
            while True:
                cursor, keys = await self.client.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.client.delete(*keys)
                    deleted_count += len(keys)
                if cursor == 0:
                    break
            
            logger.info(f"Cleared {deleted_count} Redis sessions for user: {user_id}")
        except Exception as e:
            logger.warning(f"Failed to clear all Redis sessions: {e}")