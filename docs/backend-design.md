# AMP Pool 后端架构设计

## 项目目标

构建一个 Python 项目，可以通过界面配置多个 API Key（支持 OpenAI/Anthropic/AMP 等提供商），对外提供统一的 OpenAI 格式和 Anthropic 格式的对话接口，并在前端页面展示每个 Key 的余额使用、模型使用情况及统计信息。

---

## 核心模块划分

### 1️⃣ **API Key 管理模块** (`api_keys`)

**职责**：
- API Key 的增删改查（支持多个 Key）
- Key 的启用/禁用状态管理
- Key 的标签/备注（方便区分不同 Key 用途）
- Key 的优先级/权重配置（用于负载均衡或轮询策略）

**数据字段参考**：
```
- id: 主键
- name: Key 名称/别名
- api_key: 实际的密钥
- provider: 提供商（openai/anthropic/amp）
- enabled: 是否启用
- priority: 优先级
- tags: 标签
- created_at/updated_at
```

---

### 2️⃣ **代理服务模块** (`proxy`)

**职责**：
- 统一对外暴露 OpenAI 和 Anthropic 格式接口
- 请求转发与响应类型处理（JSON/Stream/SSE）
- 请求头管理（参考 amp-server 的 forward_headers 机制）
- Key 的选择策略（轮询/随机/权重/健康度）

**子模块**：
- `router.py`: 定义 `/v1/chat/completions`、`/v1/messages` 等端点
- `forwarder.py`: 实际的 HTTP 转发逻辑（使用 httpx）
- `key_selector.py`: Key 选择策略（轮询、加权、故障转移）
- `stream_handler.py`: 流式响应处理（SSE/Stream）

---

### 3️⃣ **请求追踪模块** (`tracker`)

**职责**：
- 记录每次代理请求的详细信息
- 实时更新 Key 的使用统计
- 支持异步写入（避免阻塞请求）

**记录字段**：
```
- request_id: 请求唯一标识
- api_key_id: 使用的 Key ID
- model: 使用的模型
- provider: 提供商
- input_tokens/output_tokens: Token 消耗
- cost: 成本（可根据模型定价计算）
- latency: 延迟
- status: 成功/失败
- error_message: 错误信息
- created_at: 请求时间
```

---

### 4️⃣ **余额查询模块** (`balance`)

**职责**：
- 定期或按需查询各 Key 的剩余额度
- 缓存余额信息（避免频繁调用上游）
- 支持手动刷新余额

**实现方式**：
- OpenAI: 调用官方 billing API（如果有权限）
- Anthropic: 类似方式
- AMP: 调用对应接口
- 定时任务（Celery/APScheduler）+ 缓存（Redis/内存）

---

### 5️⃣ **统计分析模块** (`analytics`)

**职责**：
- 基于 `tracker` 数据聚合统计指标
- 按时间维度聚合（小时/天/周/月）
- 按 Key、模型、提供商等维度统计

**统计指标**：
```
- 请求总数/成功率
- Token 消耗（输入/输出）
- 成本统计
- 平均延迟
- 模型使用分布
- Key 使用频次排行
- 错误率/错误类型分布
```

---

### 6️⃣ **配置管理模块** (`config`)

**职责**：
- 系统全局配置（端口、日志级别等）
- 代理配置（类似 amp-server 的 proxy_config.yaml）
- 支持动态配置更新（可选）

**配置项参考**：
```yaml
proxy:
  timeout: 60
  retry: 3
  default_provider: openai

tracking:
  enable: true
  async_write: true

balance:
  refresh_interval: 3600  # 1小时刷新一次
  enable_cache: true
```

---

### 7️⃣ **认证与权限模块** (`auth`)

**职责**：
- 前端用户登录/登出
- API 访问鉴权（可选：为代理接口提供 API Token）
- 基于角色的权限控制（如果需要多租户）

**可选设计**：
- 简单模式：单用户，只保护管理后台
- 复杂模式：多用户，每个用户管理自己的 Key

---

### 8️⃣ **通知告警模块** (`alerts`，可选）

