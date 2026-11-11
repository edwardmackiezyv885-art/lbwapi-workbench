# NOTICE · 来源与第三方组件

LBW Workbench · 本地破甲工作台

协议文本见 [LICENSE](LICENSE)（MIT）。本文件记录来源、改造范围与随包第三方组件，
不改变 LICENSE 的条款。

## 本仓库的来源与改造范围

- 上游基础项目（MIT）：[3641397194-wq/gpt6-Astra](https://github.com/3641397194-wq/gpt6-Astra)，Copyright (c) 2026 3641397194-wq
- 本仓库的改造部分（同样按 MIT 分发）：界面主题、品牌、本地运行方式，以及配置写入与字节级回滚的实现

## 随包第三方组件

| 组件 | 地址 | 许可 |
| --- | --- | --- |
| rea 技能库 | [morluto/rea](https://github.com/morluto/rea) | MIT |
| reverse-skill 技能库 | [zhaoxuya520/reverse-skill](https://github.com/zhaoxuya520/reverse-skill) | MIT（其中 CTF-Sandbox-Orchestrator 为 GPL-3.0，src-hunter 为独立 MIT） |

随包的 REA / reverse-skill 快照各自保留原许可证与声明，不因本仓库的 MIT 声明而改变。

第三方组件完整清单见发行包内的《第三方组件与许可.txt》，许可证全文在 `licenses/` 目录。

## 免责声明

本工具只做本机配置文件管理，不修改任何客户端二进制，也不代理、不破解任何服务。
写入的词包由各客户端自行决定是否加载；使用前请自行确认符合你所在地区的法律法规与所用服务的条款。
