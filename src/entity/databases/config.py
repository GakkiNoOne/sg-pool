"""系统配置模型"""

from sqlalchemy import Column, String, Text
from entity.databases.database import Base
from entity.databases.base_model import TimestampMixin


class Config(Base, TimestampMixin):
    """系统配置表"""
    
    __tablename__ = 'config'
    
    # 业务字段
    key = Column(String(100), nullable=False, unique=True, comment='配置键')
    value = Column(Text, comment='配置值（JSON格式）')
    memo = Column(Text, comment='配置说明')
    
    def __repr__(self):
        return f"<Config(id={self.id}, key='{self.key}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'key': self.key,
            'value': self.value,
            'memo': self.memo,
        }

