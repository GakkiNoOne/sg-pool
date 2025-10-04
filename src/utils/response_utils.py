"""响应处理工具"""

import json

from fastapi.responses import StreamingResponse, JSONResponse

from constants import PROVIDER_ANTHROPIC
from service import log_service
from utils.convert_utils import convert_anthropic_response, convert_anthropic_stream_chunk
from utils.logger import logger


def handle_openai_compatible_stream(context) -> StreamingResponse:
    """
    处理 OpenAI 兼容格式的流式响应
    
    支持：
    - OpenAI 原生格式
    - Anthropic 转换为 OpenAI 格式
    """
    def generate():
        last_chunk = None
        # Anthropic: 保存第一个 chunk 的 id 和 model
        saved_id = None
        saved_model = None
        # Anthropic: 累积 usage 信息（分散在多个事件中）
        input_tokens = 0
        output_tokens = 0
        cache_creation_tokens = 0
        cache_read_tokens = 0
        credits = 0  # 累积 credits
        # 累积响应内容
        accumulated_content = []
        
        try:
            for chunk in context.response:
                last_chunk = chunk
                
                if context.provider == PROVIDER_ANTHROPIC:
                    chunk_type = chunk.type if hasattr(chunk, 'type') else None
                    
                    # 1. message_start: 包含 usage (input_tokens)
                    if chunk_type == "message_start" and hasattr(chunk, 'message'):
                        if hasattr(chunk.message, 'id'):
                            saved_id = chunk.message.id
                        if hasattr(chunk.message, 'model'):
                            saved_model = chunk.message.model
                            # 保存模型信息到 context，用于日志记录
                            context.stream_model = chunk.message.model
                        # message_start 可能包含初始 usage
                        if hasattr(chunk.message, 'usage') and chunk.message.usage:
                            usage = chunk.message.usage
                            if hasattr(usage, 'input_tokens') and usage.input_tokens:
                                input_tokens = usage.input_tokens
                            if hasattr(usage, 'cache_creation_input_tokens') and usage.cache_creation_input_tokens:
                                cache_creation_tokens = usage.cache_creation_input_tokens
                            if hasattr(usage, 'cache_read_input_tokens') and usage.cache_read_input_tokens:
                                cache_read_tokens = usage.cache_read_input_tokens
                    
                    # 2. message_delta: 包含增量 usage (output_tokens, credits)
                    elif chunk_type == "message_delta" and hasattr(chunk, 'usage') and chunk.usage:
                        usage = chunk.usage
                        if hasattr(usage, 'output_tokens') and usage.output_tokens:
                            output_tokens = usage.output_tokens
                        if hasattr(usage, 'credits') and usage.credits is not None:
                            credits = usage.credits
                    
                    # Anthropic: 转换为 OpenAI 格式
                    chunk_data = convert_anthropic_stream_chunk(chunk, saved_id, saved_model)
                    yield f"data: {chunk_data}\n\n"
                    
                    # 累积内容（从 content_block_delta 事件）
                    if chunk_type == "content_block_delta" and hasattr(chunk, 'delta'):
                        if hasattr(chunk.delta, 'text'):
                            accumulated_content.append(chunk.delta.text)
                else:
                    # OpenAI: 直接使用 SDK 格式
                    chunk_json = chunk.model_dump_json()
                    yield f"data: {chunk_json}\n\n"
                    
                    # OpenAI: 保存模型信息到 context（从第一个 chunk）
                    if hasattr(chunk, 'model') and chunk.model and not hasattr(context, 'stream_model'):
                        context.stream_model = chunk.model
                    
                    # 累积内容（从 choices[0].delta.content）
                    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            accumulated_content.append(delta.content)
            
            # 发送结束标记
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"流式响应错误: {str(e)}")
            error_msg = f"data: {{'error': 'Stream error: {str(e)}'}}\n\n"
            yield error_msg
            context.error = str(e)
        finally:
            # 保存 usage 信息（安全处理）
            try:
                # Anthropic: 构建累积的 usage 对象
                if context.provider == PROVIDER_ANTHROPIC and (input_tokens > 0 or output_tokens > 0):
                    # 创建一个简单的对象来存储累积的 usage
                    class CumulativeUsage:
                        def __init__(self, input_tokens, output_tokens, cache_creation, cache_read, credits):
                            self.input_tokens = input_tokens
                            self.output_tokens = output_tokens
                            self.cache_creation_input_tokens = cache_creation
                            self.cache_read_input_tokens = cache_read
                            self.credits = credits  # 添加 credits 字段
                        
                        def __repr__(self):
                            return f"CumulativeUsage(input={self.input_tokens}, output={self.output_tokens}, cache_creation={self.cache_creation_input_tokens}, cache_read={self.cache_read_input_tokens}, credits={self.credits})"
                    
                    context.stream_usage = CumulativeUsage(input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens, credits)
                    logger.debug(f"流式响应 token 统计: input={input_tokens}, output={output_tokens}, cache_creation={cache_creation_tokens}, cache_read={cache_read_tokens}, credits={credits}")
                # OpenAI: 从 last_chunk 获取 usage
                elif last_chunk and hasattr(last_chunk, 'usage') and last_chunk.usage:
                    context.stream_usage = last_chunk.usage
                    logger.debug(f"流式响应 token 统计: {last_chunk.usage}")
                else:
                    logger.warning(f"流式响应未能获取 token 统计 (provider={context.provider})")
            except Exception as e:
                logger.warning(f"保存流式 usage 信息失败: {str(e)}")
            
            # 保存累积的响应内容
            try:
                if accumulated_content:
                    context.stream_content = ''.join(accumulated_content)
            except Exception as e:
                logger.warning(f"保存流式响应内容失败: {str(e)}")
            
            # 记录日志（安全处理，不抛出异常）
            try:
                log_service.log(context)
            except Exception as e:
                logger.error(f"记录流式请求日志失败: {str(e)}")
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


