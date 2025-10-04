"""缓存服务"""

from typing import List, Optional
from entity.databases.api_key import APIKey
from entity.context import KeyCache


# 全局 Key 缓存实例
_key_cache = KeyCache()


def get_all_keys() -> List[APIKey]:
    """获取所有缓存的 key"""
    return _key_cache.get_all_keys()


def add_key(key: APIKey):
    """向缓存添加 key"""
    _key_cache.add_key(key)


def get_random_key() -> Optional[APIKey]:
    """随机获取一个 key"""
    return _key_cache.get_random_key()


def remove_key(key_id: int):
    """从缓存移除指定的 key"""
    _key_cache.remove_key(key_id)

