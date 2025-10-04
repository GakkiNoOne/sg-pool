"""请求上下文相关的工具函数"""

from decimal import Decimal
from typing import Dict, Any, Optional
from utils.logger import logger


def extract_error_type(error_message: str) -> str:
    """
    从错误消息中提取错误类型
    
    Args:
        error_message: 错误消息字符串
        
    Returns:
        错误类型字符串（ConnectionError, TimeoutError, AuthError 等）
    """
    if not error_message:
        return 'OtherError'
    
    error_msg = error_message.lower()
    
    if 'connection' in error_msg or 'connect' in error_msg:
        return 'ConnectionError'
    elif 'timeout' in error_msg:
        return 'TimeoutError'
    elif 'auth' in error_msg or 'unauthorized' in error_msg or '401' in error_msg:
        return 'AuthError'
    elif 'rate limit' in error_msg or '429' in error_msg:
        return 'RateLimitError'
    elif 'not found' in error_msg or '404' in error_msg:
        return 'NotFoundError'
    elif 'server error' in error_msg or '500' in error_msg or '502' in error_msg or '503' in error_msg:
        return 'ServerError'
    else:
        return 'OtherError'


def extract_credits(usage) -> Decimal:
    """
    从 usage 对象中提取 credits（OpenAI 和 Anthropic 都有这个字段）
    
    Args:
        usage: 响应的 usage 对象
        
    Returns:
        credits 值（Decimal 类型）
    """
    try:
        if not usage:
            return Decimal('0')
        
        if hasattr(usage, 'credits'):
            credits = usage.credits
            if credits is not None:
                return Decimal(str(credits))
        
        return Decimal('0')
        
    except Exception as e:
        logger.warning(f"提取 credits 失败: {str(e)}")
        return Decimal('0')


def extract_tokens(usage, provider: str) -> Dict[str, Any]:
    """
    从 usage 对象中提取 token 信息
    
    Args:
        usage: 响应的 usage 对象
        provider: 提供商（openai 或 anthropic）
        
    Returns:
        包含 token 信息的字典
    """
    tokens = {
        'input_tokens': 0,
        'output_tokens': 0,
        'prompt_tokens': 0,
        'completion_tokens': 0,
        'cache_creation_input_tokens': 0,  # 修正字段名
        'cache_read_input_tokens': 0,      # 修正字段名
    }
    
    if not usage:
        return tokens
    
    try:
        if provider == 'anthropic':
            # Anthropic 格式
            tokens['input_tokens'] = getattr(usage, 'input_tokens', 0) or 0
            tokens['output_tokens'] = getattr(usage, 'output_tokens', 0) or 0
            tokens['cache_creation_input_tokens'] = getattr(usage, 'cache_creation_input_tokens', 0) or 0
            tokens['cache_read_input_tokens'] = getattr(usage, 'cache_read_input_tokens', 0) or 0
        else:
            # OpenAI 格式
            tokens['prompt_tokens'] = getattr(usage, 'prompt_tokens', 0) or 0
            tokens['completion_tokens'] = getattr(usage, 'completion_tokens', 0) or 0
            # 也保存到通用字段
            tokens['input_tokens'] = tokens['prompt_tokens']
            tokens['output_tokens'] = tokens['completion_tokens']
        
        return tokens
        
    except Exception as e:
        logger.warning(f"提取 token 信息失败: {str(e)}")
        return tokens


def get_usage_from_context(context, is_stream: bool):
    """
    从 context 中获取 usage 对象（处理流式和非流式）
    
    Args:
        context: RequestContext 对象
        is_stream: 是否为流式响应
        
    Returns:
        usage 对象或 None
    """
    try:
        if is_stream:
            # 流式响应：从 stream_usage 中获取
            if hasattr(context, 'stream_usage') and context.stream_usage:
                return context.stream_usage
        else:
            # 非流式响应：从 response.usage 中获取
            if hasattr(context.response, 'usage') and context.response.usage:
                return context.response.usage
        
        return None
        
    except Exception as e:
        logger.warning(f"获取 usage 失败: {str(e)}")
        return None

