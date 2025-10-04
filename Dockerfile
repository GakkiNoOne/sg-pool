# ============================================
# 阶段 1: 构建前端
# ============================================
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

# 复制前端依赖文件
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# 安装 pnpm 和依赖
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# 复制前端源码
COPY frontend/ ./

# 构建前端（hash 路由模式）
RUN pnpm build

# ============================================
# 阶段 2: 构建后端并整合前端
# ============================================
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装 UV 包管理器并安装 Python 依赖
RUN pip install uv && \
    uv pip install --system -r pyproject.toml

# 复制后端项目文件
COPY src/ ./src/

# 复制前端构建产物
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# 创建必要的目录
RUN mkdir -p data logs

# 暴露端口
EXPOSE 6777

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:6777/health || exit 1

# 启动命令 - 使用 uvicorn 直接启动 FastAPI 应用
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "6777"]

