"""请求流程上下文对象"""

from typing import Optional
from entity.req import ChatCompletionRequest
from entity.databases.api_key import APIKey
from constants import get_provider_by_model


class RequestContext:
    """请求处理流程的上下文，贯穿整个请求处理过程"""
    
    def __init__(self, request: ChatCompletionRequest, db=None):
        self.request = request
        self.db = db  # 数据库会话
        self.provider: Optional[str] = None
        self.is_stream: bool = False
        self.api_key: Optional[str] = None  # API Key 字符串
        self.api_key_entity: Optional[APIKey] = None  # APIKey 对象（用于日志记录）
        self.api_key_from_pool: bool = False  # 标记：API Key 是否从池中选择（True=池中选择，False=参数指定）
        self.proxy: Optional[str] = None  # 代理地址
        self.url: Optional[str] = None
        self.headers: Optional[dict] = None
        self.body: Optional[dict] = None
        self.response = None
        self.error: Optional[str] = None
        self.start_time: float = 0.0  # 请求开始时间
    
    def init(self):
        """初始化上下文基本信息（不包含参数校验）"""
        import time
        from constants import OPENAI_API_URL, ANTHROPIC_API_URL, PROVIDER_ANTHROPIC, PROVIDER_OPENAI
        
        # 记录开始时间
        self.start_time = time.time()
        
        # 检测 provider（不做校验，只是设置）
        self.provider = get_provider_by_model(self.request.model)
        
        # 设置 URL（根据 provider）
        if self.provider == PROVIDER_ANTHROPIC:
            self.url = ANTHROPIC_API_URL
        else:
            self.url = OPENAI_API_URL
        
        # 判断是否流式
        self.is_stream = self.request.stream if self.request.stream is not None else False
        
        # 提取 API Key（如果请求中指定了）
        if self.request.api_key:
            self.api_key = self.request.api_key
            self.api_key_from_pool = False  # 参数指定的 key
        else:
            self.api_key_from_pool = True  # 需要从池中选择

        # 提取代理（如果请求中指定了）
        if self.request.proxy:
            self.proxy = self.request.proxy

    def __repr__(self):
        return f"<RequestContext(provider='{self.provider}', model='{self.request.model}')>"

