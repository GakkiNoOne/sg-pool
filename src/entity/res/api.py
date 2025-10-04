"""API 响应模型"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ==================== OpenAI Chat Completions 响应模型 ====================

class ChatCompletionMessage(BaseModel):
    """响应消息"""
    role: str = Field(..., description="角色")
    content: str = Field(..., description="内容")


class ChatCompletionChoice(BaseModel):
    """选择项"""
    index: int = Field(..., description="索引")
    message: ChatCompletionMessage = Field(..., description="消息")
    finish_reason: Optional[str] = Field(None, description="结束原因: stop/length/content_filter")


class ChatCompletionUsage(BaseModel):
    """Token使用统计"""
    prompt_tokens: int = Field(..., description="输入token数")
    completion_tokens: int = Field(..., description="输出token数")
    total_tokens: int = Field(..., description="总token数")


class ChatCompletionResponse(BaseModel):
    """OpenAI Chat Completions 响应"""
    id: str = Field(..., description="请求ID")
    object: str = Field("chat.completion", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="模型名称")
    choices: List[ChatCompletionChoice] = Field(..., description="选择列表")
    usage: ChatCompletionUsage = Field(..., description="使用统计")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1677652288,
                "model": "gpt-4",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! I'm doing well, thank you for asking."
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": 15,
                    "total_tokens": 35
                }
            }
        }


# ==================== 流式响应模型 ====================

class ChatCompletionStreamChoice(BaseModel):
    """流式响应选择项"""
    index: int = Field(..., description="索引")
    delta: Dict[str, Any] = Field(..., description="增量内容")
    finish_reason: Optional[str] = Field(None, description="结束原因")


class ChatCompletionStreamResponse(BaseModel):
    """流式响应"""
    id: str = Field(..., description="请求ID")
    object: str = Field("chat.completion.chunk", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="模型名称")
    choices: List[ChatCompletionStreamChoice] = Field(..., description="选择列表")


# ==================== 错误响应模型 ====================

class ErrorDetail(BaseModel):
    """错误详情"""
    message: str = Field(..., description="错误消息")
    type: str = Field(..., description="错误类型")
    code: str = Field(..., description="错误代码")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: ErrorDetail = Field(..., description="错误详情")

