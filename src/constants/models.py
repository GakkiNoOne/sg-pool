"""模型常量定义"""

from constants.constants import PROVIDER_OPENAI, PROVIDER_ANTHROPIC


# OpenAI 模型列表
OPENAI_MODELS = {
    # GPT-4 系列
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4-turbo-preview",
    "gpt-4-0125-preview",
    "gpt-4-1106-preview",
    "gpt-4-vision-preview",
    "gpt-4-32k",
    "gpt-4-0613",
    "gpt-4-32k-0613",
    
    # GPT-4o 系列
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4o-2024-05-13",
    "gpt-4o-2024-08-06",
    
    # GPT-3.5 系列
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-0613",
    
    # O1 系列
    "o1",
    "o1-mini",
    "o1-preview",
}


# Anthropic 模型列表
ANTHROPIC_MODELS = {
    # Claude 3.5 系列
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    
    # Claude 3 系列
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    
    # Claude Sonnet 4 系列
    "claude-sonnet-4-20250514",
    
    # 通用别名
    "claude-3-opus",
    "claude-3-sonnet",
    "claude-3-haiku",
    "claude-3.5-sonnet",
    "claude-sonnet-4",
}


# 模型到 Provider 的映射
MODEL_TO_PROVIDER = {}

# 构建映射
for model in OPENAI_MODELS:
    MODEL_TO_PROVIDER[model] = PROVIDER_OPENAI

for model in ANTHROPIC_MODELS:
    MODEL_TO_PROVIDER[model] = PROVIDER_ANTHROPIC


def get_provider_by_model(model: str) -> str:
    # 精确匹配
    if model in MODEL_TO_PROVIDER:
        return MODEL_TO_PROVIDER[model]
    return None
