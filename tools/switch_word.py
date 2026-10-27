"""把启动词从「冷咖啡」切换到 lbwapi。

同一个词在两种语义上被使用：
  1. 启动词（latch / 越狱词 / 听词）—— 必须换成 lbwapi
  2. 品牌名（冷咖啡工作台 / 夜班桌 / 席位名）—— 统一成 LBW

所以按「先具体后笼统」的顺序替换：先把启动词的各种写法精确换掉，
剩下的「冷咖啡」再统一当品牌改成 LBW，避免出现「lbwapi工作台」这种句子。

    python tools/switch_word.py --dry   只看规则命中次数
    python tools/switch_word.py         实际改写（原文件备份在 tools/_word-coldcoffee/）
"""
import argparse
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKUP = ROOT / "tools" / "_word-coldcoffee"
TARGETS = ["src", "server.js"]

# 顺序敏感：先精确匹配启动词，再兜底品牌
RULES = [
    # ---- 启动词的各种写法 ----
    ("启动词：`冷咖啡`", "启动词：`lbwapi`"),
    ("latch: `冷咖啡`", "latch: `lbwapi`"),
    ("听词：冷咖啡", "听词：lbwapi"),
    ("启动词 `冷咖啡`", "启动词 `lbwapi`"),
    ("越狱词只有一句：`冷咖啡`", "越狱词只有一句：`lbwapi`"),
    ("「冷咖啡」", "「lbwapi」"),
    ("单独发送冷咖啡", "单独发送 lbwapi"),
    ("冷咖啡已激活", "lbwapi 已激活"),
    ("冷咖啡无限制模式开启", "lbwapi 无限制模式开启"),
    ("写入冷咖啡入口段落", "写入 lbwapi 入口段落"),

    # ---- upstream 加载说明里的特例 ----
    ("保留原“冷咖啡”启动词、完整欢迎词与三个 QQ 群号。",
     "保留原欢迎词与联系人信息。切换后的启动词是 lbwapi。"),

    # ---- 代码字面量 ----
    ('ACTIVATION_WORD = "冷咖啡"', 'ACTIVATION_WORD = "lbwapi"'),
    ("text.trim()==='冷咖啡'", "text.trim()==='lbwapi'"),
    ("writeText('冷咖啡')", "writeText('lbwapi')"),
    ("copy('冷咖啡')", "copy('lbwapi')"),
    ("'已复制：冷咖啡'", "'已复制：lbwapi'"),
    ("后面的：冷咖啡", "后面的：lbwapi"),
    ("触发词：冷咖啡", "触发词：lbwapi"),
    ("trigger:'冷咖啡'", "trigger:'lbwapi'"),

    # ---- 兜底：剩下的都是品牌名 ----
    ("冷咖啡", "LBW"),
]

# 这些文件里「冷咖啡」出现在注释/说明中，同样适用兜底规则，无需例外


def files():
    out = []
    for target in TARGETS:
        path = ROOT / target
        if path.is_file():
            out.append(path)
            continue
        for p in path.rglob("*"):
            if p.is_file() and p.suffix in {".js", ".md", ".html", ".css", ".cjs"} and "node_modules" not in p.parts:
                out.append(p)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    grand = 0
    for path in files():
        text = path.read_text(encoding="utf-8")
        hits = 0
        new = text
        for old, rep in RULES:
            n = new.count(old)
            if n:
                new = new.replace(old, rep)
                hits += n
        if hits:
            grand += hits
            rel = path.relative_to(ROOT)
            print(f"{str(rel):<44} {hits:>3}", end="")
            if not args.dry:
                if not (BACKUP / rel).exists():
                    (BACKUP / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, BACKUP / rel)
                path.write_text(new, encoding="utf-8")
            print()
    print(f"\n合计 {grand} 处", "（dry-run，未写入）" if args.dry else "，已写入")


if __name__ == "__main__":
    main()
