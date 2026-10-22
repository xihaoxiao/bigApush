# Cloudflare Worker 定时触发器

GitHub Actions 的 `schedule` 事件高峰期会延迟 5-30 分钟，导致"推送不准时"。
这个 Worker 用 Cloudflare Cron（通常秒级精度）准时敲一下 GitHub 的
`workflow_dispatch` 接口，由 GitHub 立刻开始跑工作流。

```
Cloudflare Cron (UTC 00:00 / 07:10 / 14:30)
        └──> Worker.scheduled()
                 └──> 按 cron 查 WORKFLOWS 映射，确定工作流
                 └──> POST api.github.com/repos/{owner}/{repo}/actions/workflows/{file}/dispatches
                          └──> GitHub Actions (event = workflow_dispatch)
                                   └──> 早间新闻 / 收盘选股 / 晚间新闻 → 飞书 / Server酱 / 邮箱
```

GitHub 自带的 `schedule` 事件**保留**作为兜底：万一 Worker 挂了，
GitHub 那边延迟几十分钟也会把当天的推送补上。

---

## 一、需要的配置

### 环境变量（Worker → Settings → Variables and Secrets）

| 名称 | 示例 | 说明 |
|------|------|------|
| `GITHUB_OWNER` | `xihaoxiao` | 仓库 owner |
| `GITHUB_REPO` | `bigApush` | 仓库名 |
| `GITHUB_REF` | `main` | 触发用的分支 |
| `WORKFLOWS` | `{"0 0 * * *":"morning-news.yml",...}` | cron 表达式 → 工作流文件（JSON） |
| `WORKFLOW_FILE` | `selection.yml` | 手动触发 / cron 未映射时的默认工作流 |

### 密钥（Worker → Settings → Variables and Secrets → Encrypt）

| 名称 | 说明 |
|------|------|
| `GH_TOKEN` | GitHub PAT。fine-grained 需勾 **Actions: Read and write**；classic 需 **repo** scope |
| `TRIGGER_TOKEN` | 随机串，用来保护 `/trigger` 端点（可选，不配则该端点禁用） |

> 少配 `GITHUB_OWNER` / `GITHUB_REPO` 是最常见的坑：URL 会拼成
> `.../repos/undefined/undefined/...`，GitHub 直接返回 404。

### Cron Trigger（Worker → Settings → Triggers → Cron Triggers）

```
0 0 * * *        # 00:00 UTC = 08:00 北京时间  早间新闻
10 7 * * 1-5     # 07:10 UTC = 15:10 北京时间  收盘选股
30 14 * * *      # 14:30 UTC = 22:30 北京时间  晚间新闻
```

Cloudflare cron **一律按 UTC 解释**，不要填北京时间。

---

## 二、部署

### 方式 A：wrangler CLI（可复现，便于排查）

```bash
cd deploy/cloudflare-scheduler
npm install
npx wrangler login                 # 或设置 CLOUDFLARE_API_TOKEN
npx wrangler secret put GH_TOKEN
npx wrangler secret put TRIGGER_TOKEN
npx wrangler deploy
```

或者用一键脚本（会做体检）：

```powershell
cd deploy/cloudflare-scheduler
Copy-Item .cf.env.example .cf.env   # 填入 CLOUDFLARE_API_TOKEN / GH_TOKEN
pwsh -File scripts/deploy.ps1
```

`wrangler.toml` 里的 `name` 必须和 Dashboard 里那个 Worker 一致
（当前是 `bigapush-scheduler`），否则会新建一个 Worker，两边各挂一条 cron → 重复触发。

> **注意**：不要和 lianghua 项目的 Worker（`lianhua`）同名。

### 方式 B：Dashboard

1. Workers & Pages → 新建 Worker，名字填 `bigapush-scheduler`
2. 用 `src/index.js` 的内容替换编辑器里的代码
3. 点 **Deploy**
4. Settings → Variables and Secrets → 按上表补齐变量和密钥
5. Settings → Triggers → 添加上面三条 Cron
6. Settings → Observability → 打开日志（否则失败信息看不到）

