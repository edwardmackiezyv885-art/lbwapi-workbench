# 更新日志

## 1.0.1 — 挂上评测 / 教程站

- 新增官方站点 [lbwapi.online](https://lbwapi.online/)：接入教程、六维实测评分、报错对照表
- 社群页新增直达入口，README 联系方式与中转说明同步
- 外链白名单放行 `lbwapi.online`（`coldbrew:open-external`）

## 1.0.0 — 首个公开版本

**核心**

- 11 个席位的一键破甲：Codex / Claude Code / Cursor / Gemini / DeepSeek Harness / Grok / GLM·ZCode / 豆包 / WorkBuddy / MiMo / Kimi
- 部署事务：预览 → 写入 → 校验 → 卸载，逐文件哈希 + 权限位备份，原子 rename，失败按哈希回滚
- 备份目录 `.lbw-history/`（内容寻址 blob 去重），旧备份目录自动沿用
- 完整技能树随包落盘（94 项技能 / 11,671 个文件），索引入口织入各客户端指令文件

**界面与交互**

- 白底简约主题，单一强调色 `#0f7b86`，去掉装饰插画与发光
- 全新品牌资源：透明底 logo、7 尺寸 ico
- 一键破甲 / LBW 中转 / LBW 社群 / 工具箱四个主入口

**能力**

- LBW 中转：Base URL + Key → 测连接 → 模型 / 用量 → 复制 Codex 配置
- 五档工作模式 + 任务契约（compose / evaluate）
- 工作流引擎：5 套模板，SSE 推事件
- IDA 9.x 简中界面安装 / 卸载；IDA MCP 写入 8 个客户端
- 原创工具箱：16 个本地工具 + MCP 服务 + AI 自动调用代理

**发行**

- Windows x64 便携包：内置 Node.js 24.16.0，免安装、免管理员权限
- 运行时能力：端口自动避让（8788 → 8789 …）、`/api/diagnostics` 自检页、日志落盘 `~/.brewdesk/logs/`
