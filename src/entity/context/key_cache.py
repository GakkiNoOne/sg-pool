"""API Key 缓存池实体"""

import random
from typing import List, Optional
from entity.databases.api_key import APIKey


class KeyCache:
    """API Key 缓存池"""
    
    def __init__(self):
        self._keys: List[APIKey] = []
    
    def get_all_keys(self) -> List[APIKey]:
        """获取缓存中的所有 key"""
        return self._keys.copy()
    
    def add_key(self, key: APIKey):
        """向缓存池添加一个 key"""
        # 避免重复添加
        if not any(k.id == key.id for k in self._keys):
            self._keys.append(key)
    
    def get_random_key(self) -> Optional[APIKey]:
        """从缓存池中随机获取一个 key"""
        if not self._keys:
            return None
        return random.choice(self._keys)
    
    def remove_key(self, key_id: int):
        """从缓存池移除指定的 key"""
        self._keys = [k for k in self._keys if k.id != key_id]
    
    def clear(self):
        """清空缓存池"""
        self._keys = []
    
    def size(self) -> int:
        """获取缓存池中 key 的数量"""
        return len(self._keys)

