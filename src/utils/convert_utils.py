"""响应格式转换工具"""

import time
import json


def convert_anthropic_response(response) -> dict:
    """
    将 Anthropic 响应转换为 OpenAI 兼容格式
    
    Anthropic Message format:
    {
        "id": "msg_xxx",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Hello!"}],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 20}
    }
    
    Convert to OpenAI ChatCompletion format:
    {
        "id": "msg_xxx",
        "object": "chat.completion",
        "created": timestamp,
        "model": "claude-3-5-sonnet-20241022",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "Hello!"},
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    }
    """
    # 提取 content 文本
    content_text = ""
    if hasattr(response, 'content') and response.content:
        for block in response.content:
            if hasattr(block, 'text'):
                content_text += block.text
    
    # 转换 stop_reason
    stop_reason_map = {
        "end_turn": "stop",
        "max_tokens": "length",
        "stop_sequence": "stop",
    }
    finish_reason = stop_reason_map.get(response.stop_reason, "stop") if hasattr(response, 'stop_reason') else "stop"
    
    # 构建 OpenAI 格式
    openai_format = {
        "id": response.id if hasattr(response, 'id') else "unknown",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": response.model if hasattr(response, 'model') else "unknown",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content_text,
                },
                "finish_reason": finish_reason
            }
        ],
    }
    
    # 添加 usage 信息
    if hasattr(response, 'usage') and response.usage:
        input_tokens = (response.usage.input_tokens or 0) if hasattr(response.usage, 'input_tokens') else 0
        output_tokens = (response.usage.output_tokens or 0) if hasattr(response.usage, 'output_tokens') else 0
        openai_format["usage"] = {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }
    
    return openai_format


def convert_anthropic_stream_chunk(chunk, saved_id=None, saved_model=None) -> str:
    """
    将 Anthropic 流式响应 chunk 转换为 OpenAI 兼容格式
    
    Anthropic stream events:
    - message_start: {"type": "message_start", "message": {...}}
    - content_block_start: {"type": "content_block_start", "index": 0, "content_block": {...}}
    - content_block_delta: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello"}}
    - content_block_stop: {"type": "content_block_stop", "index": 0}
    - message_delta: {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {...}}
    - message_stop: {"type": "message_stop"}
    
    Convert to OpenAI stream format:
    {
        "id": "chatcmpl-xxx",
        "object": "chat.completion.chunk",
        "created": timestamp,
        "model": "claude-xxx",
        "choices": [{
            "index": 0,
            "delta": {"role": "assistant", "content": "Hello"},
            "finish_reason": null
        }]
    }
    """
    chunk_type = chunk.type if hasattr(chunk, 'type') else "unknown"
    
    # 从 chunk 中提取 id 和 model
    chunk_id = saved_id or "unknown"
    chunk_model = saved_model or "unknown"
    
    if chunk_type == "message_start" and hasattr(chunk, 'message'):
        # message_start 事件包含完整的 message 对象
        message = chunk.message
        if hasattr(message, 'id'):
            chunk_id = message.id
        if hasattr(message, 'model'):
            chunk_model = message.model
    
    # 基础格式
    openai_chunk = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": chunk_model,
        "choices": []
    }
    
    # 根据不同类型转换
    if chunk_type == "message_start":
        # 消息开始：返回 role
        openai_chunk["choices"] = [{
            "index": 0,
            "delta": {"role": "assistant"},
            "finish_reason": None
        }]
    
    elif chunk_type == "content_block_delta":
        # 内容增量：返回文本
        text = ""
        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
            text = chunk.delta.text
        
        openai_chunk["choices"] = [{
            "index": 0,
            "delta": {"content": text},
            "finish_reason": None
        }]
    
    elif chunk_type == "message_delta":
        # 消息结束：返回 finish_reason 和 usage
        stop_reason_map = {
            "end_turn": "stop",
            "max_tokens": "length",
            "stop_sequence": "stop",
        }
        
        finish_reason = None
        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'stop_reason'):
            finish_reason = stop_reason_map.get(chunk.delta.stop_reason, "stop")
        
        openai_chunk["choices"] = [{
            "index": 0,
            "delta": {},
            "finish_reason": finish_reason
        }]
        
        # 添加 usage（如果有）
        if hasattr(chunk, 'usage') and chunk.usage:
            input_tokens = (chunk.usage.input_tokens or 0) if hasattr(chunk.usage, 'input_tokens') else 0
            output_tokens = (chunk.usage.output_tokens or 0) if hasattr(chunk.usage, 'output_tokens') else 0
            openai_chunk["usage"] = {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
    
    else:
        # 其他类型：返回空 delta
        openai_chunk["choices"] = [{
            "index": 0,
            "delta": {},
            "finish_reason": None
        }]
    
    return json.dumps(openai_chunk)