def handle_openai_compatible_response(context) -> JSONResponse:
    """
    处理 OpenAI 兼容格式的非流式响应
    
    支持：
    - OpenAI 原生格式
    - Anthropic 转换为 OpenAI 格式
    """
    try:
        # 转换响应格式
        if context.provider == PROVIDER_ANTHROPIC:
            response_data = convert_anthropic_response(context.response)
        else:
            response_data = context.response.model_dump()
        
        # 记录日志（安全处理）
        try:
            log_service.log(context)
        except Exception as log_err:
            logger.error(f"记录非流式请求日志失败: {str(log_err)}")
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"解析响应失败: {str(e)}")
        # 即使解析失败，也尝试记录日志
        try:
            context.error = str(e)
            log_service.log(context)
        except:
            pass
        
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "message": f"Failed to parse response: {str(e)}",
                    "type": "parse_error",
                    "code": "response_parse_failed"
                }
            }
        )


def handle_anthropic_native_stream(context) -> StreamingResponse:
    """
    处理 Anthropic 原生格式的流式响应
    
    直接返回 Anthropic SDK 的原生格式，不做转换
    """
    def generate():
        last_chunk = None
        # Anthropic: 累积 usage 信息（分散在多个事件中）
        input_tokens = 0
        output_tokens = 0
        cache_creation_tokens = 0
        cache_read_tokens = 0
        credits = 0  # 累积 credits
        # 累积响应内容
        accumulated_content = []
        
        try:
            for chunk in context.response:
                last_chunk = chunk
                # Anthropic: 直接使用原生格式
                chunk_json = chunk.model_dump_json()
                
                chunk_type = chunk.type if hasattr(chunk, 'type') else None
                
                # 1. message_start: 包含 usage (input_tokens)
                if chunk_type == "message_start" and hasattr(chunk, 'message'):
                    # 保存模型信息到 context
                    if hasattr(chunk.message, 'model') and chunk.message.model:
                        context.stream_model = chunk.message.model
                    
                    if hasattr(chunk.message, 'usage') and chunk.message.usage:
                        usage = chunk.message.usage
                        if hasattr(usage, 'input_tokens') and usage.input_tokens:
                            input_tokens = usage.input_tokens
                        if hasattr(usage, 'cache_creation_input_tokens') and usage.cache_creation_input_tokens:
                            cache_creation_tokens = usage.cache_creation_input_tokens
                        if hasattr(usage, 'cache_read_input_tokens') and usage.cache_read_input_tokens:
                            cache_read_tokens = usage.cache_read_input_tokens
                
                # 2. message_delta: 包含增量 usage (output_tokens, credits)
                elif chunk_type == "message_delta" and hasattr(chunk, 'usage') and chunk.usage:
                    usage = chunk.usage
                    if hasattr(usage, 'output_tokens') and usage.output_tokens:
                        output_tokens = usage.output_tokens
                    if hasattr(usage, 'credits') and usage.credits is not None:
                        credits = usage.credits
                
                # Anthropic 流式格式: event: type\ndata: {...}\n\n
                event_type = chunk.type if hasattr(chunk, 'type') else "unknown"
                yield f"event: {event_type}\n"
                yield f"data: {chunk_json}\n\n"
                
                # 累积内容（从 content_block_delta 事件）
                if chunk_type == "content_block_delta" and hasattr(chunk, 'delta'):
                    if hasattr(chunk.delta, 'text'):
                        accumulated_content.append(chunk.delta.text)
            
        except Exception as e:
            logger.error(f"Anthropic 流式响应错误: {str(e)}")
            error_data = {
                "type": "error",
                "error": {
                    "type": "api_error",
                    "message": str(e)
                }
            }
            yield f"event: error\n"
            yield f"data: {json.dumps(error_data)}\n\n"
            context.error = str(e)
        finally:
            # 保存 usage 信息（安全处理）
            try:
                # Anthropic: 构建累积的 usage 对象
                if input_tokens > 0 or output_tokens > 0:
                    # 创建一个简单的对象来存储累积的 usage
                    class CumulativeUsage:
                        def __init__(self, input_tokens, output_tokens, cache_creation, cache_read, credits):
                            self.input_tokens = input_tokens
                            self.output_tokens = output_tokens
                            self.cache_creation_input_tokens = cache_creation
                            self.cache_read_input_tokens = cache_read
                            self.credits = credits  # 添加 credits 字段
                        
                        def __repr__(self):
                            return f"CumulativeUsage(input={self.input_tokens}, output={self.output_tokens}, cache_creation={self.cache_creation_input_tokens}, cache_read={self.cache_read_input_tokens}, credits={self.credits})"
                    
                    context.stream_usage = CumulativeUsage(input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens, credits)
                    logger.debug(f"Anthropic 流式响应 token 统计: input={input_tokens}, output={output_tokens}, cache_creation={cache_creation_tokens}, cache_read={cache_read_tokens}, credits={credits}")
                else:
                    logger.warning(f"Anthropic 流式响应未能获取 token 统计")
            except Exception as e:
                logger.warning(f"保存 Anthropic 流式 usage 信息失败: {str(e)}")
            
            # 保存累积的响应内容
            try:
                if accumulated_content:
                    context.stream_content = ''.join(accumulated_content)
            except Exception as e:
                logger.warning(f"保存 Anthropic 流式响应内容失败: {str(e)}")
            
            # 记录日志（安全处理，不抛出异常）
            try:
                log_service.log(context)
            except Exception as e:
                logger.error(f"记录 Anthropic 流式请求日志失败: {str(e)}")
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


