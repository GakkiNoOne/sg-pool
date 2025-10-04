"""统计服务 - 请求日志统计"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from entity.databases.request_log import RequestLog
from entity.databases.request_stats import RequestStats
from utils.logger import logger


def calculate_and_save_stats(db: Session, target_date: date, target_hour: Optional[int] = None):
    """
    计算并保存统计数据
    
    Args:
        db: 数据库会话
        target_date: 统计日期
        target_hour: 统计小时（None表示全天统计）
    """
    try:
        logger.info(f"开始统计: date={target_date}, hour={target_hour}")
        
        # 1. 全局统计
        _calculate_global_stats(db, target_date, target_hour)
        
        # 2. 按 Provider 统计
        _calculate_provider_stats(db, target_date, target_hour)
        
        # 3. 按 Model 统计
        _calculate_model_stats(db, target_date, target_hour)
        
        db.commit()
        logger.info(f"统计完成: date={target_date}, hour={target_hour}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"统计失败: {str(e)}")
        raise


def _calculate_global_stats(db: Session, target_date: date, target_hour: Optional[int]):
    """计算全局统计"""
    stats_data = _query_stats_data(db, target_date, target_hour)
    
    if not stats_data:
        logger.info(f"没有数据需要统计: date={target_date}, hour={target_hour}")
        return
    
    _upsert_stats(
        db=db,
        stat_date=target_date,
        stat_hour=target_hour,
        stat_type='global',
        provider=None,
        model=None,
        key_id=None,
        stats_data=stats_data
    )


def _calculate_provider_stats(db: Session, target_date: date, target_hour: Optional[int]):
    """按提供商统计"""
    # 获取所有提供商
    providers = db.query(RequestLog.provider).filter(
        _build_time_filter(RequestLog, target_date, target_hour)
    ).distinct().all()
    
    for (provider,) in providers:
        if not provider:
            continue
        
        stats_data = _query_stats_data(db, target_date, target_hour, provider=provider)
        
        _upsert_stats(
            db=db,
            stat_date=target_date,
            stat_hour=target_hour,
            stat_type='provider',
            provider=provider,
            model=None,
            key_id=None,
            stats_data=stats_data
        )


def _calculate_model_stats(db: Session, target_date: date, target_hour: Optional[int]):
    """按模型统计"""
    # 获取所有模型
    models = db.query(RequestLog.model, RequestLog.provider).filter(
        _build_time_filter(RequestLog, target_date, target_hour)
    ).distinct().all()
    
    for model, provider in models:
        if not model:
            continue
        
        stats_data = _query_stats_data(db, target_date, target_hour, model=model, provider=provider)
        
        _upsert_stats(
            db=db,
            stat_date=target_date,
            stat_hour=target_hour,
            stat_type='model',
            provider=provider,
            model=model,
            key_id=None,
            stats_data=stats_data
        )


def _query_stats_data(
    db: Session,
    target_date: date,
    target_hour: Optional[int],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    key_id: Optional[int] = None
) -> Dict:
    """
    查询统计数据
    
    Returns:
        包含所有统计指标的字典
    """
    from sqlalchemy import case
    
    # 构建基础查询
    query = db.query(
        func.count(RequestLog.id).label('request_count'),
        func.sum(case((RequestLog.status == 'success', 1), else_=0)).label('success_count'),
        func.sum(case((RequestLog.status == 'error', 1), else_=0)).label('error_count'),
        # OpenAI tokens
        func.sum(RequestLog.prompt_tokens).label('prompt_tokens'),
        func.sum(RequestLog.completion_tokens).label('completion_tokens'),
        # Anthropic tokens
        func.sum(RequestLog.input_tokens).label('input_tokens'),
        func.sum(RequestLog.output_tokens).label('output_tokens'),
        func.sum(RequestLog.cache_creation_input_tokens).label('cache_creation_tokens'),
        func.sum(RequestLog.cache_read_input_tokens).label('cache_read_tokens'),
        # Total tokens and cost
        func.sum(RequestLog.total_tokens).label('total_tokens'),
        func.sum(RequestLog.cost).label('total_cost'),
        # Latency stats
        func.avg(RequestLog.latency_ms).label('avg_latency_ms'),
        func.max(RequestLog.latency_ms).label('max_latency_ms'),
        func.min(RequestLog.latency_ms).label('min_latency_ms'),
    )
    
    # 添加时间过滤
    query = query.filter(_build_time_filter(RequestLog, target_date, target_hour))
    
    # 添加其他过滤条件
    if provider:
        query = query.filter(RequestLog.provider == provider)
    if model:
        query = query.filter(RequestLog.model == model)
    if key_id:
        query = query.filter(RequestLog.key_id == key_id)
    
    result = query.first()
    
    if not result or result.request_count == 0:
        return None
    
    return {
        'request_count': result.request_count or 0,
        'success_count': result.success_count or 0,
        'error_count': result.error_count or 0,
        'prompt_tokens': result.prompt_tokens or 0,
        'completion_tokens': result.completion_tokens or 0,
        'input_tokens': result.input_tokens or 0,
        'output_tokens': result.output_tokens or 0,
        'cache_creation_tokens': result.cache_creation_tokens or 0,
        'cache_read_tokens': result.cache_read_tokens or 0,
        'total_tokens': result.total_tokens or 0,
        'total_cost': float(result.total_cost) if result.total_cost else 0.0,
        'avg_latency_ms': int(result.avg_latency_ms) if result.avg_latency_ms else None,
        'max_latency_ms': result.max_latency_ms,
        'min_latency_ms': result.min_latency_ms,
    }


def _upsert_stats(
    db: Session,
    stat_date: date,
    stat_hour: Optional[int],
    stat_type: str,
    provider: Optional[str],
    model: Optional[str],
    key_id: Optional[int],
    stats_data: Dict
):
    """插入或更新统计记录"""
    # 查找现有记录
    query = db.query(RequestStats).filter(
        RequestStats.stat_date == stat_date,
        RequestStats.stat_type == stat_type
    )
    
    if stat_hour is not None:
        query = query.filter(RequestStats.stat_hour == stat_hour)
    else:
        query = query.filter(RequestStats.stat_hour.is_(None))
    
    if provider:
        query = query.filter(RequestStats.provider == provider)
    else:
        query = query.filter(RequestStats.provider.is_(None))
    
    if model:
        query = query.filter(RequestStats.model == model)
    else:
        query = query.filter(RequestStats.model.is_(None))
    
    if key_id:
        query = query.filter(RequestStats.key_id == key_id)
    else:
        query = query.filter(RequestStats.key_id.is_(None))
    
    existing = query.first()
    
    if existing:
        # 更新现有记录
        for key, value in stats_data.items():
            setattr(existing, key, value)
        existing.update_time = datetime.now()
        logger.debug(f"更新统计: {stat_type}, date={stat_date}, hour={stat_hour}")
    else:
        # 创建新记录
        new_stats = RequestStats(
            stat_date=stat_date,
            stat_hour=stat_hour,
            stat_type=stat_type,
            provider=provider,
            model=model,
            key_id=key_id,
            **stats_data
        )
        db.add(new_stats)
        logger.debug(f"新增统计: {stat_type}, date={stat_date}, hour={stat_hour}")


def _build_time_filter(model_class, target_date: date, target_hour: Optional[int]):
    """构建时间过滤条件"""
    if target_hour is not None:
        # 小时统计
        start_time = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=target_hour)
        end_time = start_time + timedelta(hours=1)
        return and_(
            model_class.create_time >= start_time,
            model_class.create_time < end_time
        )
    else:
        # 全天统计
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        return and_(
            model_class.create_time >= start_time,
            model_class.create_time < end_time
        )


# ==================== Dashboard 查询接口 ====================

def get_today_overview(db: Session) -> Dict:
    """获取今日总览数据"""
    today = date.today()
    
    # 查询今日全局统计
    stats = db.query(RequestStats).filter(
        RequestStats.stat_date == today,
        RequestStats.stat_hour.is_(None),
        RequestStats.stat_type == 'global'
    ).first()
    
    if not stats:
        return {
            'request_count': 0,
            'success_count': 0,
            'error_count': 0,
            'success_rate': 0,
            'total_cost': 0,
            'total_tokens': 0,
            'avg_latency_ms': 0,
        }
    
    success_rate = (stats.success_count / stats.request_count * 100) if stats.request_count > 0 else 0
    
    return {
        'request_count': stats.request_count,
        'success_count': stats.success_count,
        'error_count': stats.error_count,
        'success_rate': round(success_rate, 2),
        'total_cost': float(stats.total_cost),
        'total_tokens': stats.total_tokens,
        'avg_latency_ms': stats.avg_latency_ms or 0,
    }


def get_hourly_trend(db: Session, hours: int = 24) -> List[Dict]:
    """
    获取小时趋势数据
    
    Args:
        hours: 查询最近多少小时（默认24小时）
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # 查询今天和昨天的小时统计
    stats_list = db.query(RequestStats).filter(
        RequestStats.stat_date.in_([today, yesterday]),
        RequestStats.stat_hour.isnot(None),
        RequestStats.stat_type == 'global'
    ).order_by(RequestStats.stat_date, RequestStats.stat_hour).all()
    
    # 转换为列表
    result = []
    for stats in stats_list:
        hour_label = f"{stats.stat_date} {stats.stat_hour:02d}:00"
        result.append({
            'hour': hour_label,
            'request_count': stats.request_count,
            'success_count': stats.success_count,
            'error_count': stats.error_count,
            'total_cost': float(stats.total_cost),
            'total_tokens': stats.total_tokens,
        })
    
    # 只返回最近N小时
    return result[-hours:] if len(result) > hours else result


