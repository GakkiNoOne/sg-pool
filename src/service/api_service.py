"""API 请求服务 - 使用 OpenAI 和 Anthropic SDK"""

import httpx
from openai import OpenAI, AuthenticationError as OpenAIAuthError
from anthropic import Anthropic, AuthenticationError as AnthropicAuthError

from entity.context import RequestContext
from constants import PROVIDER_OPENAI, PROVIDER_ANTHROPIC
from utils.logger import logger
from service.databases import key_service


def send_request(context: RequestContext) -> bool:
    """
    发送 API 请求（使用官方 SDK）
    
    注意：
    - 使用官方 SDK，自动处理流式和非流式响应
    - 响应对象保存在 context.response 中
    - 流式响应返回 Stream 对象，非流式返回对应的 Completion 对象
    """
    try:
        if context.provider == PROVIDER_OPENAI:
            return _send_openai_request(context)
        elif context.provider == PROVIDER_ANTHROPIC:
            return _send_anthropic_request(context)
        else:
            logger.error(f"不支持的 provider: {context.provider}")
            context.error = f"Unsupported provider: {context.provider}"
            return False
            
    except Exception as e:
        logger.error(f"请求失败: provider={context.provider}, error={str(e)}")
        context.error = str(e)
        context.response = None
        return False


