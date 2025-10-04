"""日志记录服务 - 异步记录请求日志"""

import time
from concurrent.futures import ThreadPoolExecutor
from entity.context import RequestContext
from entity.databases.database import SessionLocal
from service.databases import request_log_service
from utils.logger import logger


# 全局线程池（用于异步任务）
_thread_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix="log-worker")


def _async_save_log(log_data: dict):
    """
    异步保存日志到数据库（在独立线程中执行）
    
    Args:
        log_data: 日志数据字典
    """
    # 在独立线程中创建新的数据库 session
    db = SessionLocal()
    try:
        request_log_service.create_log_from_data(db, log_data)
        # 注意：mapper 层的 insert_request_log 已经调用了 db.commit()，这里不需要再次提交
        logger.debug("异步日志保存完成")
        
    except Exception as e:
        db.rollback()
        logger.error(f"异步保存日志失败: {str(e)}")
        logger.exception(e)
    finally:
        db.close()


def log(context: RequestContext):
    """
    记录请求日志（异步执行）
    
    Args:
        context: 请求上下文
    
    注意：
    - 日志会在后台线程中异步保存到数据库
    - 不会阻塞主请求的响应
    - 如果日志保存失败，不会影响请求响应
    """
    try:
        # 从 context 构建日志数据（在主线程中完成）
        log_data = request_log_service.build_log_data_from_context(context)
        
        # 提交到线程池异步执行
        _thread_pool.submit(_async_save_log, log_data)
        logger.debug("日志任务已提交到异步队列")
        
    except Exception as e:
        logger.error(f"提交日志任务失败: {str(e)}")


def shutdown():
    """
    关闭线程池（应用退出时调用）
    """
    logger.info("正在关闭日志线程池...")
    _thread_pool.shutdown(wait=True)
    logger.info("日志线程池已关闭")

