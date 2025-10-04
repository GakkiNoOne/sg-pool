"""常量定义"""

# ==================== 配置键 ====================

CONFIG_KEY_SELECTION_STRATEGY = "key_selection_strategy"
CONFIG_KEY_POOL_SIZE = "key_pool_size"


# ==================== 默认配置值 ====================

DEFAULT_POOL_SIZE = 5


# ==================== 选择策略枚举 ====================

STRATEGY_RANDOM = 0
STRATEGY_ROUND_ROBIN = 1
STRATEGY_LEAST_USED = 2


# ==================== Provider 相关常量 ====================

PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"

# OpenAI API 配置
OPENAI_API_URL = "https://ampcode.com/api/provider/openai/v1/chat/completions"
OPENAI_API_VERSION = "v1"

# Anthropic API 配置
ANTHROPIC_API_URL = "https://ampcode.com/api/provider/anthropic/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"

# 默认请求头
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
DEFAULT_ACCEPT_LANGUAGE = "zh-CN,zh;q=0.9,en;q=0.8"

