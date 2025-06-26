import json
from typing import Dict, Any, Optional, List
from app.core.redis_client import redis_client

class ElastiCacheStateManager:
    def __init__(self):
        self.redis = redis_client
    
    def save_step_state(self, job_id: str, step: str, data: dict, ttl: int = 3600):
        """단계별 상태 저장"""
        key = f"langgraph:{job_id}:step:{step}"
        self.redis.set_with_ttl(key, data, ttl)
    
    def get_step_state(self, job_id: str, step: str) -> Optional[dict]:
        """특정 단계 상태 조회"""
        key = f"langgraph:{job_id}:step:{step}"
        return self.redis.get(key)
    
    def get_full_state(self, job_id: str) -> dict:
        """전체 상태 조회"""
        pattern = f"langgraph:{job_id}:step:*"
        keys = self.redis.get_keys_by_pattern(pattern)
        
        full_state = {}
        for key in keys:
            step_name = key.split(":")[-1]
            step_data = self.redis.get(key)
            if step_data:
                full_state[step_name] = step_data
        
        return full_state
    
    def update_progress(self, job_id: str, progress: int, message: str = ""):
        """진행률 업데이트"""
        key = f"progress:{job_id}"
        progress_data = {
            "progress": progress,
            "message": message,
            "updated_at": str(datetime.utcnow())
        }
        self.redis.set_with_ttl(key, progress_data, 3600)
    
    def get_progress(self, job_id: str) -> Optional[dict]:
        """진행률 조회"""
        key = f"progress:{job_id}"
        return self.redis.get(key)
    
    def cleanup_job(self, job_id: str):
        """작업 완료 후 Redis 정리"""
        patterns = [
            f"langgraph:{job_id}:*",
            f"progress:{job_id}"
        ]
        
        for pattern in patterns:
            keys = self.redis.get_keys_by_pattern(pattern)
            for key in keys:
                self.redis.delete(key)
    
    def add_user_active_job(self, user_id: str, job_id: str):
        """사용자 활성 작업 추가"""
        key = f"user:{user_id}:active_jobs"
        active_jobs = self.redis.get(key) or []
        if job_id not in active_jobs:
            active_jobs.append(job_id)
            self.redis.set_with_ttl(key, active_jobs, 86400)  # 24시간
    
    def remove_user_active_job(self, user_id: str, job_id: str):
        """사용자 활성 작업 제거"""
        key = f"user:{user_id}:active_jobs"
        active_jobs = self.redis.get(key) or []
        if job_id in active_jobs:
            active_jobs.remove(job_id)
            self.redis.set_with_ttl(key, active_jobs, 86400)
    
    def get_user_active_jobs(self, user_id: str) -> List[str]:
        """사용자 활성 작업 목록"""
        key = f"user:{user_id}:active_jobs"
        return self.redis.get(key) or []

from datetime import datetime
state_manager = ElastiCacheStateManager()