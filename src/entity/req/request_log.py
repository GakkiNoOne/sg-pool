"""RequestLog 查询请求模型"""

from typing import Optional
from pydantic import BaseModel, Field


class RequestLogQueryRequest(BaseModel):
    """查询请求日志列表请求"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    key_id: Optional[int] = Field(None, description="Key ID 筛选")
    api_key: Optional[str] = Field(None, description="API Key 筛选（模糊搜索）")
    status: Optional[str] = Field(None, description="状态筛选: success/error")
    provider: Optional[str] = Field(None, description="提供商筛选: openai/anthropic")
    model: Optional[str] = Field(None, description="模型名称（模糊搜索）")
    start_time: Optional[str] = Field(None, description="开始时间（格式: YYYY-MM-DD HH:mm:ss）")
    end_time: Optional[str] = Field(None, description="结束时间（格式: YYYY-MM-DD HH:mm:ss）")