def _send_openai_request(context: RequestContext) -> bool:
    """发送 OpenAI 请求"""
    try:
        logger.info(f"发送请求: provider={context.provider}, model={context.request.model}, stream={context.is_stream}")
        
        # 构建 base_url（去掉 /chat/completions，SDK 会自动添加）
        base_url = context.url.replace('/chat/completions', '')
        logger.info(f"使用 base_url: {base_url}")
        
        # 创建 HTTP 客户端（支持代理，包括 socks5）
        http_client = None
        if context.proxy:
            logger.info(f"使用代理: {context.proxy}")
            # httpx 支持 http/https/socks5 代理
            # 格式: http://..., https://..., socks5://...
            http_client = httpx.Client(
                proxy=context.proxy,
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        
        # 初始化 OpenAI 客户端
        client = OpenAI(
            api_key=context.api_key,
            base_url=base_url,
            http_client=http_client,
            timeout=60.0,
            default_headers={
                'x-amp-feature': 'chat',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        
        # 构建请求参数
        request_params = {
            'model': context.request.model,
            'messages': [msg.dict() for msg in context.request.messages],
            'stream': context.is_stream,
        }
        
        # 添加可选参数
        if context.request.max_tokens is not None:
            request_params['max_tokens'] = context.request.max_tokens
        if context.request.temperature is not None:
            request_params['temperature'] = context.request.temperature
        if context.request.top_p is not None:
            request_params['top_p'] = context.request.top_p
        if context.request.n is not None:
            request_params['n'] = context.request.n
        if context.request.stop is not None:
            request_params['stop'] = context.request.stop
        if context.request.presence_penalty is not None:
            request_params['presence_penalty'] = context.request.presence_penalty
        if context.request.frequency_penalty is not None:
            request_params['frequency_penalty'] = context.request.frequency_penalty
        if context.request.logit_bias is not None:
            request_params['logit_bias'] = context.request.logit_bias
        if context.request.user is not None:
            request_params['user'] = context.request.user
        
        # 发送请求
        response = client.chat.completions.create(**request_params)
        
        # 保存响应到 context
        context.response = response
        
        logger.info(f"OpenAI 请求成功")
        
        return True
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"OpenAI 请求失败: {error_msg}")
        context.error = error_msg
        context.response = None
        
        # 检查是否是认证错误（通过错误消息判断）
        # 支持的错误消息模式：
        # - "Unauthorized"
        # - "401"
        # - "authentication"
        # - "invalid api key"
        is_auth_error = (
            "unauthorized" in error_msg.lower() or
            "401" in error_msg or
            "authentication" in error_msg.lower() or
            "invalid api key" in error_msg.lower() or
            "invalid_api_key" in error_msg.lower()
        )
        
        # 如果确认是认证错误，且 Key 是从池中选择的，自动禁用
        if is_auth_error and context.api_key_entity and context.api_key_entity.id:
            key_id = context.api_key_entity.id
            key_name = context.api_key_entity.name
            logger.warning(f"🚨 检测到认证错误，开始自动禁用 Key: id={key_id}, name={key_name}")
            
            # 禁用 Key（更新数据库 + 移除缓存）
            if context.db:
                key_service.disable_api_key(
                    context.db, 
                    key_id, 
                    reason=f"认证失败: {error_msg}",
                    error_code="UNAUTHORIZED"
                )
        
        return False


def _send_anthropic_request(context: RequestContext) -> bool:
    """发送 Anthropic 请求"""
    try:
        logger.info(f"发送请求: provider=anthropic, model={context.request.model}, stream={context.is_stream}")
        
        # 构建 base_url（去掉 /v1/messages，SDK 会自动添加 /v1/messages）
        base_url = context.url.replace('/v1/messages', '')
        logger.info(f"使用 base_url: {base_url}")
        
        # 创建 HTTP 客户端（支持代理）
        # Anthropic SDK 需要传递完整的 httpx.Client 实例
        if context.proxy:
            logger.info(f"使用代理: {context.proxy}")
            http_client = httpx.Client(
                proxy=context.proxy,
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        else:
            http_client = httpx.Client(
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        
        # 初始化 Anthropic 客户端
        from constants import ANTHROPIC_API_VERSION
        
        client = Anthropic(
            api_key=context.api_key,
            base_url=base_url,
            http_client=http_client,
            max_retries=0,  # 禁用重试
            default_headers={
                'x-amp-feature': 'chat',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'anthropic-version': ANTHROPIC_API_VERSION  # ✅ 添加 anthropic-version header
            }
        )
        
        # 构建请求参数
        # Anthropic 只支持 role 和 content 字段，需要过滤掉其他字段（如 name）
        anthropic_messages = []
        for msg in context.request.messages:
            message_dict = {'role': msg.role, 'content': msg.content}
            anthropic_messages.append(message_dict)
        
        request_params = {
            'model': context.request.model,
            'messages': anthropic_messages,
            'max_tokens': context.request.max_tokens or 4096,  # Anthropic 必填，默认 4096
            'stream': context.is_stream,
        }
        
        # 添加可选参数
        if context.request.temperature is not None:
            request_params['temperature'] = context.request.temperature
        if context.request.top_p is not None:
            request_params['top_p'] = context.request.top_p
        if context.request.stop is not None:
            request_params['stop_sequences'] = [context.request.stop] if isinstance(context.request.stop, str) else context.request.stop
        
        # 发送请求
        response = client.messages.create(**request_params)
        
        # 保存响应到 context
        context.response = response
        
        logger.info(f"Anthropic 请求成功")
        
        return True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Anthropic 请求失败: {error_msg}")
        context.error = error_msg
        context.response = None
        
        # 检查是否是认证错误（通过错误消息判断）
        # 支持的错误消息模式：
        # - "Unauthorized"
        # - "401"
        # - "authentication"
        # - "invalid api key"
        is_auth_error = (
            "unauthorized" in error_msg.lower() or
            "401" in error_msg or
            "authentication" in error_msg.lower() or
            "invalid api key" in error_msg.lower() or
            "invalid_api_key" in error_msg.lower()
        )
        
        # 如果确认是认证错误，且 Key 是从池中选择的，自动禁用
        if is_auth_error and context.api_key_entity and context.api_key_entity.id:
            key_id = context.api_key_entity.id
            key_name = context.api_key_entity.name
            logger.warning(f"🚨 检测到认证错误，开始自动禁用 Key: id={key_id}, name={key_name}")
            
            # 禁用 Key（更新数据库 + 移除缓存）
            if context.db:
                key_service.disable_api_key(
                    context.db, 
                    key_id, 
                    reason=f"认证失败: {error_msg}",
                    error_code="UNAUTHORIZED"
                )
        
        return False

