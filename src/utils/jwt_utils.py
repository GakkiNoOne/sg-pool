"""JWT 工具类 - 用于生成和验证 JWT Token"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from configs.config import settings


def create_access_token(username: str) -> str:
    """
    创建 JWT Access Token
    
    Args:
        username: 用户名
    
    Returns:
        JWT token 字符串
    """
    expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS)
    
    payload = {
        "sub": username,  # subject - 用户标识
        "exp": expire,    # expiration time - 过期时间
        "iat": datetime.utcnow(),  # issued at - 签发时间
    }
    
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token


def verify_token(token: str) -> Optional[str]:
    """
    验证 JWT Token
    
    Args:
        token: JWT token 字符串
    
    Returns:
        用户名（验证成功时）或 None（验证失败时）
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        return username
    except jwt.ExpiredSignatureError:
        # Token 已过期
        return None
    except jwt.InvalidTokenError:
        # Token 无效
        return None

