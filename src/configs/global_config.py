"""全局配置对象 - 将数据库配置加载到内存中，避免频繁查询数据库"""

import json
from typing import List, Optional
from utils.logger import logger


class GlobalConfig:
    """全局配置单例"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # 配置字段
            self._key_pool_size: int = 5
            self._key_selection_strategy: str = '0'
            self._ua_list: List[str] = []
            self._proxy_list: List[str] = []
            self._log_conversation_content: bool = False
            self._openai_models: List[str] = []
            self._anthropic_models: List[str] = []
            
            GlobalConfig._initialized = True
    
    def load_from_db(self, db):
        """从数据库加载配置"""
        try:
            from service.databases import config_service
            from constants.config_key import (
                CONFIG_KEY_POOL_SIZE,
                CONFIG_KEY_SELECTION_STRATEGY,
                CONFIG_KEY_UA_LIST,
                CONFIG_KEY_PROXY_LIST,
                CONFIG_LOG_CONVERSATION_CONTENT,
                CONFIG_KEY_OPENAI_MODELS,
                CONFIG_KEY_ANTHROPIC_MODELS,
                DEFAULT_POOL_SIZE,
                DEFAULT_SELECTION_STRATEGY,
                DEFAULT_LOG_CONVERSATION_CONTENT,
                DEFAULT_OPENAI_MODELS,
                DEFAULT_ANTHROPIC_MODELS
            )
            
            configs = config_service.get_all_system_configs(db)
            
            # 加载 key_pool_size
            try:
                self._key_pool_size = int(configs.get(CONFIG_KEY_POOL_SIZE, str(DEFAULT_POOL_SIZE)))
            except:
                self._key_pool_size = DEFAULT_POOL_SIZE
            
            # 加载 key_selection_strategy
            self._key_selection_strategy = configs.get(
                CONFIG_KEY_SELECTION_STRATEGY, 
                str(DEFAULT_SELECTION_STRATEGY)
            )
            
            # 加载 ua_list
            ua_list_str = configs.get(CONFIG_KEY_UA_LIST, "[]")
            try:
                self._ua_list = json.loads(ua_list_str)
                if not isinstance(self._ua_list, list):
                    self._ua_list = []
            except:
                self._ua_list = []
            
            # 加载 proxy_list
            proxy_list_str = configs.get(CONFIG_KEY_PROXY_LIST, "[]")
            try:
                self._proxy_list = json.loads(proxy_list_str)
                if not isinstance(self._proxy_list, list):
                    self._proxy_list = []
            except:
                self._proxy_list = []
            
            # 加载 log_conversation_content
            log_content_str = configs.get(
                CONFIG_LOG_CONVERSATION_CONTENT, 
                str(DEFAULT_LOG_CONVERSATION_CONTENT)
            )
            self._log_conversation_content = log_content_str.lower() == 'true'
            
            # 加载 openai_models
            openai_models_str = configs.get(CONFIG_KEY_OPENAI_MODELS, json.dumps(DEFAULT_OPENAI_MODELS))
            try:
                self._openai_models = json.loads(openai_models_str)
                if not isinstance(self._openai_models, list):
                    self._openai_models = DEFAULT_OPENAI_MODELS
            except:
                self._openai_models = DEFAULT_OPENAI_MODELS
            
            # 加载 anthropic_models
            anthropic_models_str = configs.get(CONFIG_KEY_ANTHROPIC_MODELS, json.dumps(DEFAULT_ANTHROPIC_MODELS))
            try:
                self._anthropic_models = json.loads(anthropic_models_str)
                if not isinstance(self._anthropic_models, list):
                    self._anthropic_models = DEFAULT_ANTHROPIC_MODELS
            except:
                self._anthropic_models = DEFAULT_ANTHROPIC_MODELS
            
            logger.info(f"全局配置加载成功: pool_size={self._key_pool_size}, "
                       f"ua_count={len(self._ua_list)}, proxy_count={len(self._proxy_list)}, "
                       f"log_content={self._log_conversation_content}, "
                       f"openai_models_count={len(self._openai_models)}, "
                       f"anthropic_models_count={len(self._anthropic_models)}")
            
        except Exception as e:
            logger.error(f"加载全局配置失败: {str(e)}")
    
    @property
    def key_pool_size(self) -> int:
        """Key 池大小"""
        return self._key_pool_size
    
    @property
    def key_selection_strategy(self) -> str:
        """Key 选择策略"""
        return self._key_selection_strategy
    
    @property
    def ua_list(self) -> List[str]:
        """UA 列表"""
        return self._ua_list.copy()  # 返回副本，避免被外部修改
    
    @property
    def proxy_list(self) -> List[str]:
        """代理列表"""
        return self._proxy_list.copy()  # 返回副本，避免被外部修改
    
    @property
    def should_log_conversation_content(self) -> bool:
        """是否记录对话内容"""
        return self._log_conversation_content
    
    @property
    def openai_models(self) -> List[str]:
        """OpenAI 模型列表"""
        return self._openai_models.copy()  # 返回副本，避免被外部修改
    
    @property
    def anthropic_models(self) -> List[str]:
        """Anthropic 模型列表"""
        return self._anthropic_models.copy()  # 返回副本，避免被外部修改
    
    def is_model_supported(self, model: str, provider: str) -> bool:
        """检查模型是否在支持列表中"""
        if provider == 'openai':
            return model in self._openai_models
        elif provider == 'anthropic':
            return model in self._anthropic_models
        return False
    
    def reload(self, db):
        """重新加载配置（配置更新后调用）"""
        logger.info("重新加载全局配置...")
        self.load_from_db(db)


# 全局配置实例
global_config = GlobalConfig()

