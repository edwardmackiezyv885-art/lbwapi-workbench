"""
把客户给的 logo 做成可直接用于界面的资源：

  assets/logo.png   透明底、内容裁边、512×512
  assets/logo.ico   多尺寸图标（16/24/32/48/64/128/256），给浏览器标签页与窗口用

源图是「纯色 logo + 白底」，用反预乘（unmatting）把白底抠掉，
边缘的白色不会被裁出灰边。
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else None


def unmatt_white(img: Image.Image) -> Image.Image:
    """白色背景反预乘：alpha = 1 - min(r,g,b)/255，再把白色从颜色里除掉。"""
    img = img.convert("RGB")
    px = img.load()
    w, h = img.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            a = 1.0 - min(r, g, b) / 255.0
            if a <= 0.03:
                continue
            if a >= 0.97:
                dst[x, y] = (r, g, b, 255)
                continue
            # 从「白底上的半透明像素」还原纯色
            cr = (r - (1 - a) * 255) / a
            cg = (g - (1 - a) * 255) / a
            cb = (b - (1 - a) * 255) / a
            dst[x, y] = (
                max(0, min(255, round(cr))),
                max(0, min(255, round(cg))),
                max(0, min(255, round(cb))),
                max(0, min(255, round(a * 255))),
            )
    return out


def main():
    if not SRC or not SRC.exists():
        sys.exit("缺少源图路径参数")

    img = unmatt_white(Image.open(SRC))

    # 按 alpha 裁掉空白，再留 4% 边距
    box = img.getbbox()
    if box:
        img = img.crop(box)
    side = max(img.size)
    pad = round(side * 0.04)
    canvas = Image.new("RGBA", (side + pad * 2, side + pad * 2), (0, 0, 0, 0))
    canvas.paste(img, ((canvas.width - img.width) // 2, (canvas.height - img.height) // 2))

    logo = canvas.resize((512, 512), Image.LANCZOS)
    logo.save(ROOT / "assets" / "logo.png")
    print("logo.png", logo.size, (ROOT / "assets" / "logo.png").stat().st_size, "bytes")

    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    logo.save(ROOT / "assets" / "logo.ico", sizes=sizes)
    print("logo.ico", sizes, (ROOT / "assets" / "logo.ico").stat().st_size, "bytes")

    # 顺便输出一张深色底预览，方便肉眼确认没有白边
    preview = Image.new("RGBA", (512, 512), (8, 9, 11, 255))
    preview.alpha_composite(logo)
    preview.save(ROOT / "tools" / "_logo-preview-dark.png")
    print("preview", ROOT / "tools" / "_logo-preview-dark.png")


if __name__ == "__main__":
    main()
