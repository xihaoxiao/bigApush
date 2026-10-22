# 缅A每日推送

A股量化选股 + 每日自动推送系统，通过 GitHub Actions 实现全自动化运行。

## 功能特性

- **智能选股**：15种量化选股策略，覆盖底部反转、趋势加速、形态突破等多个维度
- **大盘复盘**：每日推送上证/深证/创业板/科创50指数行情
- **板块分析**：行业板块、概念板块涨跌排行
- **资金流向**：板块资金净流入/净流出TOP5
- **财经要闻**：自动抓取新浪财经最新资讯
- **新增/去除对比**：每日对比上个交易日选股变化
- **买入建议分析**：基于技术指标（均线/RSI/MACD）给每只股票评分
- **交易日判断**：自动识别A股交易日，非交易日跳过
- **多渠推送**：选股结果 + 分析报告自动发送到飞书 / Server酱 / 邮箱（填哪个推哪个，可同时推送）

## 15种选股策略

| # | 策略名称 | 核心逻辑 | 适用场景 |
|----|---------|--------|--------|
| 1 | **底部趋势拐点** | 深度下跌后的反转拐点 | 极端底部 |
| 2 | **涨停回马枪策略** | 涨停后回调再次启动 | 短期强势 |
| 3 | **涨停横盘策略** | 涨停后横盘整理突破 | 突破选股 |
| 4 | **启明星策略** | 三根K线底部反转形态 | 底部反转 |
| 5 | **多金叉共振** | 均线/KDJ/MACD金叉共振 | 多头共振 |
| 6 | **多方炮策略** | 两阳夹一阴K线组合 | 短期反弹 |
| 7 | **阻力位突破策略** | 股价突破关键阻力位 | 突破选股 |
| 8 | **强势洗盘弱转强** | 强势股洗盘后转强 | 趋势反转 |
| 9 | **趋势加速拐点** | 上升趋势中的加速拐点 | 趋势加速 |
| 10 | **仙人指路策略** | 长上影线突破形态 | 突破选股 |
| 11 | **W底策略** | W底双底反转形态 | 双底反转 |
| 12 | **趋势起点策略** | 趋势启动初期识别 | 趋势启动 |
| 13 | **2560战法** | 基于特定K线形态的选股策略 | 形态突破 |
| 14 | **金三角策略** | A/B/C三点金叉形态检测趋势拐点 | 趋势拐点 |
| 15 | **金叉不绿策略** | 金叉形态 + 绿色K线过滤提升信号质量 | 精准金叉 |

## 买入建议评分标准

| 评分 | 建议 | 说明 |
|------|------|------|
| 🟢 70分以上 | 建议买入 | 技术面多项指标向好 |
| 🟡 55-69分 | 可以关注 | 部分指标良好 |
| ⚪ 40-54分 | 建议观望 | 指标中性 |
| 🔴 40分以下 | 建议回避 | 技术面走弱 |

分析维度：均线排列、RSI指标、MACD趋势、成交量变化、涨跌幅

## 自动运行时间

| 时间 | 任务 | 内容 |
|------|------|------|
| 15:10（交易日） | 收盘选股 | 选股 + 复盘 + 板块 + 新闻 + 买入建议 |
| 08:00（每天） | 早间新闻 | 大盘回顾 + 板块 + 财经要闻 |
| 22:30（每天） | 晚间新闻 | 收盘行情 + 板块 + 晚间要闻 |

## 快速开始

### 1. Fork 仓库

点击右上角 Fork 按钮，将仓库复制到你的 GitHub 账号下。

### 2. 配置推送渠道

飞书、Server酱、邮箱三个渠道都可选，**填哪个就推哪个，多个都填会同时推送**。

> ⚠️ **凭据只走 GitHub Secrets，不要写进仓库里的配置文件。**
> `config/config.yaml` 已从版本控制移除（`config/config.defaults.yaml` 是仓库内的非敏感默认配置）。
> 本地开发请用 `config/config.local.yaml`（已 gitignore，模板见 `config/config.local.yaml.example`）。

**飞书**

1. 在飞书群中添加自定义机器人
2. 复制 Webhook URL
3. 进入仓库 → Settings → Secrets and variables → Actions
4. 新建 Secret：`FEISHU_WEBHOOK`，值为你的 Webhook URL

**Server酱**

1. 打开 <https://sct.ftqq.com>，微信扫码登录后获取 SendKey（Server酱 Turbo / Server酱³ 均支持）
2. 进入仓库 → Settings → Secrets and variables → Actions
3. 新建 Secret：`SERVERCHAN_SENDKEY`，值为你的 SendKey

