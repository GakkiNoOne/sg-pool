"""RequestLog 数据访问层（Mapper）"""

from sqlalchemy.orm import Session
from entity.databases.request_log import RequestLog


def insert_request_log(db: Session, log_data: dict) -> RequestLog:
    """
    插入请求日志
    
    Args:
        db: 数据库会话
        log_data: 日志数据字典
        
    Returns:
        RequestLog 对象
    """
    log = RequestLog(**log_data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def query_logs_by_key(db: Session, key_id: int, limit: int = 100) -> list[RequestLog]:
    """
    查询指定 Key 的日志
    
    Args:
        db: 数据库会话
        key_id: Key ID
        limit: 限制数量
        
    Returns:
        RequestLog 列表
    """
    return db.query(RequestLog).filter(
        RequestLog.key_id == key_id
    ).order_by(RequestLog.create_time.desc()).limit(limit).all()


def query_recent_logs(db: Session, limit: int = 100) -> list[RequestLog]:
    """
    查询最近的日志
    
    Args:
        db: 数据库会话
        limit: 限制数量
        
    Returns:
        RequestLog 列表
    """
    return db.query(RequestLog).order_by(
        RequestLog.create_time.desc()
    ).limit(limit).all()

