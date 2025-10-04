"""配置管理业务服务"""

from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session
from datetime import datetime
import json
from entity.databases.config import Config
from entity.req.config import ConfigCreateRequest, ConfigUpdateRequest
from constants.config_key import (
    CONFIG_KEY_POOL_SIZE,
    CONFIG_KEY_UA_LIST,
    CONFIG_KEY_PROXY_LIST,
    CONFIG_KEY_SELECTION_STRATEGY,
    CONFIG_LOG_CONVERSATION_CONTENT,
    CONFIG_KEY_OPENAI_MODELS,
    CONFIG_KEY_ANTHROPIC_MODELS,
    DEFAULT_POOL_SIZE,
    DEFAULT_UA_LIST,
    DEFAULT_PROXY_LIST,
    DEFAULT_SELECTION_STRATEGY,
    DEFAULT_LOG_CONVERSATION_CONTENT,
    DEFAULT_OPENAI_MODELS,
    DEFAULT_ANTHROPIC_MODELS,
    CONFIG_KEY_DESCRIPTIONS,
    READONLY_CONFIG_KEYS
)


def create_config(db: Session, request: ConfigCreateRequest) -> Config:
    """创建配置"""
    config = Config(
        key=request.key,
        value=request.value,
        memo=request.memo
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return config


def get_config_by_id(db: Session, config_id: int) -> Optional[Config]:
    """根据 ID 获取配置"""
    return db.query(Config).filter(Config.id == config_id).first()


def get_config_by_key(db: Session, key: str) -> Optional[Config]:
    """根据 key 获取配置"""
    return db.query(Config).filter(Config.key == key).first()


def get_config_value(db: Session, key: str, default_value: str = "") -> str:
    """
    根据 key 获取配置值
    
    Args:
        db: 数据库会话
        key: 配置键
        default_value: 默认值
        
    Returns:
        配置值，如果不存在则返回默认值
    """
    config = get_config_by_key(db, key)
    return config.value if config else default_value


def update_config(db: Session, config_id: int, request: ConfigUpdateRequest) -> Optional[Config]:
    """更新配置"""
    config = get_config_by_id(db, config_id)
    
    if not config:
        return None
    
    # 检查是否为只读配置
    if config.key in READONLY_CONFIG_KEYS:
        raise ValueError(f"配置 '{config.key}' 为只读配置，不允许修改")
    
    # 更新字段
    update_data = request.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(config, key, value)
    
    config.update_time = datetime.now()
    
    db.commit()
    db.refresh(config)
    
    return config


def delete_config(db: Session, config_id: int) -> bool:
    """删除配置"""
    config = get_config_by_id(db, config_id)
    
    if not config:
        return False
    
    # 检查是否为只读配置
    if config.key in READONLY_CONFIG_KEYS:
        raise ValueError(f"配置 '{config.key}' 为只读配置，不允许删除")
    
    db.delete(config)
    db.commit()
    
    return True


def query_configs(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    key: Optional[str] = None
) -> Tuple[List[Config], int]:
    """
    查询配置列表
    
    返回: (列表, 总数)
    """
    query = db.query(Config)
    
    # 过滤条件
    if key:
        query = query.filter(Config.key.like(f"%{key}%"))
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    items = query.order_by(Config.create_time.desc()).offset(offset).limit(page_size).all()
    
    return items, total


def get_all_system_configs(db: Session) -> Dict[str, str]:
    """
    获取所有系统配置
    
    返回: {key: value} 的字典，如果配置不存在则返回默认值
    """
    # 查询所有配置
    configs = db.query(Config).all()
    config_dict = {c.key: c.value for c in configs}
    
    # 确保所有系统配置键都存在，不存在则使用默认值
    result = {}
    
    # Key 池大小
    result[CONFIG_KEY_POOL_SIZE] = config_dict.get(
        CONFIG_KEY_POOL_SIZE, 
        str(DEFAULT_POOL_SIZE)
    )
    
    # UA 列表
    result[CONFIG_KEY_UA_LIST] = config_dict.get(
        CONFIG_KEY_UA_LIST,
        json.dumps(DEFAULT_UA_LIST, ensure_ascii=False)
    )
    
    # 代理列表
    result[CONFIG_KEY_PROXY_LIST] = config_dict.get(
        CONFIG_KEY_PROXY_LIST,
        json.dumps(DEFAULT_PROXY_LIST, ensure_ascii=False)
    )
    
    # 选择策略
    result[CONFIG_KEY_SELECTION_STRATEGY] = config_dict.get(
        CONFIG_KEY_SELECTION_STRATEGY,
        str(DEFAULT_SELECTION_STRATEGY)
    )
    
    # 日志记录配置
    result[CONFIG_LOG_CONVERSATION_CONTENT] = config_dict.get(
        CONFIG_LOG_CONVERSATION_CONTENT,
        str(DEFAULT_LOG_CONVERSATION_CONTENT).lower()
    )
    
    # OpenAI 模型列表
    result[CONFIG_KEY_OPENAI_MODELS] = config_dict.get(
        CONFIG_KEY_OPENAI_MODELS,
        json.dumps(DEFAULT_OPENAI_MODELS, ensure_ascii=False)
    )
    
    # Anthropic 模型列表
    result[CONFIG_KEY_ANTHROPIC_MODELS] = config_dict.get(
        CONFIG_KEY_ANTHROPIC_MODELS,
        json.dumps(DEFAULT_ANTHROPIC_MODELS, ensure_ascii=False)
    )
    
    return result


def save_system_configs(db: Session, configs: Dict[str, str]) -> None:
    """
    批量保存系统配置
    
    参数:
        configs: {key: value} 的字典
    """
    for key, value in configs.items():
        # 查找现有配置
        config = db.query(Config).filter(Config.key == key).first()
        
        if config:
            # 更新
            config.value = value
            config.update_time = datetime.now()
        else:
            # 创建
            config = Config(
                key=key,
                value=value,
                memo=CONFIG_KEY_DESCRIPTIONS.get(key, "")
            )
            db.add(config)
    
    db.commit()
