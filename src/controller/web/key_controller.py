"""Web API Key 管理控制器"""

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from entity.databases.database import get_db
from entity.req.key import (
    APIKeyCreateRequest,
    APIKeyUpdateRequest,
    APIKeyQueryRequest,
    APIKeyGetRequest,
    APIKeyDeleteRequest,
    APIKeyUpdateWithIdRequest,
    APIKeyBatchCreateRequest,
    APIKeyBatchCheckRequest,
    APIKeyBatchDeleteRequest
)
from entity.req.api import ChatCompletionRequest, ChatMessage
from entity.res.key import APIKeyResponse, BatchCreateResult, BatchCheckResult, KeyCheckResult
from entity.res.base import Response, PageResponse
from service.databases import key_service
from controller import api_controller
from utils.logger import logger
from utils.admin_auth import verify_admin_token

router = APIRouter(prefix="/api/keys", tags=["Key Management"], dependencies=[Depends(verify_admin_token)])


@router.post("/create", response_model=Response[APIKeyResponse], summary="创建 API Key")
async def create_key(
    request: APIKeyCreateRequest,
    db: Session = Depends(get_db)
):
    """创建新的 API Key"""
    try:
        api_key = key_service.create_api_key(db, request)
        logger.info(f"创建 API Key 成功: id={api_key.id}, name={api_key.name}")
        
        return Response[APIKeyResponse].ok(
            data=APIKeyResponse(**api_key.to_dict()),
            msg="创建成功"
        )
    except Exception as e:
        logger.error(f"创建 API Key 失败: {str(e)}")
        return Response[APIKeyResponse].fail(msg=str(e))


@router.post("/list", response_model=PageResponse[APIKeyResponse], summary="查询 API Key 列表")
async def list_keys(
    request: APIKeyQueryRequest = Body(...),
    db: Session = Depends(get_db)
):
    """查询 API Key 列表（支持分页和筛选）"""
    try:
        items, total = key_service.query_api_keys(
            db=db,
            page=request.page,
            page_size=request.page_size,
            name=request.name,
            enabled=request.enabled,
            create_date=request.create_date,
            min_balance=request.min_balance
        )
        
        return PageResponse[APIKeyResponse].ok(
            items=[APIKeyResponse(**item.to_dict()) for item in items],
            total=total,
            page=request.page,
            page_size=request.page_size
        )
    except Exception as e:
        logger.error(f"查询 API Key 列表失败: {str(e)}")
        return PageResponse[APIKeyResponse].fail(msg=str(e))


@router.post("/get", response_model=Response[APIKeyResponse], summary="获取 API Key 详情")
async def get_key(
    request: APIKeyGetRequest = Body(...),
    db: Session = Depends(get_db)
):
    """根据 ID 获取 API Key 详情"""
    try:
        api_key = key_service.get_api_key_by_id(db, request.key_id)
        
        if not api_key:
            return Response[APIKeyResponse].fail(msg="API Key 不存在", code=404)
        
        return Response[APIKeyResponse].ok(
            data=APIKeyResponse(**api_key.to_dict()),
            msg="获取成功"
        )
    except Exception as e:
        logger.error(f"获取 API Key 详情失败: {str(e)}")
        return Response[APIKeyResponse].fail(msg=str(e))


@router.post("/update", response_model=Response[APIKeyResponse], summary="更新 API Key")
async def update_key(
    request: APIKeyUpdateWithIdRequest = Body(...),
    db: Session = Depends(get_db)
):
    """更新 API Key"""
    try:
        # 构建更新请求 - 只传递前端提供的字段
        update_data = request.dict(exclude_unset=True, exclude={'key_id'})
        update_request = APIKeyUpdateRequest(**update_data)
        
        api_key = key_service.update_api_key(db, request.key_id, update_request)
        
        if not api_key:
            return Response[APIKeyResponse].fail(msg="API Key 不存在", code=404)
        
        logger.info(f"更新 API Key 成功: id={api_key.id}, name={api_key.name}")
        
        return Response[APIKeyResponse].ok(
            data=APIKeyResponse(**api_key.to_dict()),
            msg="更新成功"
        )
    except Exception as e:
        logger.error(f"更新 API Key 失败: {str(e)}")
        return Response[APIKeyResponse].fail(msg=str(e))


