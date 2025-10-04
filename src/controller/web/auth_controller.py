"""管理后台认证接口"""

from fastapi import APIRouter, HTTPException, status, Response
from pydantic import BaseModel
from configs.config import settings
from utils.jwt_utils import create_access_token
from utils.logger import logger


router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    message: str
    token: str = None


@router.post("/login", response_model=LoginResponse, summary="管理员登录")
async def login(request: LoginRequest, response: Response):
    """
    管理员登录接口
    - 验证用户名和密码
    - 生成 JWT token
    - 设置 Cookie（key: auth, httpOnly: true, 有效期: 30天）
    """
    # 验证用户名和密码
    if request.username != settings.ADMIN_USERNAME or request.password != settings.ADMIN_PASSWORD:
        logger.warning(f"登录失败: 用户名或密码错误 (username: {request.username})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # 生成 JWT token
    token = create_access_token(request.username)
    
    # 设置 Cookie（有效期 30 天）
    max_age = settings.JWT_EXPIRE_DAYS * 24 * 60 * 60  # 转换为秒
    response.set_cookie(
        key="auth",
        value=token,
        max_age=max_age,
        httponly=True,  # 防止 XSS 攻击
        samesite="lax",  # CSRF 保护
        secure=False,  # 生产环境建议设置为 True（需要 HTTPS）
    )
    
    logger.info(f"用户 {request.username} 登录成功")
    
    return LoginResponse(
        success=True,
        message="Login successful",
        token=token
    )


@router.post("/logout", summary="管理员登出")
async def logout(response: Response):
    """
    管理员登出接口
    - 清除 Cookie
    """
    response.delete_cookie(key="auth")
    
    logger.info("用户登出")
    
    return {
        "success": True,
        "message": "Logout successful"
    }

