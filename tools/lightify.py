"""
深色 → 白底黑字。

不是简单反色：按「色彩角色」分别映射，才不至于把按钮文字、洗底、金色区块搞坏。

  近黑的底色（页面/面板）      → 白 / 极淡冷灰
  中性色（正文灰阶）           → 明度翻转（亮字变深字）
  极浅饱和色（彩色底上的字）   → 白
  主色青（亮）→ 深青（白底才够对比）
  主色青（深填充）→ 淡青洗底
  金色（付费/闭源）            → 深琥珀（深填充→淡琥珀洗底）
  绿（成功态）                 → 深绿
  半透明黑（遮罩/阴影）        → 保持黑
  半透明白（发丝线/高光）      → 半透明黑

原文件备份在 tools/_css-cyan-dark/，随时可回退：
    python tools/lightify.py --restore
"""
import argparse
import colorsys
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSS_FILES = sorted((ROOT / "src" / "workbench").glob("*.css")) + sorted((ROOT / "src" / "renderer").glob("*.css"))
BACKUP = ROOT / "tools" / "_css-cyan-dark"

NEUTRAL_HUE = 210 / 360.0


def hls(h, l, s):
    """注意参数序：h, l, s —— 与 colorsys.hls_to_rgb 一致。"""
    r, g, b = colorsys.hls_to_rgb(h, max(0.0, min(1.0, l)), max(0.0, min(1.0, s)))
    return tuple(max(0, min(255, round(v * 255))) for v in (r, g, b))


def to_light(r, g, b):
    """把深色主题下的一个颜色，翻译成白底黑字主题下语义等价的颜色。"""
    if (r, g, b) == (0, 0, 0):
        return (0, 0, 0)                      # 纯黑＝遮罩/阴影，白底上依然正确

    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    deg = h * 360.0

    # 1) 近黑的底 → 白
    if l < 0.12:
        return (252, 253, 255)

    # 2) 近白的一切（正文白字、淡青字、发丝线）→ 深灰字
    #    彩色底上的白字由 theme-light.css 单独刷回来
    if l >= 0.86:
        nl = 0.06 + (1.0 - l) * 0.55
        return hls(NEUTRAL_HUE, nl, 0.05)

    # 3) 中性灰阶：明度翻转
    if s < 0.22:
        nl = 0.04 + (1.0 - l) * 0.90
        return hls(NEUTRAL_HUE, nl, 0.04)

    # 4) 主色：青 / 蓝青
    if 158 <= deg <= 215:
        if l < 0.34:                          # 深填充 → 淡洗底
            return hls(deg / 360.0, 0.95, 0.45)
        if l < 0.55:                          # 中深 → 主色
            return hls(deg / 360.0, 0.38, min(0.95, s * 1.10))
        return hls(deg / 360.0, 0.33, min(0.95, s * 1.10))

    # 5) 金色
    if 28 <= deg < 62:
        if l < 0.34:
            return hls(deg / 360.0, 0.95, 0.55)
        return hls(deg / 360.0, 0.50, min(0.95, s))

    # 6) 绿 / 薄荷（成功态）
    if 115 <= deg < 158:
        if l < 0.34:
            return hls(deg / 360.0, 0.95, 0.40)
        return hls(deg / 360.0, 0.40, s)

    # 7) 其余（紫 / 红 / 洋红）：明度翻转
    return hls(deg / 360.0, 0.06 + (1.0 - l) * 0.88, s)


HEX6 = re.compile(r"#([0-9a-fA-F]{6})\b")
HEX3 = re.compile(r"#([0-9a-fA-F]{3})\b")
RGB_COMMA = re.compile(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(,\s*[\d.]+%?\s*)?\)")
RGB_SLASH = re.compile(r"rgb\(\s*(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})\s*/\s*([\d.]+%?)\s*\)")


def hex_sub(match, width):
    h = match.group(1)
    if width == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    nr, ng, nb = to_light(r, g, b)
    return "#{:02x}{:02x}{:02x}".format(nr, ng, nb)


def rgb_comma_sub(match):
    r, g, b = (int(match.group(i)) for i in (1, 2, 3))
    alpha = match.group(4) or ""
    nr, ng, nb = to_light(r, g, b)
    return f"{'rgba' if alpha else 'rgb'}({nr},{ng},{nb}{alpha})"


def rgb_slash_sub(match):
    r, g, b = (int(match.group(i)) for i in (1, 2, 3))
    alpha = match.group(4)
    nr, ng, nb = to_light(r, g, b)
    return f"rgb({nr} {ng} {nb} / {alpha})"


def transform(text):
    text = HEX6.sub(lambda m: hex_sub(m, 6), text)
    text = HEX3.sub(lambda m: hex_sub(m, 3), text)
    text = RGB_COMMA.sub(rgb_comma_sub, text)
    text = RGB_SLASH.sub(rgb_slash_sub, text)
    return text.replace("color-scheme:dark", "color-scheme:light").replace("color-scheme: dark", "color-scheme: light")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()

    if args.restore:
        if not BACKUP.exists():
            sys.exit("没有深色版备份")
        for src in BACKUP.glob("*.css"):
            for target in CSS_FILES:
                if target.name == src.name:
                    shutil.copyfile(src, target)
                    print("restored", target.name)
        return

    BACKUP.mkdir(parents=True, exist_ok=True)
    total = 0
    for path in CSS_FILES:
        text = path.read_text(encoding="utf-8")
        if not (BACKUP / path.name).exists():
            (BACKUP / path.name).write_text(text, encoding="utf-8")
        n = (len(HEX6.findall(text)) + len(HEX3.findall(text))
             + len(RGB_COMMA.findall(text)) + len(RGB_SLASH.findall(text)))
        new = transform(text)
        if new != text:
            path.write_text(new, encoding="utf-8")
        total += n
        print(f"{path.name:<28} 色值 {n}")
    print(f"共转换 {total} 处；深色版备份在 tools/_css-cyan-dark/")


if __name__ == "__main__":
    main()
