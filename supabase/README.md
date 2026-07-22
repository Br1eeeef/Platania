# Supabase 与 RLS

`migrations/202607220001_initial_schema.sql` 创建会员、策略、回测、自选、信息流、互动、通知和 AI 用量表，并为全部用户数据启用 RLS。

## 应用迁移

在安装 Supabase CLI 并登录后运行：

```bash
supabase link --project-ref YOUR_PROJECT_REF
supabase db push
```

也可以在 Supabase SQL Editor 中完整执行迁移文件。执行前应先在测试项目验证。

浏览器只配置 `VITE_SUPABASE_URL` 和 `VITE_SUPABASE_PUBLISHABLE_KEY`。`SUPABASE_SECRET_KEY` 与 `SUPABASE_JWT_SECRET` 仅放在服务器 `/etc/platania/platania.env` 或本机根目录 `.env` 中，永远不要写入 `web/.env.local`。

当前 API 未配置 Supabase 时返回明确的 Demo 用户；配置后，受保护接口要求 `Authorization: Bearer <Supabase access token>` 并在服务端验证 JWT。自选股请求使用用户 access token 调用 Supabase REST，由 RLS 再次约束。

