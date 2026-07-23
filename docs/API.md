# API 说明

默认根地址为 `http://127.0.0.1:8010/api`，交互文档位于 `/docs`。除 `/api/health` 外，市场、策略、回测、AI、会员、信息流和管理员接口均经过后端会员依赖；生产环境必须携带 Supabase Bearer Token。

## 通用约定

- JSON 请求/响应；时间使用 ISO 8601，行情交易日为 `YYYY-MM-DD`
- 分页参数为 `page`、`page_size`
- 客户端超时 15 秒；数据 Provider 具有独立超时、重试和退避
- 校验错误统一返回 `422`，会员无权 `403`，未登录 `401`，额度耗尽 `429`
- 统一错误主体：`{"error":{"code":"...","message":"...","details":{...}}}`；业务 HTTP 错误也可使用 FastAPI `detail`
- 日志禁止记录 Authorization、DeepSeek Key 或 Supabase Secret

## 路由

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/health` | 服务、数据、AI、认证模式 |
| GET | `/market/status` | A 股状态、来源与更新时间 |
| GET | `/instruments` | 标的分页和搜索 |
| GET | `/market/{symbol}/bars` | 日/周 K 线 |
| GET | `/market/{symbol}/indicators` | 技术指标 |
| GET | `/market/{symbol}/signals` | 三套策略信号 |
| POST | `/backtests` | 创建回测并扣减成功用量 |
| GET | `/backtests/{id}` | 读取回测结果 |
| POST | `/ai/strategy` | 生成受约束 StrategySpec |
| POST | `/ai/strategy/validate` | 验证并生成只读代码 |
| POST | `/ai/strategy/backtest` | 使用平台引擎回测 AI spec |
| GET | `/strategies` | 策略目录 |
| GET | `/feed` | 会员信息流 |
| GET | `/me` | 会员状态和用量 |
| GET/POST/DELETE | `/watchlist` | 自选股 |
| GET | `/admin` | 管理概览 |
| GET/POST | `/admin/members` | 列表、邀请 |
| PATCH | `/admin/members/{user_id}` | 续费/暂停/恢复/封禁/额度 |
| GET | `/admin/usage` | 会员用量配置 |
| GET | `/admin/audit-log` | 管理操作日志 |
| GET | `/admin/members.csv` | 导出会员 |

`POST /admin/members` 必须包含邮箱、套餐、起止时间、额度、付款确认以及付款备注或外部参考号。服务端调用 Supabase Admin Invite；不接受密码字段。

## 可配置回测

`POST /backtests` 支持 `symbol`、`strategy_id`、`initial_cash`、`commission_rate`、`minimum_commission`、`stamp_duty_rate`、`slippage_rate`、`max_position`、`benchmark_symbol`、可选 `start_date` / `end_date`，以及受白名单约束的 `strategy_parameters`。日期范围至少包含 130 根交易日 K 线。

三套平台策略分别允许：趋势动量的 `rsi_min`、`rsi_max`、`atr_stop`；放量突破的 `volume_ratio`、`atr_stop`；均值回归的 `rsi_entry`、`rsi_exit`、`max_holding_days`。未知参数和越界数值返回 `422`，不接受任意代码。回测结果的 `parameters` 保存完整参数快照。
