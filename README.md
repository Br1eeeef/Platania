# Platania

Platania 是面向封闭付费会员的“A 股量化研究终端 + AI 策略工坊 + 策略信息流社区”。第一阶段支持 A 股前复权日线、技术指标、三套策略与考虑中国市场约束的历史回测；没有外部账号或网络时使用固定种子的明确标记演示数据。

> 仅供量化研究与历史回测，不构成投资建议。历史表现不代表未来收益。

## 已实现

- AKShare 主数据源、BaoStock 回退、统一 Provider、超时/重试/限频、Parquet 缓存和增量更新
- 日 K / 周 K、成交量、MA5/20/60/120、EMA、MACD、RSI、布林带、ATR、缩放和信号标记
- 趋势动量、放量突破、均值回归三套独立策略
- 次根 K 线执行、T+1、整手、停牌、涨跌停、佣金、印花税、滑点、仓位限制和基准回测
- DeepSeek 受约束 `StrategySpec`；无 Key 时为 Mock；永不执行模型返回的任意 Python
- Supabase Auth、RLS、会员、用量、自选、策略/回测/信息流表结构
- 封闭会员流程和管理员后台：邀请、续费、暂停、恢复、封禁、额度、CSV 和审计日志
- React/TypeScript/Vite 响应式终端，手机端底部导航
- Nginx、systemd、定时采集、原子发布、健康检查与回滚配置

## 架构与目录

```text
web/        React + TypeScript，生产输出 web/dist
api/        FastAPI、数据 Provider、指标、策略、回测、AI 和会员服务
tests/      确定性后端与 API 测试
supabase/   PostgreSQL migration 与 RLS
data/       演示数据和被 Git 忽略的本地缓存
scripts/    定时行情刷新
deploy/     Nginx、systemd、日志轮转、发布与回滚
docs/       API、数据库、策略、数据源和部署说明
```

用户请求只读平台缓存，不会在打开页面时直接请求 AKShare。定时任务负责采集、完整性检查、保存缓存和后续计算。

## 本地环境

- Python 3.12（3.11+ 应可用）
- Node.js 20+
- pnpm 11+

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --cache-dir .pip-cache -r api\requirements-dev.txt
pnpm --dir web install --store-dir ..\.pnpm-store
Copy-Item .env.example .env
Copy-Item web\.env.example web\.env.local
```

`.env` 和 `web/.env.local` 已被 Git 忽略。Demo 模式不需要填写任何 Key。

## 启动

终端一：

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.app.main:app --host 127.0.0.1 --port 8010 --reload
```

终端二：

```powershell
pnpm --dir web dev
```

- 前端开发地址：`http://127.0.0.1:5173`
- FastAPI 与生产静态页：`http://127.0.0.1:8010`
- OpenAPI：`http://127.0.0.1:8010/docs`

构建过 `web/dist` 后，FastAPI 会直接托管前端，可只启动 API。

## 行情刷新

全 A 股目录每日同步一次；分钟 K 线（1/5/15/30/60 分钟）仅对已查看或运营配置的标的按需刷新并缓存，默认 TTL 为 90 秒。可手动执行：

```powershell
.\.venv\Scripts\python.exe scripts\refresh_market.py --catalog
.\.venv\Scripts\python.exe scripts\refresh_market.py --symbol 600519.SH --interval-kind 5m
```

根目录被忽略的 `.env` 可调整 `PLATANIA_REALTIME_CACHE_TTL_SECONDS`、`PLATANIA_REALTIME_DEFAULT_INTERVAL` 和 `PLATANIA_ON_DEMAND_LIVE_REFRESH`。AKShare 用于本地真实数据演示，数据来源、更新时间与真实/演示状态会在 API 和页面上清楚标识；其公开聚合源不代表已获得收费产品的商业再分发授权。

```powershell
.\.venv\Scripts\python.exe scripts\refresh_market.py
.\.venv\Scripts\python.exe scripts\refresh_market.py --demo
```

默认优先 AKShare、失败后 BaoStock、最后确定性 Demo；`--demo` 强制离线演示数据。生产环境由 `platania-data.timer` 在用户请求之外低频运行。数据来源、更新时间、真实/演示状态会随 API 返回。

## 测试与构建

```powershell
.\.venv\Scripts\python.exe -m ruff check api tests scripts
.\.venv\Scripts\python.exe -m pytest
pnpm --dir web lint
pnpm --dir web typecheck
pnpm --dir web build
```

## 封闭会员与 Supabase

平台没有公开注册入口。访客联系 Br1ef 并在线下付款，管理员确认后由后端使用 Supabase Admin Invite API 发送邀请，用户自行设置密码。管理员不接收、不显示、不保存明文密码。

1. 在 Supabase Dashboard 关闭公开邮箱注册，只保留邀请流程。
2. 执行 `supabase/migrations/202607220001_initial_schema.sql`。
3. 根目录 `.env` 填服务端的 `SUPABASE_URL`、`SUPABASE_SECRET_KEY`、`SUPABASE_JWT_SECRET`。
4. `web/.env.local` 只填公开的 `VITE_SUPABASE_URL` 与 `VITE_SUPABASE_PUBLISHABLE_KEY`。
5. 在 `profiles.is_admin` 设置管理员，或在服务端 `PLATANIA_ADMIN_USER_IDS` 配置管理员 UUID。

生产环境设置 `PLATANIA_ENV=production`。认证配置缺失时 API 会关闭会员访问，不会退回匿名 Demo。RLS 与数据库触发器再次验证 active、开始/到期时间及 AI/回测额度。详见 [数据库与 RLS](docs/DATABASE_RLS.md)。

## DeepSeek

在根目录被忽略的 `.env` 填写：

```dotenv
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

Key 只供后端读取，禁止放进 `web/.env.local`、浏览器包、日志或 Git。未配置时页面明确显示 Mock 模式。AI 流程为自然语言 → JSON StrategySpec → Pydantic/白名单/风险验证 → 平台策略 → 回测；不使用 `eval`、`exec` 或任意导入。

## GitHub 与部署

仓库远程为 `https://github.com/Br1eeeef/Platania.git`。推送前应运行测试、构建和密钥扫描。服务器使用只读 SSH Deploy Key，不保存个人 GitHub Token。

- 本机非敏感服务器信息：复制 `deploy/server.example.env` 为被忽略的 `deploy/server.env`
- 服务器运行密钥：`/etc/platania/platania.env`，权限 `600`
- 不要把服务器密码写入任何文件；优先 SSH 公钥认证

部署、HTTPS、防火墙、2G Swap、定时拉取与回滚见 [部署文档](docs/DEPLOYMENT.md)。

## 进一步文档

- [API](docs/API.md)
- [数据库与 RLS](docs/DATABASE_RLS.md)
- [策略规则](docs/STRATEGIES.md)
- [数据来源与授权风险](docs/DATA_SOURCES.md)
- [部署和回滚](docs/DEPLOYMENT.md)

## 当前边界

- Supabase migration 尚需在你自己的项目中执行；真实邮件、RLS 和 Admin API 需用本机配置验证。
- DeepSeek 未配置时只运行 Mock，不伪装为真实 AI 调用。
- 港股、美股和主流加密货币仅预留 Provider，不宣称已支持。
- 未接支付宝、微信或自动续费；付款状态由管理员线下确认。
- 免费数据源的商业使用、缓存和再分发权需在正式运营前单独评估。
