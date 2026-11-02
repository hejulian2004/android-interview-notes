# 认证版本的配置、部署与回滚

本文件描述部署流程，不代表生产账号、服务或路由已经启用。新前端必须与后端一起发布；管理员密码未初始化时保留原刷题站，不能先切前端使其不可用。

## 身份与凭据

管理员通过服务器真实终端运行初始化工具，隐藏输入两次密码；不能在聊天、命令参数或日志中提供明文。工具只写当前用户私有目录中的密码哈希，不创建公开默认密码或匿名接管端点。`jwt-secret` 应由单独明确授权的安全部署步骤预先准备，初始化工具仅检查元信息、复用该文件，不显示或替换密钥。

```bash
python3 -m web.server.admin initialize --directory "$HOME/.config/android-study" --username admin
```

上述命令仅在程序与私有 JWT 文件已准备后可执行；已有管理员凭据须明确加 `--replace` 才能更改。配置目录 `0700`，秘密普通文件 `0600` 且归服务 UID 所有，不接受符号链接或 FIFO。部署过程不能把秘密值写进本文、Git 或浏览器。

GitHub 支持两种明确配置的传输：

- `https`：只使用显式指定的私密 token 文件，不发现其他凭据或扩大权限。题库需要 Contents 写权限；源码仅需读。读成功或 `permissions.push` 元信息均不能证明 token 写权限。
- `ssh`：复用服务用户已批准的现有 GitHub SSH 身份及 known_hosts。Git、OpenSSH 直接使用身份，不读取/复制私钥内容，不生成新 PAT、不关闭主机密钥验证、不转发 agent。题库正常非强推；三个源码适配器只读。

写操作还必须在服务端明确设置 `STUDY_GITHUB_WRITE_ENABLED=1`；读取成功不会自动启用。只对题库仓库写入，分支保护与远端权限拒绝均不能绕过。真实写验证应使用获授权的实际代码/内容更新，不创建测试垃圾，不无故修改学习资料。

## 配置键

| 变量 | 用途 |
| --- | --- |
| STUDY_PUBLIC_ORIGIN | 精确 HTTPS origin，例如 `https://txy.hejulian.org` |
| STUDY_ADMIN_USERNAME | 与初始化命令一致的管理员用户名 |
| STUDY_ADMIN_PASSWORD_HASH_FILE | 私密 `admin-password-hash` 文件 |
| STUDY_JWT_SECRET_FILE | 私密 `jwt-secret` 文件；至少 32 字节高熵密钥 |
| STUDY_GITHUB_TRANSPORT | `https` 或 `ssh`，默认 https |
| STUDY_GITHUB_TOKEN_FILE | 仅 https 传输需要，私密 bearer token 文件 |
| STUDY_GITHUB_CACHE_ROOT | SSH 传输必需，Web 根外、服务用户独占的绝对缓存目录 |
| STUDY_GITHUB_WRITE_ENABLED | 默认关闭，只有明确批准题库写入才设 1 |
| STUDY_SOURCE_REPOSITORIES | 显式注册列表，最多四个已授权 exact slug |
| STUDY_TRUSTED_PROXY_IPS | 实际反代 TCP peer 的精确数字 IP，不是任意 XFF/CIDR |
| STUDY_STATIC_ROOT | 已验证的新静态 dist/release 目录 |
| STUDY_MODEL_ALLOWED_HOSTS | 明确批准的公网供应商主机/端口，空则不能启用外部模型 |
| STUDY_MODEL_BASE_URL / STUDY_MODEL_NAME / STUDY_MODEL_API_KEY | 可选模型配置；key 不返回前端 |
| STUDY_MODEL_INTERNAL_ENDPOINTS | 默认空；受信内部 HTTPS 端点须另行明确批准 |

内联 `STUDY_JWT_SECRET`、`STUDY_ADMIN_PASSWORD_HASH` 仅为兼容保留，生产推荐文件配置。显式文件不安全或缺失时 fail closed，不回退。模型先留空，管理员之后在页面填写 key 前还需配置供应商允许列表与供应商侧费用硬上限。

可注册源码仅限 `hejulian2004/android-interview-notes`、`hejulian2004/ssh_mobile`、`hejulian2004/testDemo`、`hejulian2004/word-crush-app`。服务端默认仅题库；其他仓库须明确加入配置。读取采用固定完整 SHA、严格代码路径白名单；未核验可见性时保守按私有处理。当前默认分支不能冒充笔记记录的历史 XML/SDK 实现。

## 运行与网络

Python 3.10+、Git、OpenSSH 是 SSH 模式所需运行时。`runtime-image/` 仅包含运行时 Dockerfile，不把整个 checkout 或秘密作为构建上下文；应用、状态与现有 SSH 身份通过最小只读/可写挂载分别提供。容器服务 UID 必须有匹配 passwd/home 记录、与私密文件 UID 一致。

实际 Caddy 是容器时，宿主 loopback 与其 loopback 不同。一个可选隔离方案是新后端容器共享既有 Caddy 的网络命名空间，只监听 `127.0.0.1:8183`，不发布宿主端口、不改变现有容器网络。先核实命名空间内端口空闲和外连能力；不得据此重建/重启其他容器或开放防火墙。

使用两条内联路径匹配，并校验其排在原静态路由前；不要假定命名匹配器会保持相同排序。仅在现有学习路径静态路由前添加 API 匹配；先备份、校验候选配置，确认其他路由规范化结果不变，再平滑重载：

```caddyfile
handle /android-study/api {
    reverse_proxy 127.0.0.1:8183 {
        header_up X-Study-Client-IP {remote_host}
    }
}
handle /android-study/api/* {
    reverse_proxy 127.0.0.1:8183 {
        header_up X-Study-Client-IP {remote_host}
    }
}
```

Caddy 必须覆盖专用客户端 IP 头，服务器仅信任明确配置的实际 proxy peer。共享命名空间且上游为 IPv4 loopback 时 peer 为 `127.0.0.1`，仍应验证。否则全部用户会共用登录限流桶，不能直接相信客户端伪造头。

新站点专用 CSP 将 `connect-src` 收紧为 `'self'`；保留其他路径响应头。遵守 `../DEPLOYMENT.md` 中已有延迟 header 匹配和校验要求。新后端资源应设 CPU、内存、PID 限额，容器只读根文件系统、最小挂载、丢弃额外能力，不使用公开端口。

## 发布、验收与回滚

1. 跟进远端并保留并发修改，运行测试后提交实际代码；服务端可信 `scripts/build.py` 必须与 GitHub 发布版本一致，否则 Q/E 写入返回版本冲突。
2. 在独立 release 准备后端源码、可信生成器与新 dist。先完成管理员安全初始化，验证后端匿名拒绝、会话、CSRF、同源业务与源码只读，再切换 UI/API。
3. 验证 HTTPS、实际凭据权限与 HEAD、491 题 ID/进度兼容、源代码完整 SHA 引用、公开资源无秘密，以及其他服务的路由/健康基线。不配置或试调用付费模型。
4. 保留旧静态 release 和 Caddy 原配置；失败时回切旧 UI、恢复仅本站的 API 路由并停止新后端。核对同期配置修改，不能恢复覆盖其他项目新变化。

单进程内存会话、草稿、内容缓存、模型配置/历史/调用预算会随重启失效；SSH Git 对象缓存和候选事务元数据独立持久化。模型 key 页面设置不跨重启，内存计数不是永久花费上限；部署必须同时采用供应商预算。未初始化或配置错误时不能宣称站点可登录。当前模拟测试不能替代真实公网、HTTPS Cookie、实际供应商或真机验证。