@router.post("/delete", response_model=Response[None], summary="删除 API Key")
async def delete_key(
    request: APIKeyDeleteRequest = Body(...),
    db: Session = Depends(get_db)
):
    """删除 API Key"""
    try:
        success = key_service.delete_api_key(db, request.key_id)
        
        if not success:
            return Response[None].fail(msg="API Key 不存在", code=404)
        
        logger.info(f"删除 API Key 成功: id={request.key_id}")
        
        return Response[None].ok(msg="删除成功")
    except Exception as e:
        logger.error(f"删除 API Key 失败: {str(e)}")
        return Response[None].fail(msg=str(e))


@router.post("/batchCreate", response_model=Response[BatchCreateResult], summary="批量创建 API Key")
async def batch_create_keys(
    request: APIKeyBatchCreateRequest = Body(...),
    db: Session = Depends(get_db)
):
    """批量创建 API Keys"""
    try:
        # 从配置中获取UA和proxy列表
        from service.databases import config_service
        import json
        from constants.config_key import CONFIG_KEY_UA_LIST, CONFIG_KEY_PROXY_LIST
        
        configs = config_service.get_all_system_configs(db)
        
        # 解析UA列表
        ua_list_str = configs.get(CONFIG_KEY_UA_LIST, "[]")
        try:
            ua_list = json.loads(ua_list_str)
            if not isinstance(ua_list, list) or len(ua_list) == 0:
                ua_list = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"]
        except:
            ua_list = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"]
        
        # 解析代理列表
        proxy_list_str = configs.get(CONFIG_KEY_PROXY_LIST, "[]")
        try:
            proxy_list = json.loads(proxy_list_str)
            if not isinstance(proxy_list, list):
                proxy_list = []
        except:
            proxy_list = []
        
        # 批量创建
        success_keys, success_count, fail_count = key_service.batch_create_api_keys(db, request, ua_list, proxy_list)
        
        total_count = len(request.api_keys)
        
        logger.info(f"批量创建 API Keys: 成功{success_count}个, 失败{fail_count}个, 总共{total_count}个")
        
        result = BatchCreateResult(
            success_count=success_count,
            fail_count=fail_count,
            total_count=total_count,
            success_keys=[APIKeyResponse(**key.to_dict()) for key in success_keys]
        )
        
        if fail_count > 0:
            msg = f"批量创建完成：成功 {success_count} 个，失败 {fail_count} 个"
        else:
            msg = f"批量创建成功：共创建 {success_count} 个密钥"
        
        return Response[BatchCreateResult].ok(data=result, msg=msg)
        
    except Exception as e:
        logger.error(f"批量创建 API Keys 失败: {str(e)}")
        return Response[BatchCreateResult].fail(msg=str(e))


@router.post("/batchCheck", response_model=Response[BatchCheckResult], summary="批量测活 API Key")
async def batch_check_keys(
    request: APIKeyBatchCheckRequest = Body(...),
    db: Session = Depends(get_db)
):
    """批量测活 API Keys"""
    try:
        total_count = len(request.key_ids)
        success_count = 0
        fail_count = 0
        results = []
        
        logger.info(f"开始批量测活: 总共 {total_count} 个密钥")
        
        for key_id in request.key_ids:
            # 获取密钥信息
            api_key = key_service.get_api_key_by_id(db, key_id)
            
            if not api_key:
                results.append(KeyCheckResult(
                    key_id=key_id,
                    key_name="未知",
                    success=False,
                    message="密钥不存在"
                ))
                fail_count += 1
                continue
            
            # 测活
            check_success, message = await _check_key_alive(api_key, db)
            
            results.append(KeyCheckResult(
                key_id=key_id,
                key_name=api_key.name,
                success=check_success,
                message=message
            ))
            
            if check_success:
                success_count += 1
                logger.info(f"密钥 {api_key.name} (ID: {key_id}) 测活成功")
            else:
                fail_count += 1
                # 测活失败，禁用该密钥，并根据错误信息设置 error_code
                error_code = "CHECK_FAILED"  # 默认错误代码
                
                # 根据错误消息判断错误类型
                message_lower = message.lower()
                if "unauthorized" in message_lower or "401" in message_lower or "authentication" in message_lower or "invalid api key" in message_lower:
                    error_code = "UNAUTHORIZED"
                elif "rate limit" in message_lower or "429" in message_lower:
                    error_code = "RATE_LIMIT"
                elif "insufficient" in message_lower or "quota" in message_lower or "balance" in message_lower:
                    error_code = "INSUFFICIENT_QUOTA"
                elif "timeout" in message_lower:
                    error_code = "TIMEOUT"
                
                # 使用 disable_api_key 函数禁用密钥并设置 error_code（批量操作不自动提交）
                key_service.disable_api_key(
                    db, 
                    key_id, 
                    reason=f"批量测活失败: {message}",
                    error_code=error_code,
                    auto_commit=False  # 批量操作时不自动提交
                )
                logger.warning(f"密钥 {api_key.name} (ID: {key_id}) 测活失败，已禁用 (error_code: {error_code}): {message}")
        
        # 批量操作结束后统一提交
        db.commit()
        logger.info(f"批量测活完成: 成功 {success_count} 个, 失败 {fail_count} 个")
        
        result = BatchCheckResult(
            success_count=success_count,
            fail_count=fail_count,
            total_count=total_count,
            results=results
        )
        
        return Response[BatchCheckResult].ok(
            data=result,
            msg=f"测活完成：成功 {success_count} 个，失败 {fail_count} 个"
        )
        
    except Exception as e:
        logger.error(f"批量测活失败: {str(e)}")
        return Response[BatchCheckResult].fail(msg=str(e))


