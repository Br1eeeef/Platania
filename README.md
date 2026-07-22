# Platania Quant Demo

Platania 的第一版 A 股日线量化研究工作台。它把行情采集、策略计算和用户浏览拆开：用户请求只读取本地缓存，AKShare 仅在明确刷新时调用，避免对免费数据源造成高频压力。

当前 Demo 包含：

- 6 只 A 股研究池与可复现的离线演示行情
- AKShare 前复权日线的手动、低频刷新
- 均线趋势、放量突破、趋势内均值回归三种策略
- K 线、MA20/60/120、成交量和买卖信号
- 次日开盘成交的回测，计入佣金、印花税、滑点和整手约束
- React + TypeScript 工作台与 FastAPI 接口
- Supabase 环境变量预留，会员鉴权将在下一阶段接入

## 本地启动

需要 Node.js 20+ 和 Python 3.11+。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt

cd frontend
npm install
npm run dev
```

另开一个终端，在项目根目录启动 API：

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --reload --port 8000
```

浏览器打开 `http://localhost:5173`。接口文档位于 `http://localhost:8000/docs`。

## 刷新行情

页面初次启动会生成并缓存固定种子的演示行情，不依赖网络。需要真实行情时单独安装 AKShare：

```powershell
python -m pip install akshare
python -m backend.scripts.refresh_data --source akshare --interval 2
```

刷新脚本默认逐个处理研究池标的，并在请求间等待 1.5 秒。生产环境建议仅在交易日收盘后运行一次，不要在用户请求链路中调用数据提供方。

缓存文件写入 `data/cache/`，不会提交到 Git。可通过 `.env.example` 中的环境变量调整路径和跨域来源。

## 测试与构建

```powershell
python -m pytest
cd frontend
npm run build
```

构建后，FastAPI 会自动托管 `frontend/dist`，因此服务器上只需运行一个低内存 Python 进程：

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

也可以使用容器：

```powershell
docker compose up --build
```

## API

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/stocks` | 研究池与策略目录 |
| GET | `/api/overview` | 研究池排名和市场宽度 |
| GET | `/api/stocks/{symbol}/analysis` | K 线、信号和回测结果 |
| POST | `/api/stocks/{symbol}/refresh` | 明确刷新单个标的缓存 |

## 边界

这是一套量化研究与历史回测工具，不构成投资建议。演示数据不是实际行情；历史回测也不能代表未来收益。面向付费会员提供具体证券信号前，需要进一步确认行情商业授权、证券投资咨询合规要求，并接入 Supabase Auth、Row Level Security 和服务端会员权限校验。

