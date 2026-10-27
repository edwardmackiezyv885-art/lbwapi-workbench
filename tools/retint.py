"""
CSS 主题重映射：把原版「暖红 + 金 + 暖白」的配色整体换成「电青 + 琥珀 + 冷白」。

做法：不逐条手改 436 个色值，而是按 HSL 做色相族映射，保留每个色值的明度 L，
因此对比度关系基本不变；同时把中性色统一往冷蓝方向偏一点。

    python tools/retint.py --dry-run      # 只看关键色的映射结果
    python tools/retint.py                # 实际改写（原文件备份到 tools/_css-original/）
    python tools/retint.py --restore      # 从备份还原
"""
import argparse
import colorsys
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSS_FILES = sorted((ROOT / "src" / "workbench").glob("*.css")) + sorted((ROOT / "src" / "renderer").glob("*.css"))
BACKUP = ROOT / "tools" / "_css-original"

NEUTRAL_TINT = 212.0 / 360.0   # 冷蓝灰
PRIMARY_HUE = 187.0            # 电青
ACCENT_HUE = 43.0              # 琥珀金（保留，作为付费/闭源色）
MINT_HUE = 158.0               # 成功绿
AZURE_HUE = 205.0              # 冷蓝
VIOLET_HUE = 220.0             # 紫蓝


def from_hls(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return tuple(max(0, min(255, round(v * 255))) for v in (r, g, b))


def retint(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    deg = h * 360.0

    if l <= 0.02 or l >= 0.985:          # 纯黑/纯白保持
        return (r, g, b)

    if s < 0.12:                          # 中性：往冷蓝灰偏
        if l < 0.10:
            ns = max(0.30, s)             # 极暗底色 → 蓝黑
        elif l > 0.80:
            ns = max(0.06, s)             # 浅色文字 → 冷白
        else:
            ns = min(0.16, max(0.10, s * 1.6))
        return from_hls(NEUTRAL_TINT, l, ns)

    # 金色单独保护：暖橙（tan）饱和度低，仍是主色族的过渡色
    if 30 <= deg < 75 and s > 0.35:
        return from_hls(ACCENT_HUE / 360.0, l, min(0.95, s))

    if deg < 45 or deg >= 300:            # 主色族（暖红/洋红/橙）→ 电青
        if l >= 0.88:                     # 极浅：淡青文字/底色
            nh, ns = PRIMARY_HUE, min(s * 0.45, 0.50)
        elif l >= 0.60:                   # 亮：主按钮、强调
            nh, ns = PRIMARY_HUE - 1, min(s * 0.80, 0.80)
        elif l >= 0.32:                   # 中：链接、边框
            nh, ns = PRIMARY_HUE + 1, min(s * 0.95, 0.92)
        else:                             # 深：深色填充背景
            nh, ns = PRIMARY_HUE + 7, min(s * 0.95, 0.88)
        return from_hls(nh / 360.0, l, ns)

    if 45 <= deg < 75:                    # 残留金色（已在上方处理高饱和）
        return from_hls(ACCENT_HUE / 360.0, l, min(0.95, s))

    if 75 <= deg < 170:                   # 绿 → 薄荷
        return from_hls(MINT_HUE / 360.0, l, s)

    if 170 <= deg < 210:                  # 青/蓝 → 天蓝
        return from_hls(AZURE_HUE / 360.0, l, s)

    return from_hls(VIOLET_HUE / 360.0, l, s)


HEX6 = re.compile(r"#([0-9a-fA-F]{6})\b")
HEX3 = re.compile(r"#([0-9a-fA-F]{3})\b")
RGB_COMMA = re.compile(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(,\s*[\d.]+%?\s*)?\)")
RGB_SLASH = re.compile(r"rgb\(\s*(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})\s*/\s*([\d.]+%?)\s*\)")


def convert_hex(match, width):
    h = match.group(1)
    if width == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    nr, ng, nb = retint(r, g, b)
    if (nr, ng, nb) == (r, g, b):
        return match.group(0)
    return "#{:02x}{:02x}{:02x}".format(nr, ng, nb)


def convert_rgb_comma(match):
    r, g, b = (int(match.group(i)) for i in (1, 2, 3))
    alpha = match.group(4) or ""
    nr, ng, nb = retint(r, g, b)
    name = "rgba" if alpha else "rgb"
    return f"{name}({nr},{ng},{nb}{alpha})"


def convert_rgb_slash(match):
    r, g, b = (int(match.group(i)) for i in (1, 2, 3))
    alpha = match.group(4)
    nr, ng, nb = retint(r, g, b)
    return f"rgb({nr} {ng} {nb} / {alpha})"


def transform(text):
    text = HEX6.sub(lambda m: convert_hex(m, 6), text)
    text = HEX3.sub(lambda m: convert_hex(m, 3), text)
    text = RGB_COMMA.sub(convert_rgb_comma, text)
    text = RGB_SLASH.sub(convert_rgb_slash, text)
    return text


DRY = {
    "#e53543": "主强调（按钮/链接）",
    "#ef4348": "亮强调",
    "#4b1318": "深色填充",
    "#2a1218": "更深填充",
    "#f0c14a": "金色（保留）",
    "#f1ede7": "正文暖白",
    "#0a090a": "页面底色",
    "#131113": "面板底色",
    "#353035": "分割线",
    "#a09a9f": "次要文字",
    "#ffd8d9": "反白浅字",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()

    if args.restore:
        if not BACKUP.exists():
            sys.exit("没有备份可还原")
        for src in BACKUP.glob("*.css"):
            target = next((p for p in CSS_FILES if p.name == src.name), None)
            if target:
                shutil.copyfile(src, target)
                print("restored", target.relative_to(ROOT))
        return

    if args.dry_run:
        print(f"{'原色':10} {'新色':10} 说明")
        for hexv, note in DRY.items():
            r, g, b = (int(hexv[i:i + 2], 16) for i in (1, 3, 5))
            nr, ng, nb = retint(r, g, b)
            print(f"{hexv:10} #{nr:02x}{ng:02x}{nb:02x}   {note}")
        return

    BACKUP.mkdir(parents=True, exist_ok=True)
    total = 0
    for path in CSS_FILES:
        text = path.read_text(encoding="utf-8")
        backup = BACKUP / path.name
        if not backup.exists():
            backup.write_text(text, encoding="utf-8")
        before = len(HEX6.findall(text)) + len(HEX3.findall(text)) + len(RGB_COMMA.findall(text)) + len(RGB_SLASH.findall(text))
        new = transform(text)
        if new != text:
            path.write_text(new, encoding="utf-8")
        total += before
        print(f"{path.relative_to(ROOT)}  替换色值 {before}")
    print(f"完成，共处理 {total} 处色值；原文件备份在 tools/_css-original/")


if __name__ == "__main__":
    main()

