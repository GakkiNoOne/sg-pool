"""Web Dashboard 控制器"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from entity.databases.database import get_db
from entity.databases.api_key import APIKey
from entity.res.base import Response
from service.databases import stats_service, key_service
from service.stats_task import trigger_stats_now
from utils.logger import logger
from utils.admin_auth import verify_admin_token

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"], dependencies=[Depends(verify_admin_token)])


@router.post("/overview", summary="获取今日总览")
async def get_overview(db: Session = Depends(get_db)):
    """
    获取今日总览数据
    
    返回:
    - request_count: 总请求数
    - success_count: 成功请求数
    - error_count: 失败请求数
    - success_rate: 成功率（百分比）
    - total_cost: 总成本（美元）
    - total_tokens: 总 token 数
    - avg_latency_ms: 平均延迟（毫秒）
    """
    try:
        data = stats_service.get_today_overview(db)
        return Response.ok(data=data, msg="获取成功")
    except Exception as e:
        logger.error(f"获取今日总览失败: {str(e)}")
        return Response.fail(msg=str(e))


@router.post("/hourly-trend", summary="获取小时趋势")
async def get_hourly_trend(db: Session = Depends(get_db)):
    """
    获取最近24小时的趋势数据
    
    返回列表，每项包含:
    - hour: 小时标签（如"2025-10-04 14:00"）
    - request_count: 请求数
    - success_count: 成功数
    - error_count: 失败数
    - total_cost: 成本
    - total_tokens: token数
    """
    try:
        data = stats_service.get_hourly_trend(db, hours=24)
        return Response.ok(data=data, msg="获取成功")
    except Exception as e:
        logger.error(f"获取小时趋势失败: {str(e)}")
        return Response.fail(msg=str(e))


@router.post("/provider-distribution", summary="获取提供商分布")
async def get_provider_distribution(db: Session = Depends(get_db)):
    """
    获取今日各提供商的使用情况
    
    返回列表，每项包含:
    - provider: 提供商名称
    - request_count: 请求数
    - success_rate: 成功率
    - total_cost: 总成本
    - total_tokens: 总 token 数
    """
    try:
        data = stats_service.get_provider_distribution(db)
        return Response.ok(data=data, msg="获取成功")
    except Exception as e:
        logger.error(f"获取提供商分布失败: {str(e)}")
        return Response.fail(msg=str(e))


@router.post("/model-distribution", summary="获取模型使用分布")
async def get_model_distribution(db: Session = Depends(get_db)):
    """
    获取今日各模型的使用情况（Top 10）
    
    返回列表，每项包含:
    - model: 模型名称
    - provider: 提供商
    - request_count: 请求数
    - total_cost: 总成本
    - total_tokens: 总 token 数
    - avg_latency_ms: 平均延迟
    """
    try:
        data = stats_service.get_model_distribution(db, limit=10)
        return Response.ok(data=data, msg="获取成功")
    except Exception as e:
        logger.error(f"获取模型分布失败: {str(e)}")
        return Response.fail(msg=str(e))


@router.post("/error-stats", summary="获取错误统计")
async def get_error_stats(db: Session = Depends(get_db)):
    """
    获取今日错误统计
    
    返回:
    - total_errors: 总错误数
    - error_distribution: 错误类型分布列表
      - error_type: 错误类型
      - count: 错误次数
    """
    try:
        data = stats_service.get_error_stats(db)
        return Response.ok(data=data, msg="获取成功")
    except Exception as e:
        logger.error(f"获取错误统计失败: {str(e)}")
        return Response.fail(msg=str(e))


@router.post("/trigger-stats", summary="手动触发统计")
async def trigger_stats():
    """
    手动触发一次统计任务
    
    用于测试或需要立即更新统计数据时使用
    """
    try:
        await trigger_stats_now()
        return Response.ok(msg="统计任务已触发")
    except Exception as e:
        logger.error(f"触发统计任务失败: {str(e)}")
        return Response.fail(msg=str(e))


@router.post("/key-balance-stats", summary="获取 Key 余额统计")
async def get_key_balance_stats(db: Session = Depends(get_db)):
    """
    获取可用 Key 的余额统计
    
    返回:
    - total_keys: 总 Key 数量
    - enabled_keys: 可用 Key 数量
    - total_balance: 可用 Key 总余额
    - keys_with_balance: 有余额信息的 Key 数量
    """
    try:
        # 查询所有 Key 统计
        total_keys = db.query(func.count(APIKey.id)).scalar()
        
        # 查询可用 Key 数量
        enabled_keys = db.query(func.count(APIKey.id)).filter(
            APIKey.enabled == True
        ).scalar()
        
        # 查询可用 Key 的总余额
        total_balance_result = db.query(
            func.sum(APIKey.balance)
        ).filter(
            APIKey.enabled == True,
            APIKey.balance.isnot(None)
        ).scalar()
        
        # 查询有余额信息的可用 Key 数量
        keys_with_balance = db.query(func.count(APIKey.id)).filter(
            APIKey.enabled == True,
            APIKey.balance.isnot(None)
        ).scalar()
        
        total_balance = float(total_balance_result) if total_balance_result else 0.0
        
        data = {
            'total_keys': total_keys or 0,
            'enabled_keys': enabled_keys or 0,
            'total_balance': total_balance,
            'keys_with_balance': keys_with_balance or 0,
        }
        
        return Response.ok(data=data, msg="获取成功")
    except Exception as e:
        logger.error(f"获取 Key 余额统计失败: {str(e)}")
        return Response.fail(msg=str(e))


@router.post("/update-keys-balance", summary="手动更新 Key 余额")
async def update_keys_balance(db: Session = Depends(get_db)):
    """
    手动触发更新所有可用 Key 的余额
    
    逻辑：
    1. 获取所有可用的 Key（enabled=True）
    2. 对每个 Key，统计所有请求日志的成本总和
    3. 计算余额：balance = total_balance - sum(cost)
    4. 更新 balance 和 balance_last_update
    
    返回:
    - total_keys: 处理的 Key 总数
    - updated_keys: 成功更新的 Key 数
    - failed_keys: 更新失败的 Key 数
    - errors: 错误信息列表
    """
    try:
        logger.info("手动触发 Key 余额更新")
        stats = key_service.update_all_keys_balance(db)
        
        if stats['failed_keys'] > 0:
            return Response.ok(
                data=stats, 
                msg=f"余额更新完成，但有 {stats['failed_keys']} 个 Key 更新失败"
            )
        else:
            return Response.ok(
                data=stats, 
                msg=f"余额更新成功，共更新 {stats['updated_keys']} 个 Key"
            )
    except Exception as e:
        logger.error(f"手动更新 Key 余额失败: {str(e)}")
        return Response.fail(msg=str(e))

