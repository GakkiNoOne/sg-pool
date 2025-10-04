"""RequestLog 业务服务"""

import time
import json
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy.orm import Session
from entity.databases.request_log import RequestLog
from entity.context import RequestContext
from mapper import request_log_mapper
from utils.logger import logger
from constants.config_key import CONFIG_LOG_CONVERSATION_CONTENT, DEFAULT_LOG_CONVERSATION_CONTENT
from service.databases import config_service


def build_log_data_from_context(context: RequestContext) -> Dict[str, Any]:
    """
    从请求上下文构建日志数据
    
    Args:
        context: 请求上下文
        
    Returns:
        日志数据字典
    """
    try:
        # 计算延迟
        latency_ms = int((time.time() - context.start_time) * 1000) if hasattr(context, 'start_time') else 0
        
        # 构建日志数据
        log_data = {
            'model': context.request.model if hasattr(context.request, 'model') else 'unknown',
            'res_model': None,  # 稍后从响应中提取
            'provider': context.provider if hasattr(context, 'provider') else 'unknown',
            'latency_ms': latency_ms,
            'proxy': context.proxy if hasattr(context, 'proxy') else None,
            # 初始化所有 token 字段为 0
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'cache_creation_input_tokens': 0,
            'cache_read_input_tokens': 0,
            # 成本字段（使用 Decimal 类型）
            'cost': Decimal('0'),  # 默认为0，稍后从 usage.credits 中提取
            # 请求和响应内容
            'request_body': None,
            'response_body': None,
        }
        
        # 检查是否记录对话内容
        # 使用全局配置（避免频繁查询数据库）
        from configs.global_config import global_config
        should_log_content = global_config.should_log_conversation_content
        
        # 保存请求 body（如果配置允许）
        if should_log_content:
            try:
                if hasattr(context.request, 'model_dump'):
                    log_data['request_body'] = json.dumps(context.request.model_dump(), ensure_ascii=False)
                elif hasattr(context.request, 'dict'):
                    log_data['request_body'] = json.dumps(context.request.dict(), ensure_ascii=False)
            except Exception as e:
                logger.warning(f"序列化请求 body 失败: {str(e)}")
        
        # 根据 key 来源设置不同字段
        if context.api_key_from_pool:
            # 从池中选择的 key：记录 key_id 和 api_key
            log_data['key_id'] = context.api_key_entity.id if context.api_key_entity else 0
            log_data['api_key'] = context.api_key if hasattr(context, 'api_key') else None
        else:
            # 参数指定的 key：只记录 api_key，key_id 设置为 0
            log_data['key_id'] = 0
            log_data['api_key'] = context.api_key if hasattr(context, 'api_key') else None
    except Exception as e:
        logger.error(f"构建基础日志数据失败: {str(e)}")
        # 返回最小日志数据
        return {
            'key_id': 0,
            'api_key': None,
            'proxy': None,
            'model': 'error',
            'provider': 'unknown',
            'latency_ms': 0,
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'cache_creation_input_tokens': 0,
            'cache_read_input_tokens': 0,
            'cost': Decimal('0'),
            'status': 'error',
            'error_message': f'Log build error: {str(e)}',
            'http_status_code': 0,
        }
    
    # 判断请求状态
    if context.error:
        # 失败
        log_data['status'] = 'error'
        log_data['error_message'] = context.error
        log_data['http_status_code'] = 0
        
        # 从错误消息中提取错误类型（使用工具函数）
        from utils.context_utils import extract_error_type
        log_data['error_type'] = extract_error_type(context.error)
    elif context.response:
        # 成功
        log_data['status'] = 'success'
        log_data['http_status_code'] = 200
        
        # 提取响应中的实际模型名称
        try:
            if hasattr(context.response, 'model') and context.response.model:
                log_data['res_model'] = context.response.model
            # 流式响应的情况，从 stream_usage 中获取（如果有保存）
            elif context.is_stream and hasattr(context, 'stream_model') and context.stream_model:
                log_data['res_model'] = context.stream_model
        except Exception as e:
            logger.warning(f"提取响应模型名称失败: {str(e)}")
        
        # 保存响应 body（如果配置允许）
        if should_log_content:
            # 非流式响应
            if not context.is_stream:
                try:
                    if hasattr(context.response, 'model_dump'):
                        log_data['response_body'] = json.dumps(context.response.model_dump(), ensure_ascii=False)
                    elif hasattr(context.response, 'dict'):
                        log_data['response_body'] = json.dumps(context.response.dict(), ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"序列化响应 body 失败: {str(e)}")
            else:
                # 流式响应：保存累积的响应信息
                try:
                    if hasattr(context, 'stream_content') and context.stream_content:
                        stream_response = {
                            'content': context.stream_content,
                            'model': context.stream_model if hasattr(context, 'stream_model') else None,
                        }
                        log_data['response_body'] = json.dumps(stream_response, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"序列化流式响应 body 失败: {str(e)}")
        
        # 解析 token 使用量（使用工具函数简化）
        try:
            from utils.context_utils import get_usage_from_context, extract_tokens, extract_credits
            
            # 获取 usage 对象
            usage = get_usage_from_context(context, context.is_stream)
            
            if usage:
                # 提取 token 信息
                tokens = extract_tokens(usage, context.provider)
                log_data.update(tokens)
                
                # 如果没有 total_tokens，计算总和
                if log_data['total_tokens'] == 0:
                    log_data['total_tokens'] = (
                        (log_data['prompt_tokens'] or 0) + 
                        (log_data['completion_tokens'] or 0) +
                        (log_data['input_tokens'] or 0) + 
                        (log_data['output_tokens'] or 0)
                    )
                
                # 提取 credits 作为 cost
                log_data['cost'] = extract_credits(usage)
                logger.debug(f"✅ 成功提取 usage: cost={log_data['cost']}, tokens={log_data['total_tokens']}")
                
        except Exception as e:
            logger.error(f"❌ 解析响应 token 使用量失败: {str(e)}")
    else:
        # 未知状态
        log_data['status'] = 'unknown'
    
    return log_data


