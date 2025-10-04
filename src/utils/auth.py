"""API 鉴权工具"""

from fastapi import Header, HTTPException, status
from configs.config import settings


async def verify_api_secret(authorization: str = Header(None)) -> bool:
    """
    验证 API Secret（Bearer Token）
    
    Args:
        authorization: Authorization header，格式为 "Bearer {API_SECRET}"
    
    Returns:
        True if valid
        
    Raises:
        HTTPException: 如果鉴权失败
    """
    # 如果未配置 API_SECRET，跳过鉴权
    if not settings.API_SECRET:
        return True
    
    # 检查 Authorization header 是否存在
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查格式是否正确
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证 token
    token = parts[1]
    if token != settings.API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API secret",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True

