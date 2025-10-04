"""Admin 后台认证工具"""

from fastapi import Cookie, HTTPException, status
from typing import Optional
from utils.jwt_utils import verify_token


async def verify_admin_token(auth: Optional[str] = Cookie(None)) -> str:
    """
    验证 Admin JWT Token（从 Cookie 中获取）
    
    Args:
        auth: 从 Cookie 中获取的 JWT token
    
    Returns:
        用户名（验证成功时）
    
    Raises:
        HTTPException: 验证失败时抛出 401 异常
    """
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login first.",
        )
    
    username = verify_token(auth)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please login again.",
        )
    
    return username

