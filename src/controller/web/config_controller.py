"""Web 配置管理控制器"""

from typing import Dict, List
import json
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from entity.databases.database import get_db
from entity.res.base import Response
from service.databases import config_service
from constants.config_key import CONFIG_KEY_UA_LIST, CONFIG_KEY_PROXY_LIST, READONLY_CONFIG_KEYS
from utils.logger import logger
from utils.admin_auth import verify_admin_token

router = APIRouter(prefix="/api/configs", tags=["Config Management"], dependencies=[Depends(verify_admin_token)])


# ==================== 系统配置专用请求模型 ====================

class SystemConfigSaveRequest(BaseModel):
    """保存系统配置请求"""
    configs: Dict[str, str] = Field(..., description="配置字典 {key: value}")


# ==================== 系统配置专用接口 ====================

@router.post("/system/get", response_model=Response[Dict], summary="获取所有系统配置")
async def get_system_configs(
    db: Session = Depends(get_db)
):
    """获取所有系统配置（返回 {key: value} 格式，以及只读标记和环境变量配置）"""
    try:
        from configs.config import settings
        
        configs = config_service.get_all_system_configs(db)
        logger.info(f"获取系统配置成功")
        
        # 获取环境变量配置（只读）
        env_configs = {
            "API_PREFIX": settings.API_PREFIX,
            "API_SECRET": settings.API_SECRET if settings.API_SECRET else "（未配置）",
            "ADMIN_PREFIX": settings.ADMIN_PREFIX,
            "ADMIN_USERNAME": settings.ADMIN_USERNAME,
            "ADMIN_PASSWORD": "******",  # 密码不显示
            "JWT_SECRET_KEY": "******",  # JWT密钥不显示
        }
        
        # 返回配置、只读标记和环境变量配置
        result = {
            "configs": configs,
            "readonly_keys": READONLY_CONFIG_KEYS,
            "env_configs": env_configs
        }
        
        return Response[Dict].ok(
            data=result,
            msg="获取成功"
        )
    except Exception as e:
        logger.error(f"获取系统配置失败: {str(e)}")
        return Response[Dict].fail(msg=str(e))


@router.post("/system/save", response_model=Response[None], summary="保存系统配置")
async def save_system_configs(
    request: SystemConfigSaveRequest = Body(...),
    db: Session = Depends(get_db)
):
    """批量保存系统配置"""
    try:
        # 保存配置
        config_service.save_system_configs(db, request.configs)
        logger.info(f"保存系统配置成功: {list(request.configs.keys())}")
        
        # 重新加载全局配置
        from configs.global_config import global_config
        global_config.reload(db)
        logger.info("全局配置已重新加载")
        
        # 检查并更新启用的key的UA和proxy
        await _update_enabled_keys_config(db, request.configs)
        
        return Response[None].ok(msg="保存成功")
    except Exception as e:
        logger.error(f"保存系统配置失败: {str(e)}")
        return Response[None].fail(msg=str(e))


async def _update_enabled_keys_config(db: Session, configs: Dict[str, str]):
    """
    更新所有启用的key的UA和proxy，确保它们在配置列表中
    
    Args:
        db: 数据库会话
        configs: 配置字典
    """
    try:
        import random
        from entity.databases.api_key import APIKey
        from datetime import datetime
        
        # 解析配置中的UA列表
        ua_list = []
        if CONFIG_KEY_UA_LIST in configs:
            try:
                ua_list = json.loads(configs[CONFIG_KEY_UA_LIST])
                if not isinstance(ua_list, list) or len(ua_list) == 0:
                    logger.warning("UA列表为空，跳过更新")
                    return
            except:
                logger.error("解析UA列表失败")
                return
        
        # 解析配置中的代理列表
        proxy_list = []
        if CONFIG_KEY_PROXY_LIST in configs:
            try:
                proxy_list = json.loads(configs[CONFIG_KEY_PROXY_LIST])
                if not isinstance(proxy_list, list):
                    proxy_list = []
            except:
                logger.error("解析代理列表失败")
        
        # 查询所有启用的key
        enabled_keys = db.query(APIKey).filter(APIKey.enabled == True).all()
        
        updated_count = 0
        for key in enabled_keys:
            need_update = False
            
            # 检查UA是否在配置列表中
            if key.ua not in ua_list:
                key.ua = random.choice(ua_list)
                need_update = True
                logger.info(f"Key {key.name} (ID: {key.id}) 的UA不在配置中，已更新为: {key.ua}")
            
            # 检查proxy是否在配置列表中
            if proxy_list:
                # 代理列表不为空：检查key的proxy是否在列表中
                if key.proxy not in proxy_list:
                    key.proxy = random.choice(proxy_list)
                    need_update = True
                    logger.info(f"Key {key.name} (ID: {key.id}) 的proxy不在配置中，已更新为: {key.proxy}")
            else:
                # 代理列表为空：将所有key的proxy置空
                if key.proxy:
                    key.proxy = ""
                    need_update = True
                    logger.info(f"Key {key.name} (ID: {key.id}) 的proxy已置空（配置中无代理）")
            
            if need_update:
                key.update_time = datetime.now()
                updated_count += 1
        
        # 提交更新
        if updated_count > 0:
            db.commit()
            logger.info(f"已更新 {updated_count} 个启用的key的配置")
        else:
            logger.info("所有启用的key配置都是有效的，无需更新")
            
    except Exception as e:
        logger.error(f"更新启用的key配置失败: {str(e)}")
        db.rollback()


@router.post("/ua/list", response_model=Response[List[str]], summary="获取UA列表")
async def get_ua_list(
    db: Session = Depends(get_db)
):
    """获取系统配置中的UA列表"""
    try:
        configs = config_service.get_all_system_configs(db)
        ua_list_str = configs.get(CONFIG_KEY_UA_LIST, "[]")
        
        # 解析 JSON
        try:
            ua_list = json.loads(ua_list_str)
            if not isinstance(ua_list, list):
                ua_list = []
        except:
            ua_list = []
        
        logger.info(f"获取UA列表成功: {len(ua_list)} 个")
        return Response[List[str]].ok(data=ua_list, msg="获取成功")
    except Exception as e:
        logger.error(f"获取UA列表失败: {str(e)}")
        return Response[List[str]].fail(msg=str(e))


@router.post("/proxy/list", response_model=Response[List[str]], summary="获取代理列表")
async def get_proxy_list(
    db: Session = Depends(get_db)
):
    """获取系统配置中的代理列表"""
    try:
        configs = config_service.get_all_system_configs(db)
        proxy_list_str = configs.get(CONFIG_KEY_PROXY_LIST, "[]")
        
        # 解析 JSON
        try:
            proxy_list = json.loads(proxy_list_str)
            if not isinstance(proxy_list, list):
                proxy_list = []
        except:
            proxy_list = []
        
        logger.info(f"获取代理列表成功: {len(proxy_list)} 个")
        return Response[List[str]].ok(data=proxy_list, msg="获取成功")
    except Exception as e:
        logger.error(f"获取代理列表失败: {str(e)}")
        return Response[List[str]].fail(msg=str(e))

