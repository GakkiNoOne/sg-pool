"""API密钥模型"""

from sqlalchemy import Column, String, Boolean, DECIMAL, DateTime, Text
from entity.databases.database import Base
from entity.databases.base_model import TimestampMixin


class APIKey(Base, TimestampMixin):
    """API密钥管理表"""
    
    __tablename__ = 'api_keys'
    
    # 业务字段
    name = Column(String(100), nullable=False, comment='密钥名称/别名')
    api_key = Column(String(256), nullable=False, comment='API密钥（建议加密存储）')
    ua = Column(String(256), nullable=False, comment='绑定的固定UA')
    proxy = Column(String(256), nullable=True, comment='绑定的代理（可选）')
    enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    balance = Column(DECIMAL(10, 2), comment='当前余额')
    total_balance = Column(DECIMAL(10, 2), comment='总授权额度')
    balance_last_update = Column(DateTime, comment='余额最后更新时间')
    error_code = Column(String(50), comment='错误代码（如：UNAUTHORIZED, RATE_LIMIT 等）')
    memo = Column(Text, comment='备注说明')
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', enabled={self.enabled})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'name': self.name,
            'api_key': self.api_key,
            'ua': self.ua,
            'proxy': self.proxy,
            'enabled': self.enabled,
            'balance': float(self.balance) if self.balance else None,
            'total_balance': float(self.total_balance) if self.total_balance else None,
            'balance_last_update': self.balance_last_update.isoformat() if self.balance_last_update else None,
            'error_code': self.error_code,
            'memo': self.memo,
        }

