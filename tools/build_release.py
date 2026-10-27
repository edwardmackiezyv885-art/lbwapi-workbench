"""
构建客户可直接使用的便携包。

产物：
  release/LBW-Workbench-<版本>-win-x64/      ← 解压即用，内置 Node 运行时
  release/LBW-Workbench-<版本>-win-x64.zip   ← 发给客户的文件

设计取舍：
- 内置 node.exe：客户不用装任何环境，双击就能跑（体积 +88MB，压缩后约 +30MB）
- 不打包 tools/（开发脚本）、逆向报告、原作者文档与旧品牌素材
- 附带 MIT 许可与第三方组件声明，内含 Node.js 官方 LICENSE
"""
import json
import os
import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODE_EXE = Path(r"C:\Program Files\nodejs\node.exe")

VERSION = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
PKG_NAME = f"LBW-Workbench-{VERSION}-win-x64"
RELEASE = ROOT / "release"
OUT = RELEASE / PKG_NAME

# 需要原样带进包的目录 / 文件
INCLUDE_DIRS = ["src", "assets", "node_modules"]
INCLUDE_RESOURCES = ["toolbox", "upstream-skills"]   # docs 是原作者旧品牌截图，不带
INCLUDE_FILES = ["server.js", "package.json"]

LAUNCH_CMD = r"""@echo off
chcp 65001 >nul
title LBW 破甲工作台
cd /d "%~dp0"
set "PORT=8788"
set "URL=http://127.0.0.1:%PORT%/src/workbench/index.html"

rem 已经在跑就直接开页面，避免重复启动占端口
powershell -NoProfile -Command "try{$null=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 'http://127.0.0.1:%PORT%/api/health';exit 0}catch{exit 1}"
if not errorlevel 1 (
  echo   工作台已经在运行，正在打开页面……
  start "" "%URL%"
  timeout /t 2 >nul
  exit /b 0
)

set "NODE=%~dp0node\node.exe"
if not exist "%NODE%" set "NODE=node"

"%NODE%" --version >nul 2>nul
if errorlevel 1 (
  echo.
  echo   没有找到可用的 Node 运行时。
  echo   请确认 node\node.exe 还在，或安装 Node.js 18+ 后重试。
  echo.
  pause
  exit /b 1
)

echo.
echo   LBW 破甲工作台 %VERSION%
echo   浏览器会自动打开；这个窗口关掉 = 停止服务。
echo.
"%NODE%" server.js --open
pause
"""

STOP_CMD = r"""@echo off
chcp 65001 >nul
title LBW 破甲工作台 · 停止
set "PORT=8788"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c=Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue; if($c){ $c.OwningProcess | Sort-Object -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }; Write-Host '已停止工作台（端口 %PORT%）' } else { Write-Host '工作台当前没有在运行' }"
timeout /t 2 >nul
"""

