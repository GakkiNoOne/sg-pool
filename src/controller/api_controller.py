"""API 控制器 - 对外接口"""

from typing import Optional, Tuple
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

from constants import PROVIDER_ANTHROPIC, get_provider_by_model
from entity.databases.database import get_db
from entity.req import ChatCompletionRequest
from entity.req.anthropic import AnthropicRequest
from entity.res import ChatCompletionResponse, ErrorResponse
from entity.context import RequestContext
from service import lb_service, api_service
from utils.logger import logger
from utils.auth import verify_api_secret
from utils.response_utils import (
    handle_openai_compatible_stream,
    handle_openai_compatible_response,
    handle_anthropic_native_stream,
    handle_anthropic_native_response,
    build_error_response
)

router = APIRouter(tags=["API"])


# ==================== 通用参数校验 ====================

def validate_request_params(model: str, messages: list = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    通用参数校验方法
    
    Args:
        model: 模型名称
        messages: 消息列表（可选）
    
    Returns:
        (is_valid, error_message, provider)
        - is_valid: 是否校验通过
        - error_message: 错误消息（校验通过时为 None）
        - provider: provider 类型（openai/anthropic）
    """
    from configs.global_config import global_config
    
    # 1. 校验 model 参数
    if not model or not isinstance(model, str) or model.strip() == "":
        return False, "Model parameter is required and must be a non-empty string", None
    
    # 2. 检测 provider
    provider = get_provider_by_model(model)
    if not provider:
        return False, f"Unsupported model: {model}. Model not recognized by any provider.", None
    
    # 3. 验证模型是否在配置的支持列表中
    if not global_config.is_model_supported(model, provider):
        supported_models = global_config.openai_models if provider == 'openai' else global_config.anthropic_models
        return False, (
            f"Model '{model}' is not in the configured model list for provider '{provider}'. "
            f"Please check your system configuration. Supported models count: {len(supported_models)}"
        ), None
    
    # 4. 校验 messages 参数（如果提供）
    if messages is not None:
        if not isinstance(messages, list) or len(messages) == 0:
            return False, "Messages parameter must be a non-empty array", provider
        
        # 校验每条消息的基本结构
        for idx, msg in enumerate(messages):
            if not hasattr(msg, 'role') or not hasattr(msg, 'content'):
                return False, f"Message at index {idx} is missing required fields (role, content)", provider
            
            if not msg.role or not isinstance(msg.role, str):
                return False, f"Message at index {idx} has invalid role", provider
            
            if msg.content is None or (isinstance(msg.content, str) and msg.content.strip() == ""):
                return False, f"Message at index {idx} has empty content", provider
    
    return True, None, provider


# ==================== 路由处理 ====================

@router.post(
    "/v1/chat/completions",
    response_model=ChatCompletionResponse,
    summary="OpenAI Chat Completions",
    description="OpenAI 格式的对话接口，支持流式和非流式响应"
)
async def chat_completions(
    request: ChatCompletionRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_secret)
):
    """
    OpenAI Chat Completions API 兼容接口
    - 支持流式（stream=true）和非流式响应
    - 自动选择可用的 API Key
    - 记录请求日志和统计信息
    """
    
    # 1. 参数校验
    is_valid, error_message, provider = validate_request_params(
        model=request.model,
        messages=request.messages
    )
    
    if not is_valid:
        logger.warning(f"参数校验失败: {error_message}")
        return build_error_response(
            status_code=400,
            error_type="invalid_request_error",
            message=error_message,
            code="invalid_params"
        )
    
    # 2. 创建请求上下文并初始化
    context = RequestContext(request, db)
    context.init()
    
    logger.info(f"收到请求: model={request.model}, stream={context.is_stream}, provider={context.provider}, proxy={context.proxy}")
    
    # 3. 获取可用的 key
    api_key_string = lb_service.get_key(context)
    
    if not api_key_string:
        return build_error_response(
            status_code=503,
            error_type="service_unavailable",
            message="No available API key",
            code="no_available_key"
        )

    # 4. 发送请求（使用官方 SDK）
    success = api_service.send_request(context)
    
    # 检查请求是否成功
    if not success:
        return build_error_response(
            status_code=502,
            error_type="upstream_error",
            message=f"Upstream API request failed: {context.error}",
            code="upstream_request_failed"
        )

    # 5. 返回响应
    if context.is_stream:
        return handle_openai_compatible_stream(context)
    else:
        return handle_openai_compatible_response(context)


# ==================== Anthropic Native API ====================

@router.post("/v1/messages", summary="Anthropic Messages API (原生格式)")
async def anthropic_messages(
    request: AnthropicRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_secret)
):
    """
    Anthropic Messages API - 完全兼容 Anthropic 原生格式
    
    参考文档: https://docs.claude.com/en/api/messages
    
    特点：
    - 使用 Anthropic 原生请求/响应格式
    - 不做任何格式转换
    - 完全兼容 Anthropic SDK
    - 支持流式和非流式响应
    """
    # 1. 参数校验
    is_valid, error_message, provider = validate_request_params(
        model=request.model,
        messages=request.messages
    )
    
    if not is_valid:
        logger.warning(f"参数校验失败: {error_message}")
        return build_error_response(
            status_code=400,
            error_type="invalid_request_error",
            message=error_message,
            format="anthropic"
        )
    
    # 2. 创建请求上下文
    # 将 AnthropicRequest 转换为内部使用的 ChatCompletionRequest
    from entity.req.api import ChatMessage
    
    # 转换 messages
    chat_messages = []
    for msg in request.messages:
        # Anthropic 的 content 可能是 string 或 array，统一转为 string
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        chat_messages.append(ChatMessage(role=msg.role, content=content))
    
    # 构建内部请求对象
    internal_request = ChatCompletionRequest(
        model=request.model,
        messages=chat_messages,
        max_tokens=request.max_tokens,
        api_key=request.api_key,
        proxy=request.proxy,
        temperature=request.temperature,
        top_p=request.top_p,
        stream=request.stream,
        stop=request.stop_sequences[0] if request.stop_sequences else None
    )
    
    context = RequestContext(internal_request, db)
    context.init()
    
    # 强制设置为 Anthropic provider
    context.provider = PROVIDER_ANTHROPIC
    from constants import ANTHROPIC_API_URL
    context.url = ANTHROPIC_API_URL
    
    logger.info(f"收到 Anthropic 原生请求: model={request.model}, stream={context.is_stream}")
    
    # 3. 获取可用的 key
    api_key_string = lb_service.get_key(context)
    
    if not api_key_string:
        return build_error_response(
            status_code=503,
            error_type="api_error",
            message="No available API key",
            format="anthropic"
        )
    
    # 4. 发送请求（使用 Anthropic SDK）
    success = api_service.send_request(context)
    
    # 检查请求是否成功
    if not success:
        return build_error_response(
            status_code=502,
            error_type="api_error",
            message=f"Upstream API request failed: {context.error}",
            format="anthropic"
        )
    
    # 5. 返回响应（Anthropic 原生格式）
    if context.is_stream:
        return handle_anthropic_native_stream(context)
    else:
        return handle_anthropic_native_response(context)


# ==================== 模型列表查询 ====================

@router.get("/v1/models", summary="获取所有支持的模型列表")
async def list_models(
    request: Request,
    _: bool = Depends(verify_api_secret)
):
    """
    获取所有支持的模型列表（OpenAI 和 Anthropic 模型并集）
    
    根据请求头自动判断返回格式：
    - 如果请求头包含 anthropic-version 或 User-Agent 包含 anthropic，返回 Anthropic 格式
    - 否则返回 OpenAI 格式
    
    OpenAI 格式：
    {
        "object": "list",
        "data": [
            {
                "id": "gpt-4o-mini",
                "object": "model",
                "created": 1686935002,
                "owned_by": "openai"
            }
        ]
    }
    
    Anthropic 格式：
    {
        "data": [
            {
                "created_at": "2025-02-19T00:00:00Z",
                "display_name": "Claude Sonnet 4",
                "id": "claude-sonnet-4-20250514",
                "type": "model"
            }
        ],
        "first_id": "claude-3-5-sonnet-20241022",
        "has_more": false,
        "last_id": "claude-sonnet-4"
    }
    """
    from configs.global_config import global_config
    from datetime import datetime
    
    # 获取所有支持的模型
    openai_models = global_config.openai_models
    anthropic_models = global_config.anthropic_models
    
    # 判断请求格式：检查请求头
    is_anthropic_request = False
    anthropic_version = request.headers.get("anthropic-version", "")
    user_agent = request.headers.get("user-agent", "").lower()
    
    if anthropic_version or "anthropic" in user_agent or "claude" in user_agent:
        is_anthropic_request = True
    
    # 根据请求类型返回不同格式
    if is_anthropic_request:
        # Anthropic 格式
        models_data = []
        
        # 模型名称映射到显示名称
        model_display_names = {
            "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet",
            "claude-3-5-sonnet-20240620": "Claude 3.5 Sonnet",
            "claude-3-opus-20240229": "Claude 3 Opus",
            "claude-3-sonnet-20240229": "Claude 3 Sonnet",
            "claude-3-haiku-20240307": "Claude 3 Haiku",
            "claude-sonnet-4-20250514": "Claude Sonnet 4",
            "claude-3-opus": "Claude 3 Opus",
            "claude-3-sonnet": "Claude 3 Sonnet",
            "claude-3-haiku": "Claude 3 Haiku",
            "claude-3.5-sonnet": "Claude 3.5 Sonnet",
            "claude-sonnet-4": "Claude Sonnet 4",
        }
        
        # 只返回 Anthropic 模型
        for model in sorted(anthropic_models):
            display_name = model_display_names.get(model, model)
            models_data.append({
                "created_at": "2025-02-19T00:00:00Z",
                "display_name": display_name,
                "id": model,
                "type": "model"
            })
        
        # 构建响应
        response = {
            "data": models_data,
            "has_more": False
        }
        
        # 如果有模型数据，添加 first_id 和 last_id
        if models_data:
            response["first_id"] = models_data[0]["id"]
            response["last_id"] = models_data[-1]["id"]
        
        return response
    else:
        # OpenAI 格式
        models_data = []
        
        # 创建时间戳（统一使用当前时间）
        created_timestamp = int(datetime.now().timestamp())
        
        # 添加 OpenAI 模型
        for model in sorted(openai_models):
            models_data.append({
                "id": model,
                "object": "model",
                "created": created_timestamp,
                "owned_by": "openai"
            })
        
        # 添加 Anthropic 模型
        for model in sorted(anthropic_models):
            models_data.append({
                "id": model,
                "object": "model",
                "created": created_timestamp,
                "owned_by": "anthropic"
            })
        
        return {
            "object": "list",
            "data": models_data
        }