def handle_anthropic_native_response(context) -> JSONResponse:
    """
    处理 Anthropic 原生格式的非流式响应
    
    直接返回 Anthropic SDK 的原生格式，不做转换
    """
    try:
        # Anthropic: 直接返回原生格式
        response_data = context.response.model_dump()
        
        # 记录日志（安全处理）
        try:
            log_service.log(context)
        except Exception as log_err:
            logger.error(f"记录 Anthropic 非流式请求日志失败: {str(log_err)}")
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"解析 Anthropic 响应失败: {str(e)}")
        # 即使解析失败，也尝试记录日志
        try:
            context.error = str(e)
            log_service.log(context)
        except:
            pass
        
        return JSONResponse(
            status_code=502,
            content={
                "type": "error",
                "error": {
                    "type": "api_error",
                    "message": f"Failed to parse response: {str(e)}"
                }
            }
        )


def build_error_response(status_code: int, error_type: str, message: str, code: str = None, format: str = "openai") -> JSONResponse:
    """
    构建错误响应
    
    Args:
        status_code: HTTP 状态码
        error_type: 错误类型
        message: 错误消息
        code: 错误代码（可选）
        format: 响应格式 ("openai" 或 "anthropic")
    """
    if format == "anthropic":
        # Anthropic 错误格式
        content = {
            "type": "error",
            "error": {
                "type": error_type,
                "message": message
            }
        }
    else:
        # OpenAI 错误格式
        content = {
            "error": {
                "message": message,
                "type": error_type,
            }
        }
        if code:
            content["error"]["code"] = code
    
    return JSONResponse(status_code=status_code, content=content)

