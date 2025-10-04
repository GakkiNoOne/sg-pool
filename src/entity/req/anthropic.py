"""Anthropic API 请求/响应实体"""

from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


class AnthropicMessage(BaseModel):
    """Anthropic 消息格式"""
    role: str = Field(..., description="角色: user 或 assistant")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="消息内容")


class AnthropicRequest(BaseModel):
    """Anthropic Messages API 请求"""
    model: str = Field(..., description="模型名称", examples=["claude-sonnet-4-5-20250929"])
    messages: List[AnthropicMessage] = Field(..., description="消息列表")
    max_tokens: int = Field(..., ge=1, description="最大生成 token 数")
    
    # 可选参数
    api_key: Optional[str] = Field(None, description="指定使用的 API Key")
    proxy: Optional[str] = Field(None, description="代理地址")
    system: Optional[str] = Field(None, description="系统提示")
    temperature: Optional[float] = Field(None, ge=0, le=1, description="采样温度")
    top_p: Optional[float] = Field(None, ge=0, le=1, description="核采样参数")
    top_k: Optional[int] = Field(None, ge=0, description="Top-K 采样")
    stop_sequences: Optional[List[str]] = Field(None, description="停止序列")
    stream: Optional[bool] = Field(False, description="是否流式返回")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": "Hello, Claude"}
                ]
            }
        }

