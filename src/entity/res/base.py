"""统一响应对象"""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

# 定义泛型类型变量
T = TypeVar('T')

# 响应码常量
SUCCESS_CODE = 200
FAIL_CODE = 500

# 响应消息常量
SUCCESS_MSG = "success"
FAIL_MSG = "fail"


class Response(BaseModel, Generic[T]):
    """统一响应对象（泛型）"""
    
    code: int = Field(SUCCESS_CODE, description="响应码")
    msg: str = Field(SUCCESS_MSG, description="响应消息")
    success: bool = Field(True, description="是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    
    @classmethod
    def ok(cls, data: Optional[T] = None, msg: str = SUCCESS_MSG) -> "Response[T]":
        """成功响应"""
        return cls(
            code=SUCCESS_CODE,
            msg=msg,
            success=True,
            data=data
        )
    
    @classmethod
    def fail(cls, msg: str = FAIL_MSG, code: int = FAIL_CODE) -> "Response[T]":
        """失败响应"""
        return cls(
            code=code,
            msg=msg,
            success=False,
            data=None
        )
    
    @classmethod
    def fail_ok(cls, msg: str, data: Optional[T] = None) -> "Response[T]":
        """业务失败但HTTP成功"""
        return cls(
            code=SUCCESS_CODE,
            msg=msg,
            success=False,
            data=data
        )


class ListResponse(BaseModel, Generic[T]):
    """列表响应对象（泛型）"""
    
    code: int = Field(SUCCESS_CODE, description="响应码")
    msg: str = Field(SUCCESS_MSG, description="响应消息")
    success: bool = Field(True, description="是否成功")
    data: Optional[List[T]] = Field(None, description="列表数据")
    
    @classmethod
    def ok(cls, data: Optional[List[T]] = None, msg: str = SUCCESS_MSG) -> "ListResponse[T]":
        """成功响应"""
        return cls(
            code=SUCCESS_CODE,
            msg=msg,
            success=True,
            data=data or []
        )
    
    @classmethod
    def fail(cls, msg: str = FAIL_MSG, code: int = FAIL_CODE) -> "ListResponse[T]":
        """失败响应"""
        return cls(
            code=code,
            msg=msg,
            success=False,
            data=[]
        )
    
    @classmethod
    def fail_ok(cls, msg: str) -> "ListResponse[T]":
        """业务失败但HTTP成功"""
        return cls(
            code=SUCCESS_CODE,
            msg=msg,
            success=False,
            data=[]
        )


class PageData(BaseModel, Generic[T]):
    """分页数据"""
    items: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(0, description="总数量")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(10, description="每页数量")


class PageResponse(BaseModel, Generic[T]):
    """分页响应对象（泛型）"""
    
    code: int = Field(SUCCESS_CODE, description="响应码")
    msg: str = Field(SUCCESS_MSG, description="响应消息")
    success: bool = Field(True, description="是否成功")
    data: Optional[PageData[T]] = Field(None, description="分页数据")
    
    @classmethod
    def ok(
        cls,
        items: List[T],
        total: int,
        page: int = 1,
        page_size: int = 10,
        msg: str = SUCCESS_MSG
    ) -> "PageResponse[T]":
        """成功响应"""
        return cls(
            code=SUCCESS_CODE,
            msg=msg,
            success=True,
            data=PageData(
                items=items,
                total=total,
                page=page,
                page_size=page_size
            )
        )
    
    @classmethod
    def fail(cls, msg: str = FAIL_MSG, code: int = FAIL_CODE) -> "PageResponse[T]":
        """失败响应"""
        return cls(
            code=code,
            msg=msg,
            success=False,
            data=PageData(items=[], total=0, page=1, page_size=10)
        )

