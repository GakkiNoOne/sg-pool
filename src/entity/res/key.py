"""Key 管理接口响应模型"""

from typing import Optional, List
from pydantic import BaseModel, Field


class APIKeyResponse(BaseModel):
    """API Key 响应"""
    id: int
    create_time: Optional[str]
    update_time: Optional[str]
    name: str
    api_key: str
    ua: str
    proxy: str
    enabled: bool
    balance: Optional[float]
    total_balance: Optional[float]
    balance_last_update: Optional[str]
    error_code: Optional[str]
    memo: Optional[str]


class BatchCreateResult(BaseModel):
    """批量创建结果"""
    success_count: int = Field(..., description="成功数量")
    fail_count: int = Field(..., description="失败数量")
    total_count: int = Field(..., description="总数量")
    success_keys: List[APIKeyResponse] = Field(default_factory=list, description="成功创建的密钥列表")


class KeyCheckResult(BaseModel):
    """单个密钥测活结果"""
    key_id: int = Field(..., description="密钥ID")
    key_name: str = Field(..., description="密钥名称")
    success: bool = Field(..., description="是否测活成功")
    message: str = Field(..., description="结果信息")


class BatchCheckResult(BaseModel):
    """批量测活结果"""
    success_count: int = Field(..., description="测活成功数量")
    fail_count: int = Field(..., description="测活失败数量")
    total_count: int = Field(..., description="总数量")
    results: List[KeyCheckResult] = Field(default_factory=list, description="各密钥测活结果")
