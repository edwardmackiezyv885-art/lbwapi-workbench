"""品牌与联系方式替换：冷咖啡 → LBW，QQ 群 → TG，coldcoffeeai.com → lbwapishop.online。

原则：
1. 只改界面层与中转层的展示文案；
2. 真正的启动词「冷咖啡」必须逐字保留（它在词包正文、激活门、复制按钮里都写死了），
   所以这里只替换明确的词组，不做「冷咖啡」→「LBW」的全局替换；
3. 词包正文（src/lib/packs/**）不改，避免改变部署出去的功能内容。
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

FILES = [
    "src/workbench/index.html",
    "src/workbench/workbench.js",
    "src/workbench/newbie.js",
    "src/workbench/pack-controls.js",
    "src/workbench/upstream-skills-view.js",
    "src/workbench/workbench.css",
    "src/shared/workbench-core.js",
    "server.js",
    "src/lib/relay-adapter.js",
]

RULES = [
    # ---- 品牌（长的先来，避免被短规则截断）
    ("冷咖啡破甲工作台", "LBW 破甲工作台"),
    ("冷咖啡漫画头像", "LBW 头像"),
    ("冷咖啡原创黑白漫画人物插画", "LBW 原创插画"),
    ("冷咖啡 / 越狱 · 破甲", "LBW / 越狱 · 破甲"),
    ("冷咖啡 / 中转服务", "LBW / 中转服务"),
    ("冷咖啡中转", "LBW 中转"),
    ("冷咖啡社群", "LBW 社群"),
    ("冷咖啡内置工作流介绍", "LBW 内置工作流介绍"),
    ("冷咖啡内置工作流", "LBW 内置工作流"),
    ("冷咖啡在线工作流", "LBW 在线工作流"),
    ("冷咖啡工作流", "LBW 工作流"),
    ("冷咖啡桌面编排器", "LBW 桌面编排器"),
    ("冷咖啡满配", "LBW 满配"),
    ("冷咖啡 API", "LBW API"),
    ("为冷咖啡设计", "为 LBW 设计"),
    ("品牌：冷咖啡", "品牌：LBW"),
    ("# 冷咖啡 · 任务契约", "# LBW · 任务契约"),
    ("冷咖啡。", "LBW。"),
    ("冷咖啡-${", "LBW-${"),
    ("冷咖啡-", "LBW-"),

    # ---- 联系方式
    ("进一群 1057540028、二群 1077074552、三群 618179023，找管理。",
     "TG 频道 t.me/lbwapi，私聊 @jiali66888，找管理。"),
    ("进下面三个群找管理", "在 TG 上找管理"),
    ("进 QQ 群找管理", "进 TG 找管理"),
    ("进群找管理", "找 TG 管理"),
    ("三个 QQ 群号", "TG 频道"),
    ("QQ 群二维码", "TG 频道"),
    ("QQ 群", "TG"),
    ("QQ群", "TG"),
    ("复制群号", "复制"),
    ("群号", "账号"),
    ("1057540028", "@jiali66888"),
    ("1077074552", "https://t.me/lbwapi"),
    ("618179023", "https://t.me/lbwapi"),

    # ---- 站点
    ("https://coldcoffeeai.com/v1", "https://lbwapishop.online/v1"),
    ("https://coldcoffeeai.com/", "https://lbwapishop.online/wallet"),
    ("coldcoffeeai.com", "lbwapishop.online"),
]

# 这些位置必须是「冷咖啡」，替换后统一补成带书名号的形式，避免被误改
PROTECTED = [
    ("<strong>冷咖啡</strong>", "<strong>「冷咖啡」</strong>"),
]


def main():
    total = 0
    for rel in FILES:
        path = ROOT / rel
        if not path.exists():
            print(f"MISS  {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        hits = 0
        for old, new in PROTECTED + RULES:
            n = text.count(old)
            if n:
                text = text.replace(old, new)
                hits += n
        if text != original:
            path.write_text(text, encoding="utf-8")
        total += hits
        print(f"{rel:44} 替换 {hits}")
    print(f"\n完成：共 {total} 处")


if __name__ == "__main__":
    main()
