# Supabase 数据库与 RLS

迁移文件：`supabase/migrations/202607220001_initial_schema.sql`。

## 表

用户与会员：`profiles`、`memberships`、`ai_usage`。研究资产：`watchlists`、`watchlist_items`、`strategies`、`strategy_versions`、`backtest_runs`、`signals`。社区：`posts`、`follows`、`likes`、`comments`、`notifications`。管理员审计：`admin_audit_logs`。

`memberships` 包含 `user_id`、`plan`、`status`、`starts_at`、`expires_at`、AI/回测额度、付款备注、外部参考号、创建管理员和审计时间。状态为 `pending`、`active`、`expired`、`suspended`、`banned`。

## 封闭注册

在 Supabase Dashboard 的 Auth Providers 中关闭公开邮箱注册。新用户只允许后端使用 Secret/service_role 调用 Admin Invite API。数据库触发器只创建 pending 会员记录；管理员确认付款后再写入 active 方案。系统从不创建或存储临时明文密码。

## 权限模型

- 用户只能操作自己的私人记录。
- 公开帖子仅允许有效登录会员读取，且只通过允许的公开字段 API 输出。
- `current_user_has_active_membership()` 同时检查 status、开始和到期时间。
- 功能表使用 restrictive RLS，将有效会员检查与所有权策略做 AND。
- `profiles.is_admin` 不在普通用户可更新列中；管理员 RLS 由安全定义函数判断。
- Secret/service_role 只在 FastAPI 服务端环境中，前端只能使用 publishable key。
- `ai_usage_quota` 和 `backtest_runs_quota` 触发器在插入完成记录时锁定会员行并再次检查日额度，防止并发绕过 API 预检查。

## 应用与验证

在空的 Supabase 项目 SQL Editor 执行 migration，或用 Supabase CLI migration 流程。执行后至少验证：普通用户不能更新 membership/is_admin；过期/暂停/封禁用户不能读写功能表；非管理员不能读审计日志；额度上限处的并发插入被拒绝。

迁移尚未在真实项目运行前，不应宣称线上 Supabase 已启用。生产发布时设置 `PLATANIA_ENV=production`，缺少完整 Supabase 服务端配置会 fail closed。
