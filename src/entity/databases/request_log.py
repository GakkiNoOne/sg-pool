"""请求日志模型"""

from sqlalchemy import Column, Integer, String, DECIMAL, Text
from entity.databases.database import Base
from entity.databases.base_model import TimestampMixin


class RequestLog(Base, TimestampMixin):
    """请求日志表"""
    
    __tablename__ = 'api_request_log'
    
    # 业务字段
    key_id = Column(Integer, default=0, comment='使用的API Key ID (从池中选择时)')
    api_key = Column(String(255), comment='实际使用的 API Key (参数指定时)')
    proxy = Column(String(255), comment='使用的代理地址')
    
    # 请求信息
    model = Column(String(100), comment='请求使用的模型')
    res_model = Column(String(100), comment='响应返回的实际模型')
    provider = Column(String(20), comment='API 提供商: openai/anthropic')
    
    # Token 统计 - OpenAI 格式
    prompt_tokens = Column(Integer, default=0, comment='提示词 token 数 (OpenAI)')
    completion_tokens = Column(Integer, default=0, comment='补全 token 数 (OpenAI)')
    total_tokens = Column(Integer, default=0, comment='总 token 数')
    
    # Token 统计 - Anthropic 格式
    input_tokens = Column(Integer, default=0, comment='输入 token 数 (Anthropic)')
    output_tokens = Column(Integer, default=0, comment='输出 token 数 (Anthropic)')
    cache_creation_input_tokens = Column(Integer, default=0, comment='缓存创建输入 token 数 (Anthropic)')
    cache_read_input_tokens = Column(Integer, default=0, comment='缓存读取输入 token 数 (Anthropic)')
    
    # 成本与性能
    cost = Column(DECIMAL(10, 6), default=0, comment='成本（美元）')
    latency_ms = Column(Integer, comment='请求延迟（毫秒）')
    
    # 状态信息
    status = Column(String(20), nullable=False, comment='success/error')
    http_status_code = Column(Integer, comment='HTTP状态码')
    error_type = Column(String(100), comment='错误类型')
    error_message = Column(Text, comment='错误详细信息')
    
    # 请求和响应内容
    request_body = Column(Text, comment='请求 body（JSON）')
    response_body = Column(Text, comment='响应 body（JSON）')
    
    def __repr__(self):
        return f"<RequestLog(id={self.id}, key_id={self.key_id}, model='{self.model}', status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'key_id': self.key_id,
            'api_key': self.api_key,
            'proxy': self.proxy,
            'model': self.model,
            'res_model': self.res_model,
            'provider': self.provider,
            # OpenAI tokens
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            # Anthropic tokens
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'cache_creation_input_tokens': self.cache_creation_input_tokens,
            'cache_read_input_tokens': self.cache_read_input_tokens,
            # 其他字段
            'cost': float(self.cost) if self.cost else 0,
            'latency_ms': self.latency_ms,
            'status': self.status,
            'http_status_code': self.http_status_code,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'request_body': self.request_body,
            'response_body': self.response_body,
        }