def create_log_from_data(db: Session, log_data: Dict[str, Any]) -> RequestLog:
    """
    从日志数据创建日志记录
    
    Args:
        db: 数据库会话
        log_data: 日志数据字典
        
    Returns:
        RequestLog 对象
    """
    try:
        # 插入日志
        log = request_log_mapper.insert_request_log(db, log_data)
        logger.debug(f"日志记录成功: log_id={log.id}, status={log.status}, cost={log.cost}, latency={log.latency_ms}ms")
        return log
    except Exception as e:
        logger.error(f"日志记录失败: {str(e)}")
        raise


def get_logs_by_key(db: Session, key_id: int, limit: int = 100) -> list[RequestLog]:
    """获取指定 Key 的日志"""
    return request_log_mapper.query_logs_by_key(db, key_id, limit)


def get_recent_logs(db: Session, limit: int = 100) -> list[RequestLog]:
    """获取最近的日志"""
    return request_log_mapper.query_recent_logs(db, limit)


def query_request_logs(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    key_id: int = None,
    api_key: str = None,
    status: str = None,
    provider: str = None,
    model: str = None,
    start_time: str = None,
    end_time: str = None
) -> tuple[list[RequestLog], int]:
    """
    查询请求日志列表（支持分页和筛选）
    
    Args:
        db: 数据库会话
        page: 页码
        page_size: 每页数量
        key_id: Key ID 筛选
        api_key: API Key 筛选（模糊搜索）
        status: 状态筛选
        provider: 提供商筛选
        model: 模型名称模糊搜索
        start_time: 开始时间（格式: YYYY-MM-DD HH:mm:ss）
        end_time: 结束时间（格式: YYYY-MM-DD HH:mm:ss）
        
    Returns:
        (日志列表, 总数量)
    """
    from sqlalchemy import func
    from datetime import datetime
    
    # 构建基础查询
    query = db.query(RequestLog)
    
    # 添加筛选条件
    if key_id is not None:
        query = query.filter(RequestLog.key_id == key_id)
    
    if api_key:
        query = query.filter(RequestLog.api_key.like(f"%{api_key}%"))
    
    if status:
        query = query.filter(RequestLog.status == status)
    
    if provider:
        query = query.filter(RequestLog.provider == provider)
    
    if model:
        query = query.filter(RequestLog.model.like(f"%{model}%"))
    
    # 添加时间范围筛选
    if start_time:
        try:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            query = query.filter(RequestLog.create_time >= start_dt)
        except ValueError:
            logger.warning(f"无效的开始时间格式: {start_time}")
    
    if end_time:
        try:
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            query = query.filter(RequestLog.create_time <= end_dt)
        except ValueError:
            logger.warning(f"无效的结束时间格式: {end_time}")
    
    # 获取总数量
    total = query.count()
    
    # 分页查询
    offset = (page - 1) * page_size
    items = query.order_by(RequestLog.create_time.desc()).offset(offset).limit(page_size).all()
    
    return items, total

