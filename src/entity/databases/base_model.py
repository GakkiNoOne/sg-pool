"""基础模型类 - 包含所有表的公共字段"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class TimestampMixin:
    """时间戳混入类 - 所有表的固定字段"""
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    create_time = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment='更新时间')

