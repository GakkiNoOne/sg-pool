"""FastAPI 主应用入口"""

from contextlib import asynccontextmanager
from pathlib import Path

# 加载环境变量（必须在导入 settings 之前）
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# 加载项目根目录下的 .env 文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from configs.config import init_database, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    init_database()
    print(f"✅ 数据库已连接: {settings.DATABASE_PATH}")
    
    # 加载系统配置和全局配置
    from configs.global_config import global_config
    from entity.databases.database import SessionLocal
    from service.databases.config_service import get_system_config
    
    db = SessionLocal()
    try:
        # 1. 加载系统配置（API_PREFIX, API_SECRET, ADMIN_USERNAME 等）
        system_config = get_system_config(db)
        if system_config:
            settings.load_from_database(system_config)
            print("✅ 系统配置已从数据库加载")
        else:
            print("⚠️  数据库中未找到系统配置，使用环境变量")
        
        # 2. 加载全局配置
        global_config.load_from_db(db)
        print("✅ 全局配置已加载")
    finally:
        db.close()
    
    # 启动统计任务
    from service.stats_task import start_stats_task, stop_stats_task
    await start_stats_task()
    print("✅ 统计任务已启动")
    
    yield
    
    # 关闭时执行
    await stop_stats_task()
    print("👋 应用关闭")


app = FastAPI(
    title="AMP Pool API",
    description="AI Model Pool Service",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:8001", 
        "http://localhost:8002",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
    ],  # 开发环境允许的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to AMP Pool API",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 注册路由
from controller.api_controller import router as api_router
from controller.web import key_router, config_router, request_log_router, dashboard_router, auth_router

# API 路由（支持动态前缀）
app.include_router(api_router, prefix=settings.API_PREFIX)

# 认证路由（无需鉴权）
app.include_router(auth_router)

# Web 管理路由（需要 JWT 鉴权，已在 router 中配置）
# 注册两次：一次带 ADMIN_PREFIX，一次不带（兼容前端静态文件模式）
app.include_router(key_router, prefix=settings.ADMIN_PREFIX)
app.include_router(config_router, prefix=settings.ADMIN_PREFIX)
app.include_router(request_log_router, prefix=settings.ADMIN_PREFIX)
app.include_router(dashboard_router, prefix=settings.ADMIN_PREFIX)

# 为前端静态文件模式提供不带前缀的 API 路由
app.include_router(key_router)
app.include_router(config_router)
app.include_router(request_log_router)
app.include_router(dashboard_router)


# 前端静态文件服务（如果存在 frontend/dist 目录）
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():

    # 管理后台入口：返回 index.html（支持 hash 路由）
    # 注意：这个路由必须在静态文件路由之前注册
    @app.get(f"{settings.ADMIN_PREFIX}", response_class=FileResponse)
    @app.get(f"{settings.ADMIN_PREFIX}/", response_class=FileResponse)
    async def serve_admin_root():
        """返回管理后台首页"""
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return index_file
        # 如果前端未构建，返回错误信息
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "error": "Frontend not built",
                "message": "Please build frontend first: cd frontend && pnpm build"
            }
        )
    
    # 服务所有前端静态文件（JS、CSS等）
    # 注意：这个通配符路由应该最后注册，避免覆盖其他路由
    @app.get("/{file_path:path}", response_class=FileResponse)
    async def serve_static_files(file_path: str):
        """服务前端静态文件"""
        # 只处理静态资源文件
        if file_path.endswith(('.js', '.css', '.map', '.ico', '.png', '.jpg', '.svg', '.woff', '.woff2', '.ttf', '.eot')):
            file_full_path = frontend_dist / file_path
            if file_full_path.exists() and file_full_path.is_file():
                return file_full_path
        
        # 不是静态资源，返回 404
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=6777,
        reload=True,
    )
