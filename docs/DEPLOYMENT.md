# Ubuntu 部署、自动更新与回滚

目标为 Ubuntu 2 vCPU / 1 GB，Nginx + 单 Uvicorn worker + Python venv，不强制 Docker。真实连接前需要确认公网 IP/域名、发行版版本、SSH 用户/端口、sudo、80/443、防火墙、现有 Nginx/Docker/网站和 DNS。不要发送服务器密码或 SSH 私钥；优先把生成的公钥加入服务器。

## 文件与秘密

- `/opt/platania/repository`：只读 Deploy Key 克隆的 Git 仓库
- `/opt/platania/releases`：不可变发布目录
- `/opt/platania/current`：当前 release 软链接
- `/opt/platania/shared/data`：持久行情缓存
- `/opt/platania/venv`：共享 Python venv
- `/etc/platania/platania.env`：服务端环境变量，root 拥有，权限 `600`

服务器地址、端口、用户和域名写在你本机被忽略的 `deploy/server.env`；任何地方都不要保存服务器密码。DeepSeek/Supabase Secret 只写服务器的 `/etc/platania/platania.env`。

## 首次安装概览

安装 `nginx python3-venv git curl rsync nodejs pnpm`，创建 `platania` 系统用户和上述目录；为私有仓库生成只读 SSH Deploy Key 并添加到 GitHub。复制并按实际路径安装 `deploy/*.service`、`deploy/*.timer`、`deploy/nginx.conf` 和 `deploy/logrotate.conf`，执行 daemon-reload 后启用 API、数据与部署 timer。

1 GB 内存机器可审阅后运行 `deploy/create-swap.sh` 创建约 2 GB Swap。防火墙只开放 SSH 实际端口、80、443；8010 仅监听 `127.0.0.1`。

## 自动发布

`deploy/deploy.sh` 使用 `flock` 防并发，fetch `origin/main`，以 Git SHA 建临时 release；requirements 哈希变化时才更新 venv；pnpm 锁文件安装并构建 `web/dist`；原子切换 `current` 后重启单 worker API。健康检查成功才删除旧版本，默认保留最近五个。

私有仓库服务器只保存 Deploy Key，不保存个人 GitHub Token。定时器轮询更新；`git fetch`/归档不会修改仓库工作树。

## 回滚与故障排查

健康检查 15 次失败时脚本自动把 `current` 指回上一 release 并重启。人工回滚时选择 `/opt/platania/releases` 内已知正常目录，原子更新 `current.next` → `current`，重启 `platania-api.service`，再验证 `/api/health`。

排查顺序：`systemctl status`、`journalctl -u platania-api`、Nginx error log、`curl http://127.0.0.1:8010/api/health`、环境文件权限、磁盘/内存、DNS。不要把完整环境文件或 Authorization Header 粘贴到日志/聊天。

HTTPS 使用 Certbot/Let’s Encrypt，在 DNS 已解析且 80/443 开放后申请；成功前不要把示例域名当成真实站点。生产环境必须设置 `PLATANIA_ENV=production`，并完成 Supabase/DeepSeek 配置或接受相应功能 fail closed/Mock。
