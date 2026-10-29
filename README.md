<div align="center">

<img src="assets/logo.png" width="112" alt="LBW Workbench">

# LBW Workbench · 本地破甲工作台

把 11 个 AI 客户端的工作词包与完整技能树，一次装进本机；每一笔写入都留字节级备份，随时一键回滚。

Windows x64 便携版 · 不需要安装 Node · 不需要管理员权限 · 不联网也能跑

[下载最新版](https://github.com/edwardmackiezyv885-art/lbwapi-workbench/releases/latest) · [快速开始](#三步上手) · [常见问题](#常见问题) · [联系方式](#联系方式)

</div>

> **English** — LBW Workbench is a local Windows workbench that installs prompt packs and skill trees into the config directories of 11 AI clients (Codex, Claude Code, Cursor, Gemini, DeepSeek Harness, Grok, GLM, Doubao, WorkBuddy, MiMo, Kimi), following each client's own loading contract. Every write is hashed, backed up and reversible. It also ships an OpenAI-compatible relay panel, a workflow engine, an IDA toolbox and 16 local analysis tools. Portable build: no Electron, no installer, no admin rights.

---

## 这是什么

大多数 AI 客户端都允许你用一份本地文件定义「它该怎么干活」——`AGENTS.md`、`CLAUDE.md`、`rules/*.mdc`、`skills/*/SKILL.md`。手工维护这些文件很痛苦：路径各不相同、格式各不相同、改错了没法回退。

LBW Workbench 把这件事变成三步：**勾选 → 预览 → 写入**。

- 自动识别本机装了哪些客户端，按各自合同的路径与格式落盘
- 写之前先把原文件连内容带权限位备份下来，写之后逐字节校验
- 不满意就点「一键卸载」，文件按字节还原，新增的文件删掉

它不会替客户端做决定：写进去的词包是否生效，取决于那个客户端自己怎么加载。本工具只保证「文件写对了、能撤回」。

---

## 功能

| 模块 | 能力 |
| --- | --- |
| **一键破甲** | 11 个席位批量安装 / 单席位安装，预览 → 写入 → 校验 → 卸载全流程；写入计划逐文件列出路径、动作、字节数 |
| **完整技能树** | 随包附带两套上游技能库（94 项技能 / 11,671 个文件），落盘到各客户端配置根下的 upstream 技能目录（沿用历史目录名，旧安装可以继续增量更新），并把索引入口织进对应指令文件 |
| **LBW 中转** | 填 Base URL + Key → 测连接 → 拉模型 / 看用量 → 一键复制 Codex 的 `config.toml` 片段 |
| **五档工作模式** | `MAX / FOCUS / BUILDER / RESEARCH / CREATE`，把目标 / 上下文 / 约束 / 输出格式 / 验收组装成任务契约，并能在回答回来后校验格式 |
| **工作流引擎** | 5 套模板，可启动 / 暂停 / 继续 / 取消 / 清理，事件通过 SSE 实时推到界面 |
| **IDA 工具** | IDA 9.x 简体中文界面安装 / 卸载；把 IDA MCP（`127.0.0.1:13337`）写进 8 个客户端的配置 |
| **工具箱** | 16 个本地程序：网站测试、端口扫描、请求测试、PE/ELF 分析、字节查找、补丁副本生成、编解码、哈希爆破，另有 AI 自动调用代理 |
| **工单** | 记一次测试：范围 / 资产 / 发现 / 证据，可导出成稿 |

### 11 个席位

| 席位 | 写入位置 |
| --- | --- |
| Codex | `~/.codex/prompts/cha-codex.md` + `config.toml` 的 `model_instructions_file` + `AGENTS.md`（标记段） |
| Claude Code | `~/.claude/CLAUDE.md`（标记段）+ `rules/cha-breakopen.md` |
| Cursor | `~/.cursor/rules/cha-cursor.mdc`（`alwaysApply: true`）+ `skills/cha-cursor/SKILL.md` |
| Gemini | `~/.gemini/GEMINI.md` + `settings.json` 的 `context.fileName`（JSONC 原位补丁，保留注释） |
| DeepSeek Harness | `$DSH_HOME/AGENTS.md` 短入口 + `skills/cha-deepseek/SKILL.md`（默认 `~/.dsh`） |
| Grok | `~/.grok/AGENTS.md` + `rules/cha-breakopen.md` + `skills/cha-breakopen/SKILL.md` |
| GLM / ZCode | `~/.glm/GLM.md` + `~/.zcode/AGENTS.md`，两份根目录分别成事务 |
| 豆包 | `%LOCALAPPDATA%\Doubao\...\.user_skills\cha-doubao\SKILL.md` |
| WorkBuddy | `~/.workbuddy/AGENTS.md` + `skills/cha-workbuddy/SKILL.md` |
| MiMo | `~/.config/mimocode/skills/cha-mimo/SKILL.md` |
| Kimi | `~/.kimi-code/skills/cha-kimi/SKILL.md` |

---

## 配套资源

工具本体能独立跑，下面这些是分开维护的：装完之后要调模型、想看实测数据、或者想参考别人怎么用，可以从这里进。

| 资源 | 地址 | 是什么 |
| --- | --- | --- |
| 实测数据 | https://lbwapi.online/data/ | 30 题固定题库、5 类真实场景、7 家模型的横向对比，图表与数据表可自由引用（CC BY 4.0） |
| 接入教程 | https://lbwapi.online/tutorials/ | Cursor / Cherry Studio / LobeChat / NextChat 的完整配置步骤，附报错对照表 |
| 用户作品 | https://lbwapi.online/vibecoding/ | 用这套工具做出来的东西，以及踩过的坑 |
| API 中转 | https://lbwapishop.online/register | 跑通上面步骤需要的接口，注册送试用额度，1 元起充 |

> 离线也能完整使用「一键破甲」「技能树」「工具箱」——只有「LBW 中转」面板需要联网。

**Companion resources** — [benchmark data](https://lbwapi.online/data/) · [setup guides](https://lbwapi.online/tutorials/) · [community showcase](https://lbwapi.online/vibecoding/)

---

## 下载与安装

1. 打开 [Releases](https://github.com/edwardmackiezyv885-art/lbwapi-workbench/releases/latest)，下载 `LBW-Workbench-1.0.1-win-x64.zip`
2. 解压到任意目录（不要放在 C 盘根目录或带权限限制的路径）
3. 核对校验和：`SHA256SUMS.txt` 在同页

```powershell
Get-FileHash .\LBW-Workbench-1.0.1-win-x64.zip -Algorithm SHA256
```

包内已含 Node.js 24.16.0（官方签名），**不需要另外安装任何东西**。

> 从源码跑：见 [从源码运行](#从源码运行)。

---

## 三步上手

### 1. 启动

双击 `启动工作台.cmd`。浏览器会自动打开：

```
http://127.0.0.1:8788/src/workbench/index.html
```

没自动打开就把这行粘到浏览器。**关掉那个黑色窗口 = 停止服务**；也可以用 `停止工作台.cmd`。重复双击不会开出第二份，只会再把页面打开一次。

如果 8788 被占用，程序会自动往后找 8789、8790……并在窗口里打印实际端口。

### 2. 一键破甲

1. 左侧「一键破甲」，软件会自动识别本机装了哪些客户端
2. 勾上要装的，点「预览」——这一步只读，不写盘，会逐文件列出将要改动的路径
3. 点「写入」。原文件会自动备份到目标目录的 `.lbw-history/`
4. 把对应客户端**完全退出再打开**（配置只在启动时读取）
5. 在对话框里单独发一句：

```
lbwapi
```

发对了会回一段激活页；大小写都认，前后不要加别的字，整句必须只有这个词。

### 3. 不想要了

同一页点「一键卸载」，文件按字节还原，本次新增的文件删掉。

---

## 启动词 · lbwapi

`lbwapi` 是这个工作台的统一启动词：

- 写入的 11 份席位词包，激活页都指向这一个词
- 界面里的「启动验证」页可以直接试
- 程序内的激活门（ActivationGate）也认这个词，30 分钟会话过期、最多 100 个并发会话

它同时是社群的入口词——有问题进群问，见 [联系方式](#联系方式)。

---

## LBW 中转（可选）

不用中转也能完整跑「一键破甲」，中转只影响 Codex 这类需要在线模型的用法。

1. 左侧「LBW 中转」，填 Base URL 与 Key
2. 点「测一下」——会请求 `GET /v1/models` 验证连通与鉴权
3. 验证通过后可以看模型列表、用量，并一键复制 Codex 的 `config.toml` 片段

```
默认 Base：https://lbwapishop.online/v1
买 Key   ：https://lbwapishop.online/wallet
教程测评 ：https://lbwapi.online/
```

站上的接入教程（Cursor / Cherry Studio / LobeChat / NextChat）、六维实测评分和报错对照表都可以直接对照排查。

Key 默认**只存在内存里**，关掉进程就没了。想让程序记住，用命令行加 `--persist` 启动（写入 `~/.brewdesk/relay.json`，权限 0600）。

---

## 备份与回滚

写入前会在目标目录建 `.lbw-history/`（早期版本用的是另一个备份目录名，如果它还在就继续沿用，历史不断档）：

```
.lbw-history/
├─ <uuid>.json      事务快照：每个文件写入前/后的哈希、权限位、内容（或内容寻址的 blob）
└─ blobs/<sha256>   去重的内容备份
```

语义：

- `preview` 纯读，不落盘；`deploy` 才动手
- 每个文件走「临时文件 + 原子 rename」，中途失败按哈希校验回滚已写文件；回不去的标记 `partial` 并列出冲突文件
- `restore` 只在当前文件等于「写入后」或「写入前」状态时才执行；被别的程序改过就整体中止，绝不覆盖你的新改动
- 恢复后：新增文件删除、原有文件按字节还原；空目录和备份 blob 保留

---

## 安全与隐私

| 项 | 处理 |
| --- | --- |
| 监听地址 | 只绑 `127.0.0.1` / `::1`，不对局域网或公网暴露 |
| 跨站调用 | `/api/invoke` 只收 `application/json` + 同源 `Origin`，跨源预检一律 403，不返回 CORS 头 |
| 路径 | 静态服务做 `path.relative` 逃逸检查；写盘走引擎的 `guardPath`（拒绝符号链接、目录联接、硬链接） |
| 磁盘根 | 拒绝把磁盘根目录当配置根 |
| Key | 默认只在内存；`--persist` 才落盘（0600） |
| 外链 | 只允许 `github.com` / `lbwapishop.online` / `t.me` / `telegram.me` |
| 子进程 | 仅用于：系统目录选择框、打开文件/网址、引擎自带的工具探测 |
| 遥测 | 没有。启动时不联网；剪贴板只写不读；不碰浏览器 Cookie、聊天记录、密码 |

需要知道的一点：词包写进客户端之后，那些客户端自己会把对话发给对应厂商——这是它们的机制，跟本工具无关。

---

## 从源码运行

环境：Node.js >= 18（实测 v24.16.0）。依赖只有 `jsonc-parser` / `smol-toml` / `yaml`，已随仓库放在 `node_modules/`，**不需要 `npm install`**。

```bat
:: 双击
启动工作台.cmd

:: 或命令行
node server.js            :: 然后手动打开 http://127.0.0.1:8788
node server.js --open     :: 自动打开浏览器
node server.js --persist  :: 额外把中转配置存到 ~/.brewdesk/relay.json（0600）
```

改端口 / 改数据目录：

```bat
set BREWDESK_PORT=9000 && node server.js
set BREWDESK_HOME=D:\lbw-data && node server.js
```

自检页（报障时截图给客服）：

```
http://127.0.0.1:8788/api/diagnostics
```

---

## 自己打包

```bash
python tools/build_release.py
```

产物在 `release/LBW-Workbench-<version>-win-x64/`，压缩后记录 SHA-256。打包会剔除 `tools/`、开发文档与未引用素材，并内置 `node/node.exe`。

其它维护脚本（都是幂等的，可重复执行）：

| 脚本 | 用途 |
| --- | --- |
| `tools/retint.py` | 配色重映射（HSL 色相族映射），`--restore` 还原 |
| `tools/lightify.py` | 深色 → 白底主题，`--restore` 反向 |
| `tools/rebrand.py` | 品牌与联系方式替换 |
| `tools/switch_word.py` | 切换启动词（词包 / 路由 / 激活页 / 提示同步） |
| `tools/make_logo.py` | 从源图生成 `logo.png` / `logo.ico` 多尺寸 |

---

## 目录结构

```
.
├─ server.js                 本地 HTTP 服务（对应原 Electron 主进程的 IPC 表）
├─ 启动工作台.cmd            双击启动
├─ package.json
├─ node_modules/             三个依赖（随仓库，免安装）
├─ assets/                   图标与插画
├─ src/
│  ├─ bridge.js              浏览器侧的 preload 等价物
│  ├─ lib/                   引擎：词包 / 席位 / 事务 / 激活门 / 中转 / 工作流 / 上游技能
│  │  └─ packs/              全部词包正文（席位 / 路由 / 80 条叶子 / 工作流）
│  ├─ shared/workbench-core.js  任务契约 / 评估 / diff
│  └─ workbench/             界面
├─ resources/
│  ├─ toolbox/               16 个本地工具 + MCP 服务
│  └─ upstream-skills/       上游技能库快照（gzip bundle + catalog）
└─ tools/                    换肤、换牌子、打包脚本
```

想改词包就改 `src/lib/packs/`；想改界面就改 `src/workbench/`。

---

## 常见问题

**页面打不开** — 看黑色窗口有没有报错。开着 Clash / V2Ray 之类代理时，把 `127.0.0.1` 和 `localhost` 设为直连，否则会被代理拦掉。

**端口 8788 被占用** — 不用管，会自动往后找并在窗口里提示实际端口；想固定：`set BREWDESK_PORT=8899 && node server.js`。

**装完没生效** — 目标客户端必须**完全退出再打开**，它只在启动时读配置。

**页面白屏** — `Ctrl + F5` 强制刷新。

**安全软件弹窗** — 目录选择框用的是系统自带 PowerShell（`System.Windows.Forms`），放行即可；除此之外不会拉起别的进程。

**日志在哪** — `C:\Users\<用户名>\.brewdesk\logs\server-<日期>.log`。

**卸载** — 界面里对每个装过的客户端点「一键卸载」→ 删掉整个文件夹 → 如果用过工具箱或 `--persist`，再删掉 `C:\Users\<用户名>\.brewdesk`。

---

### 接了 LBW 中转却用不了？

装好客户端只是第一步，还得把 API 填对。这部分常见问题单独整理了一份：

**[客户端接入与排错](docs/CLIENT-SETUP.md)**

覆盖：

- **`CONTEXT_WINDOW_EXCEEDED`** — 最常见，客户端不认识模型名就按 8K 算，实际是 100 万。附一键工具和手动配置两套解法
- **同名模型冲突** — 多个服务商都有 `deepseek-flash` 时怎么分辨、怎么清掉
- **API 地址要带 `/v1`** — 少一段就 404
- **速度慢的原因** — 上游每次注入约 6300 token，流式 vs 非流式的实测差异
- **报错对照表** — 401 / 404 / model not found / 429 分别怎么处理

一键配置工具（双击即用）：

| 客户端 | 工具 |
| --- | --- |
| Pi | [LBW-Pi-Start.bat](https://lbwapi.online/pi/LBW-Pi-Start.bat) · [清理冲突](https://lbwapi.online/pi/LBW-Pi-Clean.bat) |
| DeepSeek Harness | [LBW-DSH-Setup.bat](https://lbwapi.online/pi/LBW-DSH-Setup.bat) |
| 诊断报告 | [LBW-Pi-diagnose.bat](https://lbwapi.online/pi/LBW-Pi-diagnose.bat) |

图文版教程：<https://lbwapi.online/beginner/>

---

## 联系方式

| 渠道 | 地址 |
| --- | --- |
| TG 频道 | [t.me/lbwapi](https://t.me/lbwapi) |
| TG 私聊 | [@jiali66888](https://t.me/jiali66888) |
| 站点 | [lbwapishop.online](https://lbwapishop.online) |
| 评测 / 教程站 | [lbwapi.online](https://lbwapi.online/) |
| Key 购买 | [lbwapishop.online/wallet](https://lbwapishop.online/wallet) |

有问题、要定制、要闭源版本，直接找管理。

---

## 许可与致谢

本项目以 MIT 许可发布，见 [LICENSE](LICENSE)。

- 界面主题、品牌、本地运行方式改造：Copyright (c) 2026 LBW
- 上游基础项目（MIT）：[3641397194-wq/gpt6-Astra](https://github.com/3641397194-wq/gpt6-Astra)，Copyright (c) 2026 3641397194-wq
- 随包技能库：[morluto/rea](https://github.com/morluto/rea)（MIT）、[zhaoxuya520/reverse-skill](https://github.com/zhaoxuya520/reverse-skill)（MIT，其中 CTF-Sandbox-Orchestrator 为 GPL-3.0，src-hunter 为独立 MIT），各自许可证与声明按原样保留

第三方组件清单见发行包内的《第三方组件与许可.txt》，许可证全文在 `licenses/`。

**免责声明**：本工具只做本机配置文件管理，不修改任何客户端二进制，也不代理、不破解任何服务。写入的词包由各客户端自行决定是否加载；使用前请自行确认符合你所在地区的法律法规与所用服务的条款。
