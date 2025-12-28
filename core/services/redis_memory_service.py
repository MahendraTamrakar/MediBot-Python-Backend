class RedisMemoryService:
    def __init__(self, redis_client):
        self.redis = redis_client

    def key(self, uid, session_id):
        return f"chat:{uid}:{session_id}"

    def append(self, uid, session_id, message):
        self.redis.rpush(self.key(uid, session_id), message)

    def get(self, uid, session_id):
        return self.redis.lrange(self.key(uid, session_id), 0, -1)

    def clear(self, uid, session_id):
        self.redis.delete(self.key(uid, session_id))

    def clear_all_for_user(self, firebase_uid: str):
        pattern = f"chat:{firebase_uid}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)