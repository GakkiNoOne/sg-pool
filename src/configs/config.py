"""应用配置"""

import os
from pathlib import Path
from typing import Optional


def normalize_path_prefix(prefix: str) -> str:
    """
    规范化路径前缀，支持多种格式：
    - x -> /x
    - /x -> /x
    - /x/ -> /x
    - x/ -> /x
    
    Args:
        prefix: 原始路径前缀
        
    Returns:
        规范化后的路径前缀（格式：/xxx，前面有斜杠，后面没有）
    """
    if not prefix:
        return ""
    
    # 去除首尾空格
    prefix = prefix.strip()
    
    # 如果是空字符串，返回空
    if not prefix:
        return ""
    
    # 去除尾部的斜杠
    prefix = prefix.rstrip('/')
    
    # 确保前面有斜杠
    if not prefix.startswith('/'):
        prefix = '/' + prefix
    
    return prefix


class Settings:
    """应用配置"""
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "6777"))
    
    # API 配置（从环境变量读取）
    # 自动规范化路径格式（支持 x, /x, /x/ 等格式）
    API_PREFIX: str = normalize_path_prefix(os.getenv("API_PREFIX", ""))  # API 路由前缀，例如 /api/v1
    API_SECRET: str = os.getenv("API_SECRET", "")  # API 密钥，用于鉴权（Bearer token）
    
    # Admin 管理后台配置（从环境变量读取）
    # 自动规范化路径格式（支持 admin, /admin, /admin/ 等格式）
    ADMIN_PREFIX: str = normalize_path_prefix(os.getenv("ADMIN_PREFIX", "/admin"))  # 管理后台路由前缀
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")  # 管理员账号
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")  # 管理员密码
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")  # JWT 密钥
    JWT_ALGORITHM: str = "HS256"  # JWT 加密算法
    JWT_EXPIRE_DAYS: int = 30  # JWT 有效期（天）

    
    # 数据库配置
    @property
    def DATABASE_DIR(self) -> str:
        """数据库文件目录"""
        base_dir = Path(__file__).parent.parent.parent  # 项目根目录
        db_dir = base_dir / "data"
        db_dir.mkdir(exist_ok=True)
        return str(db_dir)
    
    @property
    def DATABASE_PATH(self) -> str:
        """数据库文件路径"""
        return os.path.join(self.DATABASE_DIR, "amp_pool.db")
    
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        """SQLAlchemy 数据库连接字符串"""
        return f"sqlite:///{self.DATABASE_PATH}"
    
    # 数据库连接配置
    DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"  # 是否打印 SQL 语句


settings = Settings()


# 数据库初始化函数
def init_database():
    """初始化数据库（创建所有表）"""
    from entity.databases.database import Base, engine
    from entity.databases import APIKey, RequestLog, RequestStats, Config
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print(f"✅ 数据库初始化完成: {settings.DATABASE_PATH}")


def drop_database():
    """删除所有表（慎用）"""
    from entity.databases.database import Base, engine
    
    Base.metadata.drop_all(bind=engine)
    print("⚠️  所有表已删除")

