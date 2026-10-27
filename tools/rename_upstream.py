"""清掉最后一批对客户可见的 coldcoffee 命名。

改名清单（都用「新名优先、旧名兜底」的方式，升级用户的旧数据不会失效）：
  .coldcoffee-upstream  → .lbw-upstream
  .coldcoffee-preserved → .lbw-preserved
  coldcoffee-rea (MCP)  → lbw-rea
  coldcoffee-rea-mcp    → lbw-rea-mcp
  coldcoffee-toolbox    → lbw-toolbox
  .coldcoffee-ready.json→ .lbw-ready.json
  素材文件名            → hero-art.png / hero-bg.jpg
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
changed = []


def patch(rel, pairs):
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    before = t
    for old, new in pairs:
        if old in t:
            t = t.replace(old, new)
    if t != before:
        p.write_text(t, encoding="utf-8")
        changed.append(rel)
        print(f"ok   {rel}")
    else:
        print(f"skip {rel}（无命中）")


# ------------------------------------------------- 1. 上游目录：新名优先 + 旧名兜底
patch("src/lib/upstream-skills.js", [
    ("const SERVER = 'coldcoffee-rea';",
     "const SERVER = 'lbw-rea';\n"
     "const UPSTREAM_DIR = '.lbw-upstream';\n"
     "const LEGACY_UPSTREAM_DIR = '.coldcoffee-upstream';\n"
     "\n"
     "// 新装用 .lbw-upstream；老客户升级后旧目录还在、新目录还没建时，继续用旧的\n"
     "function upstreamBase(root) {\n"
     "  const next = path.join(root, UPSTREAM_DIR);\n"
     "  if (fs.existsSync(next)) return next;\n"
     "  const legacy = path.join(root, LEGACY_UPSTREAM_DIR);\n"
     "  if (fs.existsSync(legacy)) return legacy;\n"
     "  return next;\n"
     "}"),
    ("  const launcher = path.join(root, '.coldcoffee-upstream', 'rea-launcher.cjs');",
     "  const launcher = path.join(upstreamBase(root), 'rea-launcher.cjs');"),
    ("  const base = path.join(root, '.coldcoffee-upstream');",
     "  const base = upstreamBase(root);"),
    ("`.coldcoffee-preserved/${digest(relative)}.bin`", "`.lbw-preserved/${digest(relative)}.bin`"),
    ("'REA 需要工具时使用 coldcoffee-rea MCP；", "'REA 需要工具时使用 lbw-rea MCP；"),
])

patch("src/lib/upstream-rea-runtime.js", [
    ("  return launcher.layoutOf(path.join(path.resolve(root), '.coldcoffee-upstream'));",
     "  const next = path.join(path.resolve(root), '.lbw-upstream');\n"
     "  const legacy = path.join(path.resolve(root), '.coldcoffee-upstream');\n"
     "  return launcher.layoutOf(fs.existsSync(next) || !fs.existsSync(legacy) ? next : legacy);"),
])

patch("src/workbench/upstream-skills-view.js", [
    ("写入所选软件的 .coldcoffee-upstream 目录", "写入所选软件的 .lbw-upstream 目录"),
])

# ------------------------------------------------- 2. MCP 名称与导出文件名
patch("src/lib/upstream-config.js", [("const id = 'coldcoffee-rea-mcp';", "const id = 'lbw-rea-mcp';")])

patch("src/lib/upstream/rea-launcher.cjs", [("'.coldcoffee-ready.json'", "'.lbw-ready.json'")])

patch("server.js", [
    ("        'coldcoffee-toolbox': {", "        'lbw-toolbox': {"),
    ("`coldcoffee-${task.id}.json`", "`lbw-${task.id}.json`"),
    ("'coldcoffee-toolbox-SKILL.md'", "'lbw-toolbox-SKILL.md'"),
])

patch("src/workbench/toolbox-view.js", [
    ("connection.mcpServers['coldcoffee-toolbox']", "connection.mcpServers['lbw-toolbox']"),
])

# ------------------------------------------------- 3. 素材改名
for old, new in [("coldcoffee-manga-v4.png", "hero-art.png"), ("coldcoffee-manga-v5.jpg", "hero-bg.jpg")]:
    src = ROOT / "assets" / old
    dst = ROOT / "assets" / new
    if src.exists() and not dst.exists():
        src.rename(dst)
        print(f"ok   assets/{old} -> {new}")

patch("src/workbench/index.html", [("assets/coldcoffee-manga-v4.png", "assets/hero-art.png")])
patch("src/workbench/newbie.css", [("assets/coldcoffee-manga-v5.jpg", "assets/hero-bg.jpg")])

print(f"\n改动 {len(changed)} 个文件")