---

## 三、诊断（出问题时按顺序走）

### 1. `/health` —— 先看环境变量和 GitHub 侧是否通

```
https://bigapush-scheduler.573183877.workers.dev/health
```

只读，不会触发任何工作流。返回里几个关键字段：

| 字段 | 含义 |
|------|------|
| `missing` | 缺少的变量；非空说明配置有问题 |
| `github.token.ok` / `.login` | Token 是否有效；401 = Token 过期或 PAT 填错 |
| `github.workflows.<file>.ok` | 各工作流文件是否在默认分支上；404 = 文件名或仓库不对 |
| `github.recent_runs.items` | 最近 10 次运行的 `event`：`workflow_dispatch` = Cloudflare 触发成功，`schedule` = GitHub 自己的定时（会延迟） |

### 2. `/trigger` —— 立刻验证整条链路

```
curl -X POST "https://bigapush-scheduler.573183877.workers.dev/trigger?token=<TRIGGER_TOKEN>"
curl -X POST "https://bigapush-scheduler.573183877.workers.dev/trigger?token=<TRIGGER_TOKEN>&workflow=morning-news.yml"
```

返回 `{"ok":true,...}` 就说明 Cloudflare → GitHub 这段是通的；
然后去 GitHub Actions 页面确认出现了 `event = workflow_dispatch` 的运行记录。

### 3. Worker 日志 —— 看定时触发时到底发生了什么

Dashboard → Worker `bigapush-scheduler` → **Logs**，或：

```bash
npx wrangler tail
```

关键日志字段：

```json
{"level":"info","msg":"cron fired","cron":"10 7 * * 1-5","beijing":"..."}
{"level":"info","msg":"workflow resolved","file":"selection.yml","source":"cron-map"}
{"level":"info","msg":"workflow dispatched","status":204,"elapsed_ms":412}
{"level":"error","msg":"dispatch failed","status":403,"error":"GitHub dispatch failed: HTTP 403 ..."}
```

### 4. GitHub 侧确认

```bash
curl -H "Authorization: Bearer $GH_TOKEN" \
  "https://api.github.com/repos/xihaoxiao/bigApush/actions/runs?per_page=5"
```

`event` 字段是 `workflow_dispatch` 就说明是 Cloudflare 触发的，
是 `schedule` 就是 GitHub 自己的定时任务。

---

## 四、故障对照表

| 现象 | 原因 | 处理 |
|------|------|------|
| `/` 正常但到点没动静 | `scheduled` 抛错且没看日志 | 看 Logs / `wrangler tail` |
| 日志 `missing env vars` | 变量没配全 | 按上表补 `GITHUB_OWNER` / `GITHUB_REPO` |
| 日志 `HTTP 401` | PAT 无效/过期 | 重新生成 PAT 并 `secret put` |
| 日志 `HTTP 403` | PAT 缺 Actions:write / repo scope | 换 token |
| 日志 `HTTP 404` | 仓库名或工作流文件名错 | 检查 `GITHUB_OWNER`/`GITHUB_REPO`/`WORKFLOWS` |
| 日志 `HTTP 422` | 传了工作流里不存在的 input | 代码里默认不传 inputs |
| 触发的是选股而不是早间新闻 | `WORKFLOWS` 映射没配对 | 核对 cron 表达式（UTC） |
| 推送时间还是不准 | Cron 表达式按 UTC 解释 | 00:00 UTC = 08:00 北京 |
| GitHub 上没看到运行 | `workflow_dispatch` 要求工作流文件在默认分支 | 确认工作流已在 main |

---

## 五、本地测试

```bash
cd deploy/cloudflare-scheduler
npm test
```

覆盖：存活探针、`/health` 诊断、`/trigger` 鉴权与触发、cron→工作流映射、
未映射 cron 的回退、缺变量报错、GitHub 5xx 重试。零依赖，用 Node 内置 test runner。
