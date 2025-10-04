"""统计任务 - 定时异步执行统计"""

import asyncio
from datetime import date, datetime
from typing import Optional

from entity.databases.database import SessionLocal
from service.databases import stats_service, key_service
from utils.logger import logger


class StatsTask:
    """统计任务类 - 负责定期执行统计任务"""
    
    def __init__(self, interval_minutes: int = 5):
        """
        初始化统计任务
        
        Args:
            interval_minutes: 执行间隔（分钟），默认5分钟
        """
        self.interval_minutes = interval_minutes
        self._task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self):
        """启动定时任务"""
        if self._running:
            logger.warning("统计任务已经在运行中")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"统计任务已启动，执行间隔: {self.interval_minutes}分钟")
    
    async def stop(self):
        """停止定时任务"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("统计任务已停止")
    
    async def _run_loop(self):
        """任务循环"""
        while self._running:
            try:
                # 执行统计
                await self._execute_stats()
                
                # 等待下一次执行
                await asyncio.sleep(self.interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"统计任务执行失败: {str(e)}")
                logger.exception(e)
                # 出错后等待一段时间再重试
                await asyncio.sleep(60)
    
    async def _execute_stats(self):
        """执行统计任务"""
        db = SessionLocal()
        try:
            now = datetime.now()
            today = date.today()
            current_hour = now.hour
            
            logger.info(f"开始执行统计任务: {now}")
            
            # 1. 统计今日全天数据
            logger.info("统计今日全天数据...")
            stats_service.calculate_and_save_stats(db, today, target_hour=None)
            
            # 2. 统计当前小时数据
            logger.info(f"统计当前小时数据: {current_hour}时...")
            stats_service.calculate_and_save_stats(db, today, target_hour=current_hour)
            
            # 3. 如果当前小时大于0，统计上一小时数据（防止数据遗漏）
            if current_hour > 0:
                logger.info(f"统计上一小时数据: {current_hour - 1}时...")
                stats_service.calculate_and_save_stats(db, today, target_hour=current_hour - 1)
            
            # 4. 更新所有可用 Key 的余额
            logger.info("更新所有可用 Key 的余额...")
            balance_stats = key_service.update_all_keys_balance(db)
            logger.info(
                f"余额更新完成: 总计 {balance_stats['total_keys']} 个 Key, "
                f"成功 {balance_stats['updated_keys']} 个, "
                f"失败 {balance_stats['failed_keys']} 个"
            )
            
            logger.info("统计任务执行完成")
            
        except Exception as e:
            logger.error(f"统计任务执行失败: {str(e)}")
            logger.exception(e)
        finally:
            db.close()
    
    async def execute_now(self):
        """立即执行一次统计（用于手动触发）"""
        logger.info("手动触发统计任务")
        await self._execute_stats()


# 全局单例
_stats_task: Optional[StatsTask] = None


def get_stats_task() -> StatsTask:
    """获取全局统计任务实例"""
    global _stats_task
    if _stats_task is None:
        _stats_task = StatsTask(interval_minutes=5)
    return _stats_task


async def start_stats_task():
    """启动统计任务（在应用启动时调用）"""
    task = get_stats_task()
    await task.start()


async def stop_stats_task():
    """停止统计任务（在应用关闭时调用）"""
    task = get_stats_task()
    await task.stop()


async def trigger_stats_now():
    """立即触发一次统计（用于手动触发）"""
    task = get_stats_task()
    await task.execute_now()

