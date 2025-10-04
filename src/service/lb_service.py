


"""负载均衡服务"""

from typing import Optional

from entity.context import RequestContext
from service.databases import key_service
from utils.logger import logger
from configs.global_config import global_config


def get_key(context: RequestContext) -> Optional[str]:
    """
    获取一个可用的 API Key 字符串
    
    Returns:
        API Key 字符串，如果没有可用的则返回 None
    """
    
    # 如果 context 中已有 api_key（从请求参数中提取的），直接使用
    if context.api_key:
        logger.info(f"使用请求中指定的 API Key")
        return context.api_key
    
    # 否则通过负载均衡选择
    # 获取缓存中的 key
    cached_keys = key_service.get_cached_keys()
    logger.debug(f"当前缓存 Key 数量: {len(cached_keys)}")

    # 如果缓存不足，从数据库补充
    current_cache_size = len(cached_keys)
    pool_size = global_config.key_pool_size  # 使用全局配置
    if current_cache_size < pool_size:
        needed_count = pool_size - current_cache_size
        logger.info(f"缓存不足，需要补充 {needed_count} 个 Key")
        
        cached_key_ids = [key.id for key in cached_keys]
        new_keys = key_service.get_available_keys(context.db, limit=needed_count, exclude_ids=cached_key_ids)
        
        logger.info(f"从数据库获取到 {len(new_keys)} 个可用 Key")
        for key in new_keys:
            key_service.add_key_to_cache(key)
    
    # 根据策略选择 key（目前只支持随机）
    selected_key = key_service.get_random_key_from_cache()
    
    if selected_key:
        logger.info(f"选中 Key: id={selected_key.id}, name={selected_key.name}")
        context.api_key_entity = selected_key  # 保存 APIKey 对象（用于日志记录）
        context.api_key = selected_key.api_key  # 保存 API Key 字符串
        
        # 设置代理（优先使用 Key 自带的代理，如果没有则使用请求中指定的代理）
        if selected_key.proxy and selected_key.proxy.strip():
            context.proxy = selected_key.proxy.strip()
            logger.info(f"✅ 使用 Key 绑定的代理: {context.proxy}")
        elif context.proxy:
            logger.info(f"✅ 使用请求指定的代理: {context.proxy}")
        else:
            logger.info(f"⚠️ 未配置代理，直连")
        
        # 打印 API Key 前缀（用于调试）
        api_key_prefix = selected_key.api_key[:20] + "..." if len(selected_key.api_key) > 20 else selected_key.api_key
        logger.info(f"🔑 API Key: {api_key_prefix}")
        
        # 注意：api_key_from_pool 已在 context.init() 时设置为 True
        return selected_key.api_key
    else:
        logger.warning("没有可用的 API Key")
        return None