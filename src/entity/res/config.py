"""配置管理接口响应模型"""

from typing import Optional
from pydantic import BaseModel


class ConfigResponse(BaseModel):
    """配置响应"""
    id: int
    create_time: Optional[str]
    update_time: Optional[str]
    key: str
    value: str
    memo: Optional[str]

