"""把隐藏备份目录 .coldcoffee-history 换成 .lbw-history，并修掉 favicon 缓存。

兼容策略：
  读：两个目录都列，按 id 去重 —— 老客户升级后旧备份仍然能恢复
  写：优先 .lbw-history；只有旧目录存在且新目录还没有时才写旧目录（保持连续）

favicon：
  浏览器对 /favicon.ico 的缓存很顽固，因此页面里显式挂一个带版本号的 <link rel="icon">，
  同时把该路由改成 no-store。
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def patch(path, pairs, required=True):
    p = ROOT / path
    t = p.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in t:
            if required:
                sys.exit(f"{path}: 锚点未命中 -> {old[:60]!r}")
            continue
        t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print(f"{path:<44} ok")


# ---------------------------------------------------------------- 1. 事务引擎
patch("src/lib/seat-transactions.js", [
    (
        "const MAX_FILE = 64 * 1024 * 1024;",
        "const MAX_FILE = 64 * 1024 * 1024;\n"
        "const HISTORY_DIR = '.lbw-history';\n"
        "const LEGACY_HISTORY_DIR = '.coldcoffee-history';\n"
        "\n"
        "// 新装写 .lbw-history；老客户升级后旧目录还在时继续写旧的，避免历史断档\n"
        "function activeHistoryDir(root) {\n"
        "  if (fs.existsSync(within(root, HISTORY_DIR))) return HISTORY_DIR;\n"
        "  if (fs.existsSync(within(root, LEGACY_HISTORY_DIR))) return LEGACY_HISTORY_DIR;\n"
        "  return HISTORY_DIR;\n"
        "}",
    ),
    (
        "    return within(this.requireRoot(), `.coldcoffee-history/${id}.json`);",
        "    const root = this.requireRoot();\n"
        "    return within(root, `${activeHistoryDir(root)}/${id}.json`);",
    ),
    (
        "    return within(this.requireRoot(), `.coldcoffee-history/blobs/${digest}`);",
        "    const root = this.requireRoot();\n"
        "    return within(root, `${activeHistoryDir(root)}/blobs/${digest}`);",
    ),
    (
        """  history() {
    this.requireRoot();
    const dir = within(this.root, '.coldcoffee-history');
    if (!fs.existsSync(dir)) return [];
    return fs.readdirSync(dir).filter((name) => /^[a-f0-9-]{36}\\.json$/.test(name))
      .map((name) => JSON.parse(decode(read(within(this.root, '.coldcoffee-history/' + name)))))
      .sort((a, b) => b.at.localeCompare(a.at))
      .map((snapshot) => ({ id: snapshot.id, seat: snapshot.seat, at: snapshot.at, status: snapshot.status, files: snapshot.files.length }));
  }""",
        """  history() {
    this.requireRoot();
    const seen = new Map();
    for (const name of [HISTORY_DIR, LEGACY_HISTORY_DIR]) {
      const dir = within(this.root, name);
      if (!fs.existsSync(dir)) continue;
      for (const entry of fs.readdirSync(dir)) {
        if (!/^[a-f0-9-]{36}\\.json$/.test(entry)) continue;
        try {
          const snapshot = JSON.parse(decode(read(within(this.root, name + '/' + entry))));
          if (snapshot && snapshot.id && !seen.has(snapshot.id)) seen.set(snapshot.id, snapshot);
        } catch { /* 损坏的快照不阻断列表 */ }
      }
    }
    return [...seen.values()]
      .sort((a, b) => String(b.at).localeCompare(String(a.at)))
      .map((snapshot) => ({ id: snapshot.id, seat: snapshot.seat, at: snapshot.at, status: snapshot.status, files: snapshot.files.length }));
  }""",
    ),
])

# ---------------------------------------------------------------- 2. IDA MCP 备份
patch("src/lib/ida-mcp.js", [
    ('path.join(options.home || os.homedir(), ".coldcoffee-history", "ida-mcp")',
     'path.join(options.home || os.homedir(), ".lbw-history", "ida-mcp")'),
])

# ---------------------------------------------------------------- 3. 界面文案
patch("src/workbench/pack-controls.js", [
    ("原文件备份保存在目标目录的 .coldcoffee-history 内。",
     "原文件备份保存在目标目录的 .lbw-history 内。"),
])

# ---------------------------------------------------------------- 4. 客户文档
patch("tools/build_release.py", [
    ("原文件会自动备份到目标目录的 .coldcoffee-history 里",
     "原文件会自动备份到目标目录的 .lbw-history 里"),
    ("删掉这个文件夹", "删掉这个文件夹（连同各客户端配置目录里的 .lbw-history）"),
])

# ---------------------------------------------------------------- 5. favicon
patch("server.js", [
    ("res.writeHead(200, { 'Content-Type': 'image/x-icon', 'Cache-Control': 'public, max-age=86400' });",
     "res.writeHead(200, { 'Content-Type': 'image/x-icon', 'Cache-Control': 'no-store' });"),
])

patch("src/workbench/index.html", [
    ('<link rel="stylesheet" href="workbench.css">',
     '<link rel="icon" type="image/png" href="../../assets/logo.png?v=3">'
     '<link rel="apple-touch-icon" href="../../assets/logo.png?v=3">'
     '<link rel="stylesheet" href="workbench.css">'),
])

print("\n全部补丁完成")
