# SG-Pool

## 🚀 快速部署

### 1. 克隆项目

```bash
git clone https://github.com/GakkiNoOne/sg-pool.git
cd sg-pool
```

### 2. 配置环境变量

```bash
cp .env.example .env
vim .env
```

编辑 `.env` 文件：

```env
# API 配置
API_PREFIX=/your-api-prefix                       # API 路径前缀（支持格式：x、/x、/x/）
API_SECRET=your_secret_key           # API 访问密钥

# 管理后台配置
ADMIN_PREFIX=/admin                  # 管理后台路径前缀（支持格式：admin、/admin、/admin/）
ADMIN_USERNAME=admin                 # 管理后台用户名
ADMIN_PASSWORD=admin123              # 管理后台密码

# JWT 密钥
JWT_SECRET_KEY=your_jwt_secret_key   # Token 签名密钥 https://jwtsecrets.com/ 自己去生成

# 服务配置（可选）
HOST=0.0.0.0
PORT=6777
DATA_DIR=./data
LOGS_DIR=./logs
```


### 3. Docker Compose 配置

项目自带的 `docker-compose.yml` 配置如下：

```yaml
version: '3.8'

services:
  # SG-Pool 后端服务
  sg-pool:
    # 使用 GitHub Container Registry 构建的镜像
    image: ghcr.io/gakkinoone/sg-pool:latest
    container_name: sg-pool
    ports:
      - "6777:6777"
    volumes:
      - ${DATA_DIR:-./data}:/app/data
      - ${LOGS_DIR:-./logs}:/app/logs
    environment:
      # 从 .env 文件读取环境变量
      - API_PREFIX=${API_PREFIX:-/{your_api_prefix}}
      - API_SECRET=${API_SECRET:-your_secret_key}
      - ADMIN_PREFIX=${ADMIN_PREFIX:-/admin}
      - ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-your_jwt_secret_key}
      - HOST=${HOST:-0.0.0.0}
      - PORT=${PORT:-6777}
    env_file:
      - .env
    restart: unless-stopped
    networks:
      - sg-pool-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6777/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

networks:
  sg-pool-network:
    driver: bridge
```

**配置说明：**
- 镜像源：`ghcr.io/gakkinoone/sg-pool:latest`（GitHub Actions 自动构建）
- 支持平台：`linux/amd64`、`linux/arm64`
- 服务会自动从 `.env` 文件读取配置

**如需本地构建**，请修改 `docker-compose.yml`：
```yaml
services:
  sg-pool:
    build:
      context: .
      dockerfile: Dockerfile
    # 注释掉 image 行
    # image: ghcr.io/gakkinoone/sg-pool:latest
```

### 4. 启动服务

```bash
docker-compose up -d
```

### 5. 访问服务

- **管理后台**: http://localhost:6777/admin
- **健康检查**: http://localhost:6777/health
- **API 文档**: http://localhost:6777/docs

## 📖 使用

### 1. 登录管理后台

访问 http://localhost:6777/admin，使用 `.env` 中配置的账号登录。

### 2. 导入 API Keys

在「Key 管理」页面批量导入 API Keys。

### 3. 调用 API

#### 获取支持的模型列表

```bash
curl http://localhost:6777/{your_api_prefix}/v1/models \
  -H "Authorization: Bearer YOUR_API_SECRET"
```

#### OpenAI 格式 - Chat Completions

```bash
curl -X POST http://localhost:6777/{your_api_prefix}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_SECRET" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

#### Anthropic 原生格式 - Messages API

```bash
curl -X POST http://localhost:6777/{your_api_prefix}/v1/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_SECRET" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "max_tokens": 1024
  }'
```

**注意**：将 `YOUR_API_SECRET` 替换为你在 `.env` 中配置的 `API_SECRET`。

## 🔧 停止服务

```bash
docker-compose down
```

## 📝 许可证

MIT License
