"""配置键常量定义"""

# ==================== 配置键常量 ====================

# 系统核心配置（只读）
CONFIG_KEY_SYSTEM_CONFIG = "system_config"
"""系统核心配置（包含 API 前缀、密钥、管理员账号等）"""

# Key 池相关
CONFIG_KEY_POOL_SIZE = "key_pool_size"
"""Key 池大小"""

# UA 列表
CONFIG_KEY_UA_LIST = "ua_list"
"""User Agent 列表（JSON 数组格式）"""

# 代理列表
CONFIG_KEY_PROXY_LIST = "proxy_list"
"""代理服务器列表（JSON 数组格式）"""

# Key 选择策略
CONFIG_KEY_SELECTION_STRATEGY = "key_selection_strategy"
"""Key 选择策略（0:随机）"""

# 日志记录配置
CONFIG_LOG_CONVERSATION_CONTENT = "log_conversation_content"
"""是否记录对话内容（request_body 和 response_body）"""

# 模型列表配置
CONFIG_KEY_OPENAI_MODELS = "openai_models"
"""OpenAI 模型列表（JSON 数组格式）"""

CONFIG_KEY_ANTHROPIC_MODELS = "anthropic_models"
"""Anthropic 模型列表（JSON 数组格式）"""


# ==================== 默认配置值 ====================

DEFAULT_POOL_SIZE = 5
"""默认 Key 池大小"""

DEFAULT_UA_LIST = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]
"""默认 UA 列表"""

DEFAULT_PROXY_LIST = []
"""默认代理列表"""

DEFAULT_SELECTION_STRATEGY = 0
"""默认选择策略（随机）"""

DEFAULT_LOG_CONVERSATION_CONTENT = False
"""默认不记录对话内容"""

# 从 models.py 导入默认模型列表
from constants.models import OPENAI_MODELS, ANTHROPIC_MODELS

DEFAULT_OPENAI_MODELS = sorted(list(OPENAI_MODELS))
"""默认 OpenAI 模型列表"""

DEFAULT_ANTHROPIC_MODELS = sorted(list(ANTHROPIC_MODELS))
"""默认 Anthropic 模型列表"""

# ==================== 配置组定义 ====================

# 系统只读配置键（不允许通过 API 修改）
READONLY_CONFIG_KEYS = [
    CONFIG_KEY_SYSTEM_CONFIG,
]

# 所有配置键列表（用于初始化和验证）
ALL_CONFIG_KEYS = [
    CONFIG_KEY_SYSTEM_CONFIG,
    CONFIG_KEY_POOL_SIZE,
    CONFIG_KEY_UA_LIST,
    CONFIG_KEY_PROXY_LIST,
    CONFIG_KEY_SELECTION_STRATEGY,
    CONFIG_LOG_CONVERSATION_CONTENT,
    CONFIG_KEY_OPENAI_MODELS,
    CONFIG_KEY_ANTHROPIC_MODELS,
]

# 配置键描述映射
CONFIG_KEY_DESCRIPTIONS = {
    CONFIG_KEY_SYSTEM_CONFIG: "系统核心配置（只读）：包含 API 前缀、密钥、管理员账号、JWT 密钥等",
    CONFIG_KEY_POOL_SIZE: "Key 池大小，控制同时活跃的 API Key 数量",
    CONFIG_KEY_UA_LIST: "User Agent 列表，用于请求时随机选择",
    CONFIG_KEY_PROXY_LIST: "代理服务器列表，格式：http://host:port",
    CONFIG_KEY_SELECTION_STRATEGY: "Key 选择策略：0-随机",
    CONFIG_LOG_CONVERSATION_CONTENT: "是否记录对话内容（request_body 和 response_body）：true-记录，false-不记录",
    CONFIG_KEY_OPENAI_MODELS: "OpenAI 支持的模型列表，每行一个模型名称",
    CONFIG_KEY_ANTHROPIC_MODELS: "Anthropic 支持的模型列表，每行一个模型名称",
}

