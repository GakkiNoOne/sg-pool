"""API 请求模型"""

from typing import List, Optional, Dict, Union, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """聊天消息"""
    role: Literal["system", "user", "assistant", "function"] = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    name: Optional[str] = Field(None, description="消息发送者名称")


class ChatCompletionRequest(BaseModel):
    """OpenAI Chat Completions 请求"""
    model: str = Field(..., description="模型名称", examples=["gpt-4", "gpt-3.5-turbo"])
    messages: List[ChatMessage] = Field(..., description="消息列表")
    
    # 可选参数
    api_key: Optional[str] = Field(None, description="指定使用的 API Key")
    proxy: Optional[str] = Field(None, description="代理地址，如: http://proxy.example.com:8080")
    temperature: Optional[float] = Field(1.0, ge=0, le=2, description="采样温度")
    top_p: Optional[float] = Field(1.0, ge=0, le=1, description="核采样参数")
    n: Optional[int] = Field(1, ge=1, le=10, description="生成的回复数量")
    stream: Optional[bool] = Field(False, description="是否流式返回")
    stop: Optional[Union[str, List[str]]] = Field(None, description="停止序列")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大token数")
    presence_penalty: Optional[float] = Field(0, ge=-2, le=2, description="存在惩罚")
    frequency_penalty: Optional[float] = Field(0, ge=-2, le=2, description="频率惩罚")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="logit偏置")
    user: Optional[str] = Field(None, description="用户标识")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "temperature": 0.7,
                "stream": False
            }
        }

