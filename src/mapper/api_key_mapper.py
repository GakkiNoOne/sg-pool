"""API Key 数据访问层（Mapper）- 纯数据库操作"""

from typing import Optional
from sqlalchemy.orm import Session
from entity.databases.api_key import APIKey


def query_available_keys(
    db: Session, 
    limit: int = None, 
    exclude_ids: list[int] = None
) -> list[APIKey]:
    """
    查询可用的 API Key 列表
    
    Args:
        db: 数据库会话
        limit: 限制返回数量（None 表示不限制）
        exclude_ids: 需要排除的 Key ID 列表
        
    Returns:
        APIKey 对象列表
    """
    query = db.query(APIKey).filter(
        APIKey.enabled == True,
        (APIKey.balance > 0) | (APIKey.balance == None)
    )
    
    # 排除指定的 ID
    if exclude_ids:
        query = query.filter(~APIKey.id.in_(exclude_ids))
    
    # 限制数量
    if limit is not None:
        query = query.limit(limit)
    
    return query.all()

