"""Key 管理接口请求模型"""

from typing import Optional, List
from pydantic import BaseModel, Field


class APIKeyCreateRequest(BaseModel):
    """创建 API Key 请求"""
    name: str = Field(..., description="密钥名称")
    api_key: str = Field(..., description="API密钥")
    ua: str = Field(..., description="绑定的固定UA")
    proxy: Optional[str] = Field(None, description="绑定的代理（可选，不配置则使用本机ip）")
    enabled: bool = Field(True, description="是否启用")
    balance: Optional[float] = Field(None, description="当前余额")
    total_balance: Optional[float] = Field(None, description="总授权额度")
    memo: Optional[str] = Field(None, description="备注说明")


class APIKeyUpdateRequest(BaseModel):
    """更新 API Key 请求（不包含 ID）"""
    name: Optional[str] = Field(None, description="密钥名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    ua: Optional[str] = Field(None, description="绑定的固定UA")
    proxy: Optional[str] = Field(None, description="绑定的代理")
    enabled: Optional[bool] = Field(None, description="是否启用")
    balance: Optional[float] = Field(None, description="当前余额")
    total_balance: Optional[float] = Field(None, description="总授权额度")
    memo: Optional[str] = Field(None, description="备注说明")


class APIKeyQueryRequest(BaseModel):
    """查询 API Key 列表请求"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    name: Optional[str] = Field(None, description="密钥名称（模糊搜索）")
    enabled: Optional[bool] = Field(None, description="是否启用")
    create_date: Optional[str] = Field(None, description="创建日期（格式：YYYY-MM-DD）")
    min_balance: Optional[float] = Field(None, description="最小余额")


class APIKeyGetRequest(BaseModel):
    """获取单个 API Key 请求"""
    key_id: int = Field(..., description="Key ID")


class APIKeyDeleteRequest(BaseModel):
    """删除 API Key 请求"""
    key_id: int = Field(..., description="Key ID")


class APIKeyUpdateWithIdRequest(BaseModel):
    """更新 API Key 请求（包含 ID）"""
    key_id: int = Field(..., description="Key ID")
    name: Optional[str] = Field(None, description="密钥名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    ua: Optional[str] = Field(None, description="绑定的固定UA")
    proxy: Optional[str] = Field(None, description="绑定的代理")
    enabled: Optional[bool] = Field(None, description="是否启用")
    balance: Optional[float] = Field(None, description="当前余额")
    total_balance: Optional[float] = Field(None, description="总授权额度")
    memo: Optional[str] = Field(None, description="备注说明")


class APIKeyBatchCreateRequest(BaseModel):
    """批量创建 API Key 请求"""
    batch_name: str = Field(..., description="批次名称（作为密钥名称的前缀）")
    api_keys: List[str] = Field(..., description="API密钥列表（每行一个密钥）")


class APIKeyBatchCheckRequest(BaseModel):
    """批量测活 API Key 请求"""
    key_ids: List[int] = Field(..., description="需要测活的密钥ID列表")


class APIKeyBatchDeleteRequest(BaseModel):
    """批量删除 API Key 请求"""
    key_ids: List[int] = Field(..., description="需要删除的密钥ID列表")
