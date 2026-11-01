# 部署与回滚

目标：现有服务器上的 `https://txy.hejulian.org/android-study/`。使用已有 Caddy 的 HTTPS、端口和证书；不安装运行时，不增加端口、后台数据库、账号或定时任务。

## 目录与持久化

- Git checkout：`~/coding/android-study-site/`，网站源码在其 `web/`。
- 构建目录：`~/coding/android-study-site/web/dist/`，仅静态公开内容。
- 已有 Caddy 容器持久卷中的专用路径：`/config/android-study-site/releases/<release>/`。
- Caddy Web 根目录：`/config/android-study-site/current`，链接到上述某个发布目录。
- 部署备份保存在项目本地的 `web/.deployment/`，不提交 Git。备份只供本机回滚，不属于 Web 根目录。

## 首次挂载路由

此操作只有用户批准后才能执行。先记录原站响应、备份现有 Caddyfile；保留其他路由及现有请求匹配逻辑。为 `/android-study` 增加末尾斜杠重定向，并在现有 catch-all 之前添加静态路径：

```caddyfile
redir /android-study /android-study/ 308
handle_path /android-study/* {
    root * /config/android-study-site/current
    header Cache-Control "no-cache"
    file_server
}
```

站点专用的 Content-Security-Policy 必须允许：

```text
default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' https://api.github.com https://raw.githubusercontent.com; frame-ancestors 'none'; base-uri 'none'; form-action 'none'; object-src 'none'
```

保留旧路径的完整原有响应头，仅将该学习路径与原路径的响应头匹配器分开，避免全站放宽 GitHub 网络许可。Caddy 的响应头包含删除操作时会延后执行，因此不能仅在内部静态路由添加一个可能被外层覆盖的 CSP。参考 [Caddy header 官方文档](https://caddyserver.com/docs/caddyfile/directives/header)。

将候选配置放在独立目录，以运行中的 Caddy 环境进行 `caddy validate --config <candidate> --adapter caddyfile`。校验成功后保持原配置文件 inode 写入新内容（已有容器使用 bind mount），然后 `caddy reload` 平滑载入；不重启任何容器。确认新站及原站基线均通过。禁止修改防火墙、证书账户、SSH 或其他服务权限。

## 后续界面版本

先更新并验证 Git checkout，在网站目录运行 `node scripts/build.mjs`。把 `dist/` 内容复制到新的专用 release 目录，验证后原子切换 `current` 链接；通常无需再 reload Caddy。不要复制 node_modules、.git、.env、日志或项目根目录至公开目录。

仅修改题库时直接维护原仓库 docs/questions/supplements 并提交。用户下一次打开或手动刷新时从 GitHub 获取新版本，无需服务器拉取、重建或重载。

## 回滚

- 仅回滚界面：把 `current` 原子指回上一份发布目录，不需要重载。
- 撤销首次路由：先确认当前配置没有其他同期编辑；恢复 `.deployment/` 中部署前的 Caddyfile 备份，校验并平滑 reload。原站基线应恢复，学习路径将回落原有站点。
- 不删除其他服务或用户文件。不清除浏览器 localStorage；学习状态由用户导出或自行管理。

Python 静态服务脚本仅用于 loopback 开发验证；当前生产使用 Caddy file_server。不要自行把辅助服务绑定至公网或另开端口。
