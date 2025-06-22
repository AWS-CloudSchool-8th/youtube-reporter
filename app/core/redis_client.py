import redis
import json
from typing import Dict, Any, Optional
from app.core.config import settings

class RedisClient:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    def set_with_ttl(self, key: str, value: Any, ttl: int = 3600):
        """TTL과 함께 값 저장"""
        self.redis.setex(key, ttl, json.dumps(value))
    
    def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        value = self.redis.get(key)
        return json.loads(value) if value else None
    
    def delete(self, key: str):
        """키 삭제"""
        self.redis.delete(key)
    
    def get_keys_by_pattern(self, pattern: str) -> list:
        """패턴으로 키 검색"""
        return self.redis.keys(pattern)

redis_client = RedisClient()