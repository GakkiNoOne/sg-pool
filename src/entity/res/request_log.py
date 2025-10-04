"""RequestLog 响应模型"""

from typing import Optional
from pydantic import BaseModel


class RequestLogResponse(BaseModel):
    """请求日志响应"""
    id: int
    create_time: Optional[str]
    update_time: Optional[str]
    key_id: int
    api_key: Optional[str]
    proxy: Optional[str]
    model: str
    res_model: Optional[str]
    provider: str
    
    # Token 统计 - OpenAI 格式
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    # Token 统计 - Anthropic 格式
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    
    # 成本与性能
    cost: float
    latency_ms: Optional[int]
    
    # 状态信息
    status: str
    http_status_code: Optional[int]
    error_type: Optional[str]
    error_message: Optional[str]
    
    # 请求和响应内容
    request_body: Optional[str]
    response_body: Optional[str]

