# AMP Pool 项目文档

> 最后更新：2025-10-02  
> 版本：v0.1.0

---

## 📋 目录

1. [项目概述](#项目概述)
2. [快速开始](#快速开始)
3. [项目结构](#项目结构)
4. [数据库设计](#数据库设计)
5. [开发指南](#开发指南)
6. [API 接口](#api-接口)
7. [部署说明](#部署说明)

---

## 项目概述

AMP Pool 是一个 AI 模型池管理服务，可以：

- 📦 **多 Key 管理**：通过界面配置多个 API Key（OpenAI/Anthropic/AMP）
- 🔄 **统一代理**：对外提供统一的 OpenAI 和 Anthropic 格式接口
- 💰 **余额监控**：实时查看每个 Key 的余额使用情况
- 📊 **使用统计**：模型使用、Token 消耗、成本分析等统计信息

### 技术栈

**后端**：
- Python 3.11+
- FastAPI（Web 框架）
- SQLAlchemy 2.0（ORM）
- SQLite（数据库）
- HTTPX（HTTP 客户端）

**前端**：
- Umi 4（React 框架）
- TypeScript
- Ant Design

---

## 快速开始

### 1. 安装依赖

```bash
cd amp-pool
uv sync
```

### 2. 初始化数据库

```bash
PYTHONPATH=src python scripts/init_db.py
```

### 3. 启动服务

```bash
# 方式1: 使用启动脚本（推荐）
python run.py

# 方式2: 使用 uvicorn
cd src
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问服务

- API: http://localhost:8000
- 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

---

## 项目结构

```
amp-pool/
├── data/                       # 数据目录
│   └── amp_pool.db            # SQLite 数据库
│
├── docs/                       # 文档目录
│   ├── README.md              # 本文档
│   ├── backend-design.md      # 后端架构设计
│   └── amp-server-architecture.md  # amp-server 参考文档
│
├── frontend/                   # 前端项目（Umi）
│   ├── src/
│   ├── package.json
│   └── tsconfig.json
│
├── scripts/                    # 脚本目录
│   ├── init_db.py             # 数据库初始化
│   └── test_models.py         # 模型测试
│
├── src/                        # 后端源码
│   ├── app.py                 # FastAPI 应用入口
│   │
│   ├── configs/               # 配置模块
│   │   └── config.py          # 应用配置 + 数据库初始化
│   │
│   ├── controller/            # 控制器层（路由）
│   │   └── api_controller.py
│   │
│   ├── entity/                # 实体层
│   │   └── databases/         # 数据库模型
│   │       ├── database.py    # 引擎与会话
│   │       ├── base_model.py  # 基础模型
│   │       ├── api_key.py     # API 密钥表
│   │       ├── request_log.py # 请求日志表
│   │       ├── request_stats.py # 统计表
│   │       └── config.py      # 配置表
│   │
│   └── service/               # 服务层（业务逻辑）
│
├── pyproject.toml             # 项目配置
├── uv.lock                    # 依赖锁定
└── run.py                     # 启动脚本
```

### 模块职责

| 模块 | 职责 | 状态 |
|------|------|------|
| `configs/` | 应用配置、数据库初始化 | ✅ 完成 |
| `entity/databases/` | 数据库模型定义 | ✅ 完成 |
| `controller/` | API 路由控制器 | 🚧 待开发 |
| `service/` | 业务逻辑服务 | 🚧 待开发 |

---

## 数据库设计

### 表结构规范

所有表统一包含 3 个固定字段：
- `id`: 主键（自增）
- `create_time`: 创建时间
- `update_time`: 更新时间

### 1. api_keys - API 密钥管理表

```sql
CREATE TABLE api_keys (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    create_time             DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time             DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    name                    VARCHAR(100) NOT NULL,      -- 密钥名称
    api_key                 VARCHAR(256) NOT NULL,      -- API密钥
    ua                      VARCHAR(256) NOT NULL,      -- 固定UA
    proxy_ip                VARCHAR(256) NOT NULL,      -- 代理IP
    enabled                 BOOLEAN DEFAULT TRUE,       -- 是否启用
    balance                 DECIMAL(10, 2),             -- 当前余额
    total_balance           DECIMAL(10, 2),             -- 总额度
    balance_last_update     DATETIME,                   -- 余额更新时间
    memo                    TEXT                        -- 备注
);
```

### 2. api_request_log - 请求日志表

```sql
CREATE TABLE api_request_log (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    create_time             DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time             DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    key_id                  INTEGER NOT NULL,           -- API Key ID
    model                   VARCHAR(100),               -- 模型名称
    input_tokens            INTEGER DEFAULT 0,          -- 输入token
    output_tokens           INTEGER DEFAULT 0,          -- 输出token
    total_tokens            INTEGER DEFAULT 0,          -- 总token
    cost                    DECIMAL(10, 6) DEFAULT 0,   -- 成本
    latency_ms              INTEGER,                    -- 延迟(ms)
    status                  VARCHAR(20) NOT NULL,       -- success/error
    http_status_code        INTEGER,                    -- HTTP状态码
    error_type              VARCHAR(100),               -- 错误类型
    error_message           TEXT                        -- 错误信息
);
```

### 3. api_request_stats - 统计汇总表

```sql
CREATE TABLE api_request_stats (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    create_time             DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time             DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    stat_date               DATE NOT NULL,              -- 统计日期
    stat_hour               INTEGER,                    -- 统计小时(0-23)，NULL=全天
    key_id                  INTEGER,                    -- Key ID，NULL=全局
    model                   VARCHAR(100),               -- 模型，NULL=全部
    provider                VARCHAR(50),                -- 提供商，NULL=全部
    
    request_count           INTEGER DEFAULT 0,          -- 总请求数
    success_count           INTEGER DEFAULT 0,          -- 成功数
    error_count             INTEGER DEFAULT 0,          -- 失败数
    
    total_input_tokens      BIGINT DEFAULT 0,           -- 总输入token
    total_output_tokens     BIGINT DEFAULT 0,           -- 总输出token
    total_tokens            BIGINT DEFAULT 0,           -- 总token
    total_cost              DECIMAL(10, 4) DEFAULT 0,   -- 总成本
    
    avg_latency_ms          INTEGER,                    -- 平均延迟
    max_latency_ms          INTEGER,                    -- 最大延迟
    min_latency_ms          INTEGER                     -- 最小延迟
);
```

### 4. config - 系统配置表

```sql
CREATE TABLE config (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    create_time             DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time             DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    key                     VARCHAR(100) NOT NULL UNIQUE,  -- 配置键
    value                   TEXT,                           -- 配置值(JSON)
    memo                    TEXT                            -- 说明
);
```

---

## 开发指南

### 配置管理

```python
from configs.config import settings, init_database, drop_database

# 访问配置
print(settings.HOST)
print(settings.PORT)
print(settings.DATABASE_PATH)

# 初始化数据库
init_database()
```

### 数据库操作

```python
from entity.databases.database import SessionLocal, get_db
from entity.databases import APIKey, RequestLog, RequestStats, Config

# 方式1: 直接使用 Session
db = SessionLocal()
try:
    keys = db.query(APIKey).filter(APIKey.enabled == True).all()
    for key in keys:
        print(key.to_dict())
finally:
    db.close()

# 方式2: FastAPI 依赖注入
from fastapi import Depends
from sqlalchemy.orm import Session

@app.get("/keys")
async def list_keys(db: Session = Depends(get_db)):
    return db.query(APIKey).all()
```

### 添加新路由

在 `controller/api_controller.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from entity.databases.database import get_db
from entity.databases import APIKey

router = APIRouter(prefix="/api", tags=["API"])

@router.get("/keys")
async def list_keys(db: Session = Depends(get_db)):
    """获取所有密钥"""
    keys = db.query(APIKey).filter(APIKey.enabled == True).all()
    return [key.to_dict() for key in keys]

@router.post("/keys")
async def create_key(name: str, api_key: str, db: Session = Depends(get_db)):
    """创建密钥"""
    key = APIKey(
        name=name,
        api_key=api_key,
        ua="default-ua",
        proxy_ip="",
        enabled=True
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return key.to_dict()
```

在 `app.py` 中注册路由：

```python
from controller.api_controller import router as api_router

app.include_router(api_router)
```

### 环境变量

创建 `.env` 文件：

```bash
# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DB_ECHO=false  # 设为 true 查看 SQL 语句

# API 密钥
AMP_API_KEY=your_api_key_here
```

---

## API 接口

### 当前接口

#### 基础接口
- `GET /` - 欢迎页面
- `GET /health` - 健康检查
- `GET /docs` - API 文档（Swagger UI）

### 计划接口

#### Key 管理
- `GET /api/keys` - 获取所有密钥
- `POST /api/keys` - 创建密钥
- `GET /api/keys/{id}` - 获取单个密钥
- `PUT /api/keys/{id}` - 更新密钥
- `DELETE /api/keys/{id}` - 删除密钥
- `GET /api/keys/{id}/balance` - 查询余额

#### 代理接口
- `POST /v1/chat/completions` - OpenAI 格式代理
- `POST /v1/messages` - Anthropic 格式代理

#### 统计接口
- `GET /api/statistics/overview` - 总体统计
- `GET /api/statistics/keys` - 按 Key 统计
- `GET /api/statistics/models` - 按模型统计
- `GET /api/statistics/timeline` - 时间序列统计

#### 日志接口
- `GET /api/requests` - 请求日志列表
- `GET /api/requests/{id}` - 请求详情

---

## 部署说明

### 开发环境

```bash
# 安装依赖
uv sync

# 初始化数据库
PYTHONPATH=src python scripts/init_db.py

# 启动服务（热重载）
python run.py
```

### 生产环境

```bash
# 安装依赖
uv sync --no-dev

# 设置环境变量
export HOST=0.0.0.0
export PORT=8000
export DB_ECHO=false

# 启动服务
cd src
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker 部署（待实现）

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync --no-dev
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 开发计划

### ✅ 已完成

- [x] 项目结构设计
- [x] 数据库模型定义（4张表）
- [x] 配置管理系统
- [x] FastAPI 应用入口
- [x] 数据库初始化脚本

### 🚧 进行中

- [ ] API Key 管理接口
- [ ] 代理转发服务
- [ ] 余额查询服务

### 📋 待开发

- [ ] 统计分析接口
- [ ] 请求日志查询
- [ ] 前端管理界面
- [ ] 用户认证系统
- [ ] 告警通知功能

---

## 常见问题

### Q: 如何查看 SQL 语句？
A: 设置环境变量 `DB_ECHO=true` 或在代码中修改 `settings.DB_ECHO = True`

### Q: 数据库文件在哪里？
A: `amp-pool/data/amp_pool.db`

### Q: 如何重置数据库？
```bash
rm data/amp_pool.db
PYTHONPATH=src python scripts/init_db.py
```

### Q: 导入路径错误怎么办？
A: 确保使用 `configs.config` 而不是 `config.config`

---

## 参考文档

- [后端架构设计](./backend-design.md) - 详细的架构设计方案
- [amp-server 架构](./amp-server-architecture.md) - Rust 版参考实现

---

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 许可证

MIT License