def get_provider_distribution(db: Session) -> List[Dict]:
    """获取提供商分布统计"""
    today = date.today()
    
    stats_list = db.query(RequestStats).filter(
        RequestStats.stat_date == today,
        RequestStats.stat_hour.is_(None),
        RequestStats.stat_type == 'provider'
    ).all()
    
    return [
        {
            'provider': stats.provider,
            'request_count': stats.request_count,
            'success_rate': round((stats.success_count / stats.request_count * 100) if stats.request_count > 0 else 0, 2),
            'total_cost': float(stats.total_cost),
            'total_tokens': stats.total_tokens,
        }
        for stats in stats_list
    ]


def get_model_distribution(db: Session, limit: int = 10) -> List[Dict]:
    """获取模型使用分布（Top N）"""
    today = date.today()
    
    stats_list = db.query(RequestStats).filter(
        RequestStats.stat_date == today,
        RequestStats.stat_hour.is_(None),
        RequestStats.stat_type == 'model'
    ).order_by(RequestStats.request_count.desc()).limit(limit).all()
    
    return [
        {
            'model': stats.model,
            'provider': stats.provider,
            'request_count': stats.request_count,
            'total_cost': float(stats.total_cost),
            'total_tokens': stats.total_tokens,
            'avg_latency_ms': stats.avg_latency_ms or 0,
        }
        for stats in stats_list
    ]


def get_error_stats(db: Session) -> Dict:
    """获取错误统计"""
    today = date.today()
    start_time = datetime.combine(today, datetime.min.time())
    end_time = start_time + timedelta(days=1)
    
    # 查询今日错误日志
    error_logs = db.query(
        RequestLog.error_type,
        func.count(RequestLog.id).label('count')
    ).filter(
        and_(
            RequestLog.create_time >= start_time,
            RequestLog.create_time < end_time,
            RequestLog.status == 'error',
            RequestLog.error_type.isnot(None)
        )
    ).group_by(RequestLog.error_type).all()
    
    error_distribution = [
        {
            'error_type': error_type or 'Unknown',
            'count': count
        }
        for error_type, count in error_logs
    ]
    
    # 获取总错误数
    total_errors = sum(item['count'] for item in error_distribution)
    
    return {
        'total_errors': total_errors,
        'error_distribution': error_distribution
    }

