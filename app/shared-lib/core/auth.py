from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.services.cognito_service import verify_access_token
from typing import Dict

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """현재 사용자 정보 조회"""
    try:
        token = credentials.credentials
        
        # Cognito 토큰 검증
        result = verify_access_token(token)
        
        if not result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 사용자 정보 반환
        return {
            "user_id": result["username"],
            "token": token
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
