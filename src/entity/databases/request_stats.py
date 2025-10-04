"""请求统计模型"""

from sqlalchemy import Column, Integer, String, DECIMAL, Date, BigInteger, Index
from entity.databases.database import Base
from entity.databases.base_model import TimestampMixin


class RequestStats(Base, TimestampMixin):
    """统计汇总表 - 支持多维度统计"""
    
    __tablename__ = 'api_request_stats'
    
    # 统计维度
    stat_date = Column(Date, nullable=False, comment='统计日期')
    stat_hour = Column(Integer, comment='统计小时（0-23），NULL表示全天')
    stat_type = Column(String(20), nullable=False, default='global', comment='统计类型: global/provider/model/key')
    provider = Column(String(50), comment='提供商: openai/anthropic，NULL表示全部')
    model = Column(String(100), comment='模型名称，NULL表示全部')
    key_id = Column(Integer, comment='API Key ID，NULL表示全局')
    
    # 请求统计
    request_count = Column(Integer, default=0, comment='总请求数')
    success_count = Column(Integer, default=0, comment='成功请求数')
    error_count = Column(Integer, default=0, comment='失败请求数')
    
    # Token统计 - OpenAI 格式
    prompt_tokens = Column(BigInteger, default=0, comment='提示词 token (OpenAI)')
    completion_tokens = Column(BigInteger, default=0, comment='补全 token (OpenAI)')
    
    # Token统计 - Anthropic 格式
    input_tokens = Column(BigInteger, default=0, comment='输入 token (Anthropic)')
    output_tokens = Column(BigInteger, default=0, comment='输出 token (Anthropic)')
    cache_creation_tokens = Column(BigInteger, default=0, comment='缓存创建 token (Anthropic)')
    cache_read_tokens = Column(BigInteger, default=0, comment='缓存读取 token (Anthropic)')
    
    # 总Token统计
    total_tokens = Column(BigInteger, default=0, comment='总 token 数')
    
    # 成本统计
    total_cost = Column(DECIMAL(12, 6), default=0, comment='总成本（美元）')
    
    # 性能统计
    avg_latency_ms = Column(Integer, comment='平均延迟（毫秒）')
    max_latency_ms = Column(Integer, comment='最大延迟（毫秒）')
    min_latency_ms = Column(Integer, comment='最小延迟（毫秒）')
    
    # 创建索引以优化查询
    __table_args__ = (
        Index('idx_stat_date_hour', 'stat_date', 'stat_hour'),
        Index('idx_stat_type_date', 'stat_type', 'stat_date'),
        Index('idx_provider_date', 'provider', 'stat_date'),
        Index('idx_model_date', 'model', 'stat_date'),
    )
    
    def __repr__(self):
        return f"<RequestStats(id={self.id}, date={self.stat_date}, key_id={self.key_id}, model='{self.model}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'stat_date': self.stat_date.isoformat() if self.stat_date else None,
            'stat_hour': self.stat_hour,
            'stat_type': self.stat_type,
            'provider': self.provider,
            'model': self.model,
            'key_id': self.key_id,
            'request_count': self.request_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            # OpenAI tokens
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            # Anthropic tokens
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'cache_creation_tokens': self.cache_creation_tokens,
            'cache_read_tokens': self.cache_read_tokens,
            # Total
            'total_tokens': self.total_tokens,
            'total_cost': float(self.total_cost) if self.total_cost else 0,
            'avg_latency_ms': self.avg_latency_ms,
            'max_latency_ms': self.max_latency_ms,
            'min_latency_ms': self.min_latency_ms,
        }