**邮箱（SMTP）**

通用 SMTP，QQ邮箱 / 163 / Gmail / Outlook 都能用。

1. 在邮箱设置里开启 SMTP 服务并获取授权码
   - QQ邮箱：设置 → 账户 → 开启 SMTP → 生成授权码
   - 163邮箱：设置 → POP3/SMTP/IMAP → 开启并获取授权码
   - Gmail：需开启两步验证并生成"应用专用密码"
2. 进入仓库 → Settings → Secrets and variables → Actions，新建以下 Secret：

   | Secret | 示例 | 说明 |
   |--------|------|------|
   | `SMTP_HOST` | `smtp.qq.com` | SMTP 服务器 |
   | `SMTP_PORT` | `465` | 465=SSL，587=STARTTLS，留空按 host 自动推断 |
   | `SMTP_USER` | `you@qq.com` | 登录账号（QQ 填完整邮箱地址） |
   | `SMTP_PASSWORD` | `abcdefghijkl` | **授权码**，不是登录密码 |
   | `SMTP_FROM` | `you@qq.com` | 发件人，留空则用 `SMTP_USER` |
   | `SMTP_TO` | `a@qq.com,b@163.com` | 收件人，逗号分隔，留空则发给 `SMTP_USER` |
   | `SMTP_USE_SSL` | `true` | 465 端口填 `true`，587 端口填 `false` |
   | `SMTP_USE_TLS` | `false` | 587 端口填 `true` |

   > 密码一定要用**授权码**。用登录密码会报 `SMTPAuthenticationError`。

### 3. 启用 Actions

进入仓库 → Actions → 点击 "Enable workflow"

### 4. 手动测试

在 Actions 页面 → 选择任务 → Run workflow → 点击绿色按钮运行

## 配置说明

### 配置文件加载顺序

```
config/config.defaults.yaml   ← 仓库内，非敏感配置（filters/trading/data_dir 等）
        ↓ 覆盖
config/config.yaml            ← 兼容旧路径（已 gitignore，CI 上不存在）
        ↓ 覆盖
config/config.local.yaml      ← 本地凭据（已 gitignore，永不提交）
        ↓ 覆盖
环境变量 / GitHub Secrets      ← 最高优先级
```

由 `utils/config_loader.py` 统一负责，所有入口（`main.py` / `web_server.py` /
`daily_news.py` / `evening_news.py`）共用。

### 本地开发

```bash
# 复制凭据模板并填入（该文件不会被提交）
cp config/config.local.yaml.example config/config.local.yaml
```

### config/config.defaults.yaml（仓库内，非敏感）

```yaml
# 数据更新配置
update:
  lookback_days: 10

# 股票过滤配置
filters:
  min_market_cap: 10      # 最小市值（亿）
  max_market_cap: 10000   # 最大市值（亿）
  exclude_st: true        # 排除ST股票

# 交易配置
trading:
  initial_capital: 300000.0
```

### config/config.local.yaml（本地凭据，不提交）

```yaml
# 飞书机器人配置（可选）
feishu:
  webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"

# Server酱配置（可选，与飞书/邮箱可同时推送）
serverchan:
  sendkey: "SCTxxxxx"

# 邮箱推送配置（可选，与飞书/Server酱可同时推送）
email:
  host: "smtp.qq.com"
  port: 465
  user: "you@qq.com"
  password: "your_授权码"
  from: ""
  to: ""
  use_ssl: true
  use_tls: false
```

推送渠道也可以用环境变量配置，且优先级高于配置文件：

| 渠道 | 环境变量 |
|------|----------|
| 飞书 | `FEISHU_WEBHOOK` |
| Server酱 | `SERVERCHAN_SENDKEY`（兼容 `SERVER_CHAN_SENDKEY` / `SCKEY`） |
| 邮箱 | `SMTP_HOST` `SMTP_PORT` `SMTP_USER` `SMTP_PASSWORD` `SMTP_FROM` `SMTP_TO` `SMTP_USE_SSL` `SMTP_USE_TLS` |

三个渠道相互独立，任意一个配置完整就推送，全部配置则同时推送。

## 定时触发（Cloudflare Worker）

GitHub Actions 自带的 `schedule` 事件高峰期会延迟 5-30 分钟。
项目内置一个 Cloudflare Worker，用 Cloudflare Cron（秒级精度）准时触发
GitHub 的 `workflow_dispatch`，让推送准点到达。

```
Cloudflare Cron (UTC 00:00 / 07:10 / 14:30)
        └──> Worker.scheduled()
                 └──> POST api.github.com/repos/xihaoxiao/bigApush/actions/workflows/{file}/dispatches
                          └──> GitHub Actions (event = workflow_dispatch)
```