USAGE = """LBW 破甲工作台 {ver}  ·  Windows x64 便携版
================================================================

一、这是什么
----------------------------------------------------------------
把各个 AI 客户端（Codex / Claude Code / Cursor / Gemini / DeepSeek Harness /
GLM / Grok / 豆包 / WorkBuddy / MiMo / Kimi）的工作词包与技能，按各自客户端的
加载规则写进本机用户配置目录，并保留逐字节备份、随时可以撤回。

另外还带：API 中转接入、五档工作模式、工作流引擎、IDA 中文与 MCP 工具、
16 个本地工具箱程序。

二、怎么启动
----------------------------------------------------------------
1. 双击「启动工作台.cmd」
2. 浏览器会自动打开页面：
   http://127.0.0.1:8788/src/workbench/index.html
   没有自动打开，就把上面这一行复制到浏览器地址栏
3. 那个黑色窗口关掉 = 服务停止；也可以用「停止工作台.cmd」
   重复双击启动不会开出第二份，只会把页面再打开一次

不需要安装 Node.js —— node\\node.exe 已经内置在包里。
不需要管理员权限。

三、第一次用：一键破甲
----------------------------------------------------------------
1. 左侧点「一键破甲」，软件会自动识别本机装了哪些，勾上要装的
2. 点「预览」，先看清楚会改哪些文件（这一步只读，不写盘）
3. 点「写入」，原文件会自动备份到目标目录的 .lbw-history 里
4. 把对应软件完全退出再打开，在对话框里单独发一句：

        lbwapi

   注意：启动词是 lbwapi（大小写都认，前后不要加别的字）。
   发对了会回一段激活页。
5. 不想要了：同一页点「一键卸载」，文件会恢复到写入之前

四、中转（可选）
----------------------------------------------------------------
中转页填 API Base 与 Key → 点「测一下」→ 复制 Codex 配置。

    默认 Base：https://lbwapishop.online/v1
    买 Key   ：https://lbwapishop.online/wallet

Key 默认只放在内存里，关掉窗口就没了。
想让软件记住，用命令行加参数启动：node server.js --persist
（会写 ~/.brewdesk/relay.json，权限 0600）

五、常见问题
----------------------------------------------------------------
· 页面打不开
  先看黑色窗口有没有报错。开了 Clash / V2Ray 之类的代理时，
  要把 127.0.0.1 和 localhost 设为直连，否则会被代理拦掉。

· 端口 8788 被占用
  不用管，软件会自动往后找 8789、8790……并在黑色窗口里提示实际端口。
  想固定端口：set BREWDESK_PORT=8899  然后再启动。

· 要报障 / 让客服远程看
  浏览器打开：http://127.0.0.1:8788/api/diagnostics
  这一页就是一份自检报告（版本、端口、Node、11 个软件的识别情况、
  技能包是否完整、数据目录是否可写），截图发给客服即可。

· 日志在哪
  C:/Users/<你的用户名>/.brewdesk/logs/server-日期.log

· 页面白屏
  按 Ctrl + F5 强制刷新

· 装完没生效
  目标软件必须完全退出再打开，才会重新读取配置。

· 安全软件弹窗
  软件会用系统自带的 PowerShell 弹「选择文件夹」对话框（给高级模式用），
  放行即可。除此之外不会拉起别的进程。

六、隐私
----------------------------------------------------------------
· 没有任何遥测、统计上报；启动时不联网
· 剪贴板只写不读；不碰浏览器 Cookie、聊天记录、密码
· 唯一的对外请求：你填的中转站（只有用中转时）、本机 IDA（127.0.0.1）、
  你主动点开的外链
· 断网也能完整跑「一键破甲」

需要知道的一点：词包写进客户端之后，那些客户端自己会把对话发给对应厂商，
这是它们的机制，跟本工具无关。

七、卸载
----------------------------------------------------------------
1. 界面里对每个装过的软件点「一键卸载」（文件恢复到写入前）
2. 删掉整个文件夹
3. 如果用过工具箱或 --persist：删掉 C:\\Users\\<你的用户名>\\.brewdesk

八、环境要求
----------------------------------------------------------------
Windows 10 / 11 x64
内置 Node.js {nodever}
"""

LICENSE = """LBW 破甲工作台
================================================================

本程序基于 MIT 许可的开源项目改造（原作者 3641397194-wq，
原项目 https://github.com/3641397194-wq/gpt6-Astra），并按 MIT 条款继续分发。

Copyright (c) 2026 3641397194-wq
Copyright (c) 2026 LBW（界面主题、品牌与本地运行方式改造）

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

第三方组件见「第三方组件与许可.txt」，许可证全文在 licenses\\ 目录。
"""