async def _check_key_alive(api_key, db: Session) -> tuple[bool, str]:
    """
    测试单个密钥是否活跃（直接复用 api_controller.chat_completions）
    
    返回: (是否成功, 消息)
    """
    try:
        import json
        from fastapi.responses import JSONResponse
        
        # 构建测活请求（使用 gpt-4o-mini 模型和简单的提示词）
        request = ChatCompletionRequest(
            model="gpt-4o-mini",
            messages=[ChatMessage(role="user", content="请只返回 hi")],
            stream=False,
            max_tokens=10,
            api_key=api_key.api_key,
            proxy=api_key.proxy if api_key.proxy else None
        )
        
        # 直接调用 api_controller.chat_completions（复用完整的请求处理逻辑）
        response = await api_controller.chat_completions(request, db)
        
        # chat_completions 返回的是 JSONResponse 对象
        if isinstance(response, JSONResponse):
            # 获取响应体内容
            body = response.body
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            
            response_data = json.loads(body)
            
            # 检查是否成功（有 choices 字段）
            if 'choices' in response_data and len(response_data['choices']) > 0:
                content = response_data['choices'][0].get('message', {}).get('content', '')
                logger.info(f"密钥 {api_key.name} 测活成功: {content}")
                return True, f"测活成功，返回内容: {content}"
            
            # 检查是否有错误信息
            if 'error' in response_data:
                error_info = response_data['error']
                if isinstance(error_info, dict):
                    error_msg = error_info.get('message', str(error_info))
                else:
                    error_msg = str(error_info)
                logger.error(f"密钥 {api_key.name} 测活失败: {error_msg}")
                return False, error_msg
            
            # 其他未知错误
            error_msg = f"未知响应格式: {body[:200]}"  # 只取前200字符
            logger.error(f"密钥 {api_key.name} 测活失败: {error_msg}")
            return False, error_msg
        
        # 不应该到这里
        error_msg = f"意外的响应类型: {type(response)}"
        logger.error(f"密钥 {api_key.name} 测活失败: {error_msg}")
        return False, error_msg
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"密钥 {api_key.name} 测活异常: {error_msg}")
        return False, error_msg


@router.post("/batchDelete", response_model=Response[dict], summary="批量删除 API Key")
async def batch_delete_keys(
    request: APIKeyBatchDeleteRequest = Body(...),
    db: Session = Depends(get_db)
):
    """批量删除 API Keys"""
    try:
        total_count = len(request.key_ids)
        success_count = 0
        fail_count = 0
        
        logger.info(f"开始批量删除: 总共 {total_count} 个密钥")
        
        for key_id in request.key_ids:
            try:
                # 检查密钥是否存在
                api_key = key_service.get_api_key_by_id(db, key_id)
                if not api_key:
                    logger.warning(f"密钥不存在: ID={key_id}")
                    fail_count += 1
                    continue
                
                # 删除密钥
                key_service.delete_api_key(db, key_id)
                success_count += 1
                logger.info(f"密钥 {api_key.name} (ID: {key_id}) 删除成功")
                
            except Exception as e:
                logger.error(f"删除密钥 ID={key_id} 失败: {str(e)}")
                fail_count += 1
        
        logger.info(f"批量删除完成: 成功 {success_count} 个, 失败 {fail_count} 个")
        
        result = {
            'success_count': success_count,
            'fail_count': fail_count,
            'total_count': total_count
        }
        
        return Response[dict].ok(
            data=result,
            msg=f"删除完成：成功 {success_count} 个，失败 {fail_count} 个"
        )
        
    except Exception as e:
        logger.error(f"批量删除失败: {str(e)}")
        return Response[dict].fail(msg=str(e))
