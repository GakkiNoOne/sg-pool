"""Web 请求日志管理控制器"""

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from entity.databases.database import get_db
from entity.req.request_log import RequestLogQueryRequest
from entity.res.request_log import RequestLogResponse
from entity.res.base import PageResponse
from service.databases import request_log_service
from utils.logger import logger
from utils.admin_auth import verify_admin_token

router = APIRouter(prefix="/api/logs", tags=["Request Log Management"], dependencies=[Depends(verify_admin_token)])


@router.post("/list", response_model=PageResponse[RequestLogResponse], summary="查询请求日志列表")
async def list_logs(
    request: RequestLogQueryRequest = Body(...),
    db: Session = Depends(get_db)
):
    """查询请求日志列表（支持分页和筛选）"""
    try:
        items, total = request_log_service.query_request_logs(
            db=db,
            page=request.page,
            page_size=request.page_size,
            key_id=request.key_id,
            api_key=request.api_key,
            status=request.status,
            provider=request.provider,
            model=request.model,
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        return PageResponse[RequestLogResponse].ok(
            items=[RequestLogResponse(**item.to_dict()) for item in items],
            total=total,
            page=request.page,
            page_size=request.page_size
        )
    except Exception as e:
        logger.error(f"查询请求日志列表失败: {str(e)}")
        return PageResponse[RequestLogResponse].fail(msg=str(e))

