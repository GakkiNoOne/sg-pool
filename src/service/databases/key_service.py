"""API Key 业务服务"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from entity.databases.api_key import APIKey
from entity.databases.request_log import RequestLog
from entity.req.key import APIKeyCreateRequest, APIKeyUpdateRequest, APIKeyBatchCreateRequest
from mapper import api_key_mapper
from service import cache_service
from utils.logger import logger


# ==================== 缓存相关 ====================

def get_available_keys(db: Session, limit: int, exclude_ids: list[int] = None) -> list[APIKey]:
    """获取指定数量的可用 Key"""
    return api_key_mapper.query_available_keys(db, limit=limit, exclude_ids=exclude_ids)


def get_cached_keys() -> List[APIKey]:
    """获取缓存中的所有 Key"""
    return cache_service.get_all_keys()


def add_key_to_cache(key: APIKey):
    """添加 Key 到缓存"""
    cache_service.add_key(key)


def get_random_key_from_cache() -> Optional[APIKey]:
    """从缓存随机获取一个 Key"""
    return cache_service.get_random_key()


# ==================== CRUD 操作 ====================

def create_api_key(db: Session, request: APIKeyCreateRequest) -> APIKey:
    """创建 API Key"""
    api_key = APIKey(
        name=request.name,
        api_key=request.api_key,
        ua=request.ua,
        proxy=request.proxy,
        enabled=request.enabled,
        balance=request.balance,
        total_balance=request.total_balance,
        memo=request.memo,
        balance_last_update=datetime.now() if request.balance is not None else None
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return api_key


def batch_create_api_keys(db: Session, request: APIKeyBatchCreateRequest, ua_list: List[str], proxy_list: List[str]) -> Tuple[List[APIKey], int, int]:
    """
    批量创建 API Keys（支持去重）
    
    Args:
        db: 数据库会话
        request: 批量创建请求（包含API密钥列表）
        ua_list: UA列表（从配置中获取）
        proxy_list: 代理列表（从配置中获取）
    
    返回: (成功创建的列表, 成功数量, 失败数量)
    """
    import random
    
    success_keys = []
    success_count = 0
    fail_count = 0
    
    # 去重：获取所有待导入的key（去除重复）
    unique_keys = list(dict.fromkeys([k.strip() for k in request.api_keys if k.strip()]))
    
    # 查询数据库中已存在的key
    existing_keys_query = db.query(APIKey.api_key).filter(
        APIKey.api_key.in_(unique_keys)
    ).all()
    existing_keys_set = {row[0] for row in existing_keys_query}
    
    # 过滤掉已存在的key
    new_keys = [k for k in unique_keys if k not in existing_keys_set]
    
    # 如果有重复的key，统计失败数量
    duplicate_count = len(unique_keys) - len(new_keys)
    fail_count += duplicate_count
    
    if duplicate_count > 0:
        print(f"跳过 {duplicate_count} 个已存在的密钥")
    
    # 批量创建新的key
    for idx, api_key_str in enumerate(new_keys):
        try:
            # 随机选择UA和proxy
            ua = random.choice(ua_list) if ua_list else "Mozilla/5.0"
            proxy = random.choice(proxy_list) if proxy_list else ""
            
            api_key = APIKey(
                name=f"{request.batch_name}-{idx+1}",  # 使用批次名称 + 序号
                api_key=api_key_str,
                ua=ua,
                proxy=proxy,
                enabled=True,  # 默认启用
                balance=10.0,  # 默认余额10
                total_balance=10.0,  # 默认总额也是10
                memo=None,
                balance_last_update=datetime.now()
            )
            
            db.add(api_key)
            db.flush()  # 立即执行 SQL 但不提交事务
            success_keys.append(api_key)
            success_count += 1
            
        except Exception as e:
            # 记录失败但继续处理下一个
            fail_count += 1
            print(f"创建密钥失败: {api_key_str[:20]}..., 错误: {str(e)}")
            continue
    
    # 统一提交事务
    if success_keys:
        db.commit()
        # 刷新所有成功创建的对象
        for key in success_keys:
            db.refresh(key)
    
    return success_keys, success_count, fail_count


def get_api_key_by_id(db: Session, key_id: int) -> Optional[APIKey]:
    """根据 ID 获取 API Key"""
    return db.query(APIKey).filter(APIKey.id == key_id).first()


def update_api_key(db: Session, key_id: int, request: APIKeyUpdateRequest) -> Optional[APIKey]:
    """更新 API Key"""
    api_key = get_api_key_by_id(db, key_id)
    
    if not api_key:
        return None
    
    # 更新字段
    update_data = request.dict(exclude_unset=True)
    
    # 如果更新了余额，同时更新余额更新时间
    if 'balance' in update_data:
        update_data['balance_last_update'] = datetime.now()
    
    for key, value in update_data.items():
        setattr(api_key, key, value)
    
    api_key.update_time = datetime.now()
    
    db.commit()
    db.refresh(api_key)
    
    return api_key


def delete_api_key(db: Session, key_id: int) -> bool:
    """删除 API Key"""
    api_key = get_api_key_by_id(db, key_id)
    
    if not api_key:
        return False
    
    db.delete(api_key)
    db.commit()
    
    return True


def disable_api_key(db: Session, key_id: int, reason: str = None, error_code: str = None, auto_commit: bool = True) -> bool:
    """
    禁用 API Key（用于自动禁用被封禁的 Key）
    
    Args:
        db: 数据库会话
        key_id: Key ID
        reason: 禁用原因（可选）
        error_code: 错误代码（如：UNAUTHORIZED, RATE_LIMIT 等）
        auto_commit: 是否自动提交事务（批量操作时设为 False）
    
    Returns:
        是否成功禁用
    """
    api_key = get_api_key_by_id(db, key_id)
    
    if not api_key:
        logger.warning(f"尝试禁用不存在的 Key: id={key_id}")
        return False
    
    # 更新 Key 状态为禁用
    api_key.enabled = False
    api_key.update_time = datetime.now()
    
    # 设置错误代码
    if error_code:
        api_key.error_code = error_code
    
    # 如果有原因，添加到备注中
    if reason:
        if api_key.memo:
            api_key.memo = f"{api_key.memo}\n[自动禁用] {reason} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            api_key.memo = f"[自动禁用] {reason} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 根据参数决定是否提交
    if auto_commit:
        db.commit()
    else:
        db.flush()  # 刷新但不提交
    
    logger.warning(f"🚫 已自动禁用 Key: id={key_id}, name={api_key.name}, error_code={error_code}, reason={reason}")
    
    # 从缓存中移除
    cache_service.remove_key(key_id)
    logger.info(f"✅ 已从缓存移除 Key: id={key_id}")
    
    return True


def query_api_keys(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    name: Optional[str] = None,
    enabled: Optional[bool] = None,
    create_date: Optional[str] = None,
    min_balance: Optional[float] = None
) -> Tuple[List[APIKey], int]:
    """
    查询 API Keys
    
    Args:
        db: 数据库会话
        page: 页码
        page_size: 每页数量
        name: 密钥名称（模糊搜索）
        enabled: 是否启用
        create_date: 创建日期（格式：YYYY-MM-DD）
        min_balance: 最小余额
    
    返回: (列表, 总数)
    """
    from sqlalchemy import func, cast, Date
    
    query = db.query(APIKey)
    
    # 过滤条件
    if name:
        query = query.filter(APIKey.name.like(f"%{name}%"))
    
    if enabled is not None:
        query = query.filter(APIKey.enabled == enabled)
    
    # 按创建日期搜索（精确到天）
    if create_date:
        try:
            # 将日期字符串转换为日期对象进行比较
            from datetime import datetime
            target_date = datetime.strptime(create_date, "%Y-%m-%d").date()
            query = query.filter(cast(APIKey.create_time, Date) == target_date)
        except ValueError:
            # 日期格式错误，忽略此条件
            pass
    
    # 按余额搜索（大于等于指定值）
    if min_balance is not None:
        query = query.filter(APIKey.balance >= min_balance)
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    items = query.order_by(APIKey.create_time.desc()).offset(offset).limit(page_size).all()
    
    return items, total


# ==================== 余额更新 ====================

def update_all_keys_balance(db: Session) -> dict:
    """
    更新所有可用 Key 的余额
    
    逻辑：
    1. 获取所有可用的 Key（enabled=True）
    2. 对每个 Key，统计所有请求日志的成本总和
    3. 计算余额：balance = total_balance - sum(cost)
    4. 更新 balance 和 balance_last_update
    
    返回:
        dict: 更新统计信息
            - total_keys: 处理的 Key 总数
            - updated_keys: 成功更新的 Key 数
            - failed_keys: 更新失败的 Key 数
            - errors: 错误信息列表
    """
    logger.info("开始更新所有可用 Key 的余额...")
    
    # 统计信息
    stats = {
        'total_keys': 0,
        'updated_keys': 0,
        'failed_keys': 0,
        'errors': []
    }
    
    try:
        # 获取所有可用的 Key
        enabled_keys = db.query(APIKey).filter(APIKey.enabled == True).all()
        stats['total_keys'] = len(enabled_keys)
        
        logger.info(f"找到 {stats['total_keys']} 个可用的 Key")
        
        for key in enabled_keys:
            try:
                # 查询该 Key 的所有请求成本总和
                total_cost = db.query(func.sum(RequestLog.cost)).filter(
                    RequestLog.key_id == key.id,
                    RequestLog.status == 'success'  # 只统计成功的请求
                ).scalar()
                
                # 如果没有请求记录，total_cost 为 None
                total_cost = float(total_cost) if total_cost else 0.0
                
                # 计算新余额
                if key.total_balance is not None:
                    # 如果有总授权额度，从总额度扣减
                    new_balance = float(key.total_balance) - total_cost
                else:
                    # 如果没有总授权额度，无法计算余额
                    logger.warning(f"Key {key.name} (ID: {key.id}) 没有设置总授权额度，跳过余额更新")
                    continue
                
                # 更新余额
                old_balance = float(key.balance) if key.balance else 0.0
                key.balance = new_balance
                key.balance_last_update = datetime.now()
                key.update_time = datetime.now()
                
                logger.info(
                    f"更新 Key: {key.name} (ID: {key.id}), "
                    f"总授权: ${float(key.total_balance):.2f}, "
                    f"已消耗: ${total_cost:.4f}, "
                    f"旧余额: ${old_balance:.2f}, "
                    f"新余额: ${new_balance:.2f}"
                )
                
                stats['updated_keys'] += 1
                
            except Exception as e:
                error_msg = f"更新 Key {key.name} (ID: {key.id}) 失败: {str(e)}"
                logger.error(error_msg)
                stats['failed_keys'] += 1
                stats['errors'].append(error_msg)
        
        # 提交所有更改
        db.commit()
        
        logger.info(
            f"余额更新完成: 总计 {stats['total_keys']} 个, "
            f"成功 {stats['updated_keys']} 个, "
            f"失败 {stats['failed_keys']} 个"
        )
        
    except Exception as e:
        db.rollback()
        error_msg = f"更新余额失败: {str(e)}"
        logger.error(error_msg)
        stats['errors'].append(error_msg)
    
    return stats