THIRD_PARTY = """第三方组件与许可
================================================================
本软件在运行时使用了下列第三方组件。各自的许可证全文保存在 licenses\\ 目录。

1) Node.js {nodever}
   许可证：MIT
   用途：内置运行时（node\\node.exe）
   全文：licenses\\node-LICENSE.txt
   说明：Node.js 自身还集成了 V8、OpenSSL、ICU、zlib 等组件，
        完整清单见 Node.js 发行版附带的 LICENSE。

2) jsonc-parser 3.3.1
   许可证：MIT
   用途：Gemini settings.json 的无损（保留注释）修改
   全文：licenses\\jsonc-parser-LICENSE.md

3) smol-toml 1.9.0
   许可证：BSD-3-Clause
   用途：TOML 配置解析
   全文：licenses\\smol-toml-LICENSE

4) yaml 2.9.0
   许可证：ISC
   用途：YAML 配置解析
   全文：licenses\\yaml-LICENSE

5) REA（reverse engineering agent）
   许可证：MIT
   来源：https://github.com/morluto/rea
   形式：以「完整源码快照」形式随包附带在
        resources\\upstream-skills\\rea.bundle.json.gz
   说明：快照内含原项目的 THIRD_PARTY_NOTICES.md 与 licenses\\ 目录，
        第三方声明按原样保留。

6) reverse-skill（技能库）
   许可证：MIT（其中 CTF-Sandbox-Orchestrator 子目录为 GPL-3.0，
         src-hunter 为独立 MIT）
   来源：https://github.com/zhaoxuya520/reverse-skill
   形式：完整源码快照 resources\\upstream-skills\\reverse-skill.bundle.json.gz
   说明：GPL-3.0 组件的完整源码已随本包提供，符合其分发要求；
        各子项目许可声明按原样保留，未改写为原创。

7) ida-pro-mcp
   许可证：MIT
   来源：https://github.com/mrexodia/ida-pro-mcp
   形式：不随包分发。仅在用户点击「安装 IDA MCP 插件」时，
        由本机 Python 从上述地址下载安装，属于用户主动操作。

本软件不包含：Electron、Chromium、任何广告或统计 SDK。
"""


def copytree(src: Path, dst: Path):
    shutil.copytree(src, dst, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("*.log", "__pycache__", ".DS_Store"))


def main():
    if not NODE_EXE.exists():
        sys.exit(f"找不到 {NODE_EXE}")
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "node").mkdir(parents=True)
    (OUT / "licenses").mkdir()

    for name in INCLUDE_DIRS:
        copytree(ROOT / name, OUT / name)
    (OUT / "resources").mkdir()
    for name in INCLUDE_RESOURCES:
        copytree(ROOT / "resources" / name, OUT / "resources" / name)
    for name in INCLUDE_FILES:
        shutil.copy2(ROOT / name, OUT / name)

    shutil.copy2(NODE_EXE, OUT / "node" / "node.exe")
    node_ver = "24.16.0"

    def write(rel, text, newline="\r\n", bom=False):
        p = OUT / rel
        p.write_text(text.replace("\n", newline), encoding="utf-8-sig" if bom else "utf-8", newline="")

    write("启动工作台.cmd", LAUNCH_CMD.replace("%VERSION%", VERSION))
    write("停止工作台.cmd", STOP_CMD)
    write("使用说明.txt", USAGE.format(ver=VERSION, nodever=node_ver), bom=True)
    write("LICENSE.txt", LICENSE, bom=True)
    write("第三方组件与许可.txt", THIRD_PARTY.format(nodever=node_ver), bom=True)

    # 第三方许可证全文
    lic_src = ROOT / "licenses-src"
    if lic_src.exists():
        for f in lic_src.iterdir():
            if f.is_file():
                shutil.copy2(f, OUT / "licenses" / f.name)
    for pkg, name in [("jsonc-parser", "LICENSE.md"), ("smol-toml", "LICENSE"), ("yaml", "LICENSE")]:
        src = ROOT / "node_modules" / pkg / name
        if src.exists():
            shutil.copy2(src, OUT / "licenses" / f"{pkg}-{name}")

    # 统计
    files = list(OUT.rglob("*"))
    total = sum(f.stat().st_size for f in files if f.is_file())
    print(f"输出目录: {OUT}")
    print(f"文件数: {sum(1 for f in files if f.is_file())}   体积: {total / 1024 / 1024:.1f} MB")
    for entry in sorted(OUT.iterdir()):
        size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file()) if entry.is_dir() else entry.stat().st_size
        print(f"  {entry.name:<28} {size / 1024 / 1024:>7.1f} MB")


if __name__ == "__main__":
    main()
