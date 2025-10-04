# AMP Server 架构与项目结构概览

## 项目定位

AMP Server 是一个以 Rust 构建的 AI 服务代理层，封装在 `amp-server` 工作区内：根 crate 提供可执行入口，`amp-server-api` 子 crate 实现全部业务逻辑。服务通过统一的代理引擎将不同上游模型接口映射到自定义的本地 API，同时内置用户及遥测模拟端点，便于前端或其他服务的快速对接与测试。

```
amp-server/
├── Cargo.toml              # 工作区声明与公共依赖
├── src/main.rs             # 可执行入口，调用库 crate 的 main
├── proxy_config.yaml       # 代理端点配置（可覆盖默认值）
├── bacon.toml              # bacon 任务配置（check/run）
├── api/                    # amp-server-api 子 crate
│   ├── Cargo.toml          # 子 crate 依赖（引用工作区依赖）
│   └── src/
│       ├── lib.rs          # 服务启动、Router 汇总、信号处理
│       ├── proxy/          # 代理系统（配置 + 服务）
│       ├── telemetry/      # 遥测事件上报端点
│       └── user/           # 用户及内部 API 模块
└── target/                 # 编译产物
```

## 启动流程

1. `src/main.rs` 仅调用 `amp_server_api::main()`；真正启动逻辑在库 crate 内。
2. `lib.rs` 中的 `start()` 使用 `#[tokio::main]` 启动运行时，流程包括：
   - 初始化 tracing（读取 `RUST_LOG` 环境变量）。
   - 读取 `HOST`、`PORT`、`AMP_API_KEY` 环境变量，并在全局 `OnceLock` 中保存密钥，供代理使用。
   - 尝试加载 `proxy_config.yaml`，失败时退回 `ProxyConfig::default()` 提供的内置端点。
   - 构建 `ProxyService` 并合并 `user::router()`、`telemetry::router()`、代理路由。
   - 绑定 TCP 监听器并启动 `axum::serve`，附带 Ctrl+C / SIGTERM 优雅退出处理。

## 核心模块拆解

### proxy 模块

- `config.rs`
  - 定义 `ProxyConfig` 与 `EndpointConfig` 结构；支持 YAML 序列化/反序列化。
  - 内置默认配置，涵盖 OpenAI、Anthropic 以及 AMP LLM Proxy 端点。
  - 提供 `load_from_file()` 与 `enabled_endpoints()` 工具方法。
- `service.rs`
  - `ProxyService::create_router()` 动态遍历启用的端点，根据 `method` 生成 GET/POST/PUT/DELETE 路由。
  - `handle_proxy_request()` 将请求转发至上游：
    - 复用 `reqwest::Client` 构建外部请求，按白名单传递或追加请求头；`llm-proxy` 端点会自动带上 `AMP_API_KEY`。
    - 根据 `ResponseType`（Sse/Stream/Json/Html）选择不同的回包处理策略：
      - SSE：逐行解析 `data:`，转换为 `axum::response::sse::Event` 事件流。
      - Stream：识别 `content-type` 是否为流式，选择透传字节流或一次性读取。
      - Json/Html：按需解析 JSON 或文本，并附加允许透出的响应头。
  - 统一的错误处理返回 `(StatusCode, String)`，方便 axum 生成 HTTP 响应。

### user 模块

- 对外路由：`/api/user`、`/api/connections`、`/api/threads/sync`、`/api/internal`。
- `get_user_info()`、`get_connections()` 返回模拟数据。
- `sync_thread()` 解析线程同步请求，按照线程 ID 返回固定结构。
- `internal.rs` 定义 `InternalRequest` 及其嵌套数据结构，`internal()` 根据 `method` 字段处理内部操作（当前仅记录上传线程请求）。

### telemetry 模块

- 暴露 `POST /api/telemetry`。请求体为事件列表（`Vec<HashMap<...>>`），响应统计发布数量，用于调试遥测上报流程。

## 配置与环境依赖

- **环境变量**：`HOST`、`PORT`、`AMP_API_KEY`、`RUST_LOG`。
- **代理配置**：
  - `proxy_config.yaml` 支持自由添加端点（路径、目标 URL、HTTP 方法、请求/响应头、是否启用、响应类型）。
  - 若缺失或解析失败则回退到 `ProxyConfig::default()` 内置模板。
- **依赖管理**：
  - 工作区层面依赖：Tokio 异步运行时、Axum/Tower Web 框架、Reqwest HTTP 客户端、Serde 系列、Tracing 观测、ULID/Chrono 等工具库。
  - `bacon.toml` 配置 `cargo check` 与 `cargo run` 监视任务。
  - `mise.toml`（空配置）可配合 mise 工具管理语言版本。

## 请求流转示意

1. 客户端访问 `/api/...`。
2. axum Router 将路由分发至 `user`、`telemetry` 或代理路由。
3. 代理路由通过 `ProxyService` 将请求构造成外部 HTTP 调用：
   - 转发指定请求头、附加自定义头。
   - 对 `llm-proxy` 自动注入 `Bearer AMP_API_KEY`。
4. 上游响应按类型转换并返回，同时仅透传列入白名单的响应头，确保安全与可控性。

## 开发与扩展建议

- **新增代理端点**：编辑 `proxy_config.yaml`；如需自定义默认配置，可修改 `ProxyConfig::default()`。
- **增加业务模块**：在 `api/src` 下新增模块并在 `lib.rs` 中 `merge` 对应 Router。
- **可观测性**：已经集成 `tracing` + `TraceLayer`，可结合环境变量调整日志级别。
- **部署**：使用 `cargo build --release` 生成可执行文件；部署时确保 `proxy_config.yaml` 与环境变量正确配置。

## 相关资源

- `README.md`：快速入门与配置说明。
- `proxy_config.yaml`：示例端点配置，可作为新增端点模板。
- `LICENSE`：MIT 协议。



