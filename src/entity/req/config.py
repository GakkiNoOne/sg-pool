"""配置管理接口请求模型"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ConfigCreateRequest(BaseModel):
    """创建配置请求"""
    key: str = Field(..., description="配置键")
    value: str = Field(..., description="配置值（JSON格式）")
    memo: Optional[str] = Field(None, description="配置说明")


class ConfigUpdateRequest(BaseModel):
    """更新配置请求（不包含 ID）"""
    key: Optional[str] = Field(None, description="配置键")
    value: Optional[str] = Field(None, description="配置值（JSON格式）")
    memo: Optional[str] = Field(None, description="配置说明")


class ConfigQueryRequest(BaseModel):
    """查询配置列表请求"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    key: Optional[str] = Field(None, description="配置键（模糊搜索）")


class ConfigGetRequest(BaseModel):
    """获取单个配置请求"""
    config_id: int = Field(..., description="配置 ID")


class ConfigDeleteRequest(BaseModel):
    """删除配置请求"""
    config_id: int = Field(..., description="配置 ID")


class ConfigUpdateWithIdRequest(BaseModel):
    """更新配置请求（包含 ID）"""
    config_id: int = Field(..., description="配置 ID")
    key: Optional[str] = Field(None, description="配置键")
    value: Optional[str] = Field(None, description="配置值（JSON格式）")
    memo: Optional[str] = Field(None, description="配置说明")

