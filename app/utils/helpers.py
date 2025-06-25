import json
from typing import Any

def safe_json_dumps(data: Any) -> str:
    """안전한 JSON 직렬화"""
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"JSON 직렬화 실패: {str(e)}"

def extract_json_from_text(text: str) -> dict:
    """텍스트에서 JSON 추출"""
    try:
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_part = text[start_idx:end_idx+1]
            return json.loads(json_part)
        return {}
    except Exception:
        return {}