| Cloudflare Cron (UTC) | 北京时间 | 触发的工作流 |
|----------------------|----------|--------------|
| `0 0 * * *` | 08:00 | `morning-news.yml` 早间新闻 |
| `10 7 * * 1-5` | 15:10 | `selection.yml` 收盘选股 |
| `30 14 * * *` | 22:30 | `evening-news.yml` 晚间新闻 |

部署见 [`deploy/cloudflare-scheduler/README.md`](deploy/cloudflare-scheduler/README.md)：

```bash
cd deploy/cloudflare-scheduler
npm install
npx wrangler secret put GH_TOKEN
npx wrangler secret put TRIGGER_TOKEN
npx wrangler deploy
```

> GitHub 自带的 `schedule` 保留作兜底（Worker 挂了还能补推）。
> Worker 名字必须是 `bigapush-scheduler`，与其它项目（如 lianghua 的 `lianhua`）**不能重名**，
> 否则会新建第二个 Worker → 重复触发。

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据（首次运行）
python main.py init

# 执行选股并推送
python main.py run

# 启动Web界面
python main.py web
```

## 推送消息示例

```
📊 缅A每日推送 (2026-07-06 15:10:32)
共 36 只股票入选

【趋势共振反转策略】: 36 只
  000576 甘化科工 价格:7.4
  000848 承德露露 价格:7.82
  ...

━━━━━━━━━━━━━━━━━━━━
📋 与 2026-07-05 对比
  🟢 新增 (5只):
    + 002139 拓邦股份
  🔴 去除 (3只):
    - 000001 平安银行

━━━━━━━━━━━━━━━━━━━━
🎯 买入建议分析

🟢 002217 合力泰
  评分: 72分 | 建议买入
  理由: 均线多头排列, RSI适中, MACD多头

🟡 000576 甘化科工
  评分: 55分 | 可以关注
  理由: RSI适中(50), MACD空头

━━━━━━━━━━━━━━━━━━━━
📈 今日大盘复盘 (2026-07-06 15:10:32)
  🔴 上证指数: 3250.60 (+0.52%) 4521亿
  🟢 深证成指: 10850.30 (-0.15%) 5832亿

📊 行业板块
  🔴 领涨: 供水供气(+0.52%) | 公路桥梁(+0.38%)
  🟢 领跌: 酿酒行业(-1.31%) | 飞机制造(-0.95%)

💡 概念板块
  🔴 领涨: AI概念(+2.15%) | 芯片概念(+1.82%)
  🟢 领跌: 新能源(-1.56%) | 医美概念(-1.23%)

💰 板块资金流向
  净流入: 触摸屏(+107亿) | 华为海思(+95亿)
  净流出: 融资融券(-84亿) | 保险重仓(-49亿)

━━━━━━━━━━━━━━━━━━━━
📰 今日财经要闻
  • 新闻标题1
    新闻摘要内容...
```

## 数据来源

- 股票行情：腾讯财经
- 板块数据：新浪财经
- 资金流向：新浪财经
- 财经新闻：新浪财经
- 历史数据：东方财富

## 项目结构

```
缅A每日推送/
├── main.py              # 主程序入口
├── web_server.py        # Web服务器
├── simple_analyzer.py   # 买入建议分析
├── sector_data.py       # 板块数据获取
├── daily_news.py        # 早间新闻脚本
├── evening_news.py      # 晚间新闻脚本
├── config/              # 配置文件（defaults 提交，local 不提交）
├── strategy/            # 选股策略
├── trading/             # 交易相关
├── utils/               # 工具函数
├── web/                 # Web前端
├── deploy/              # 部署脚本（Cloudflare Worker 等）
├── data/                # 数据文件（不上传）
└── .github/workflows/   # GitHub Actions配置
```

## GitHub Actions

| Workflow | 说明 | 触发时间 |
|----------|------|----------|
| selection.yml | 收盘选股+复盘 | 交易日 15:10 |
| morning-news.yml | 早间新闻 | 每天 08:00 |
| evening-news.yml | 晚间新闻 | 每天 22:30 |
| keep-alive.yml | 保持仓库活跃 | 每天 01:00 |

## 参考项目

本项目基于以下开源项目开发：

- [KHunter](https://github.com/ling-0729/KHunter) - A股量化交易系统，提供选股策略和数据分析框架

## 免责声明

本工具仅用于学习和研究，不构成任何投资建议。股市有风险，投资需谨慎。

## License

MIT
