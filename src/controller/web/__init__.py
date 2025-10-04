"""Web 管理接口"""

from .key_controller import router as key_router
from .config_controller import router as config_router
from .request_log_controller import router as request_log_router
from .dashboard_controller import router as dashboard_router
from .auth_controller import router as auth_router

__all__ = ['key_router', 'config_router', 'request_log_router', 'dashboard_router', 'auth_router']

