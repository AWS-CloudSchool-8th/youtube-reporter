# controllers/base_controller.py
from typing import Any, Dict
from utils.logger import setup_logger


class BaseController:
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)

    def success_response(self, data: Any, message: str = "Success") -> Dict:
        return {
            "success": True,
            "message": message,
            "data": data
        }

    def error_response(self, error: str, status_code: int = 500) -> Dict:
        return {
            "success": False,
            "error": error,
            "status_code": status_code
        }

    async def handle_request(self, func, *args, **kwargs):
        """공통 요청 처리 래퍼"""
        try:
            result = await func(*args, **kwargs)
            return self.success_response(result)
        except Exception as e:
            self.logger.error(f"Request failed: {str(e)}")
            return self.error_response(str(e))