**职责**：
- Key 余额低于阈值时告警
- 请求失败率超过阈值时告警
- 支持邮件/Webhook/企业微信等通知方式

---

## 模块依赖关系

```
┌─────────────────────────────────────────┐
│           FastAPI 主应用 (main.py)       │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    │          │          │          │
┌───▼───┐  ┌──▼──┐  ┌────▼────┐  ┌─▼──────┐
│ Proxy │  │Auth │  │API Keys │  │Analytics│
│       │  │     │  │         │  │         │
└───┬───┘  └─────┘  └────┬────┘  └─┬───────┘
    │                     │         │
    │            ┌────────▼─────────▼────┐
    └────────────►     Tracker 追踪      │
                 └──────────┬────────────┘
                            │
                      ┌─────▼──────┐
                      │  Balance   │
                      │  余额查询  │
                      └────────────┘
```

---

## 数据存储设计建议

### SQLite/PostgreSQL（结构化数据）
- `api_keys` 表：Key 管理
- `request_logs` 表：请求日志
- `statistics` 表：预聚合的统计数据
- `users` 表（可选）：用户认证

### Redis（可选，缓存层）
- 余额缓存：`balance:{key_id}`
- 统计缓存：`stats:daily:{date}`
- Key 轮询状态：`key_selector:round_robin`

---

## 技术栈建议

### Web 框架
- **FastAPI**: 主框架
- **Pydantic**: 数据验证

### HTTP 客户端
- **httpx**: 异步 HTTP 客户端（替代 requests）

### 数据库
- **SQLAlchemy 2.0**: ORM
- **Alembic**: 数据库迁移
- **SQLite**（开发）/ **PostgreSQL**（生产）

### 任务调度
- **APScheduler**: 定时任务（余额刷新）

### 日志与监控
- **structlog/loguru**: 结构化日志
- **prometheus-client**: Metrics 导出（可选）

### 缓存
- **redis-py**: Redis 客户端（可选）

---

## API 路由规划

### 代理接口（对外）
```
POST /v1/chat/completions          # OpenAI 格式
POST /v1/messages                  # Anthropic 格式
```

### 管理接口（内部）
```
# Key 管理
GET    /api/keys                   # 获取 Key 列表
POST   /api/keys                   # 添加 Key
PUT    /api/keys/{id}              # 更新 Key
DELETE /api/keys/{id}              # 删除 Key
GET    /api/keys/{id}/balance      # 查询 Key 余额

# 统计分析
GET  /api/statistics/overview      # 总体统计
GET  /api/statistics/keys          # 按 Key 统计
GET  /api/statistics/models        # 按模型统计
GET  /api/statistics/timeline      # 时间序列统计

# 请求日志
GET  /api/requests                 # 请求日志列表
GET  /api/requests/{id}            # 请求详情

# 系统
GET  /health                       # 健康检查
```

---

## 设计优点

- ✅ 模块职责清晰，易于扩展
- ✅ 核心代理逻辑与统计、管理解耦
- ✅ 支持后续添加更多提供商
- ✅ 统计数据可灵活聚合与展示
- ✅ 参考 amp-server 的成熟设计，降低实现风险

---

## 与 amp-server 的对比

| 功能模块 | amp-server (Rust) | amp-pool (Python) |
|---------|-------------------|-------------------|
| 代理转发 | ✅ 配置化代理 | ✅ 继承设计理念 |
| 用户模块 | ✅ Mock 数据 | ⚠️ 可选实现 |
| 遥测上报 | ✅ 简单记录 | ✅ 扩展为完整追踪 |
| Key 管理 | ❌ 无 | ✅ 核心功能 |
| 余额查询 | ❌ 无 | ✅ 核心功能 |
| 统计分析 | ❌ 无 | ✅ 核心功能 |
| 可视化界面 | ❌ 无 | ✅ 前端支持 |

---

## 下一步计划

1. 确定最小可行版本（MVP）功能范围
2. 设计数据库表结构
3. 实现 API Key 管理模块
4. 实现代理转发核心逻辑
5. 实现请求追踪与统计
6. 前端界面开发
7. 部署与测试

