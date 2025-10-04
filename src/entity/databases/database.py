"""数据库引擎与会话管理"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from configs.config import settings


# 创建引擎
# check_same_thread=False 是 SQLite 特有的配置，允许多线程访问
# StaticPool 用于测试环境，生产环境可以使用默认的连接池
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=settings.DB_ECHO,  # 从配置读取是否打印 SQL
)

# 创建 SessionLocal 类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 基础模型类
class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


def get_db():
    """获取数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

