"""把界面里的联系方式、品牌位、社区卡片换成 LBW 的 TG 入口。

只做结构性替换（多行块 / 整行函数），品牌字样的批量替换在 tools/rebrand.py。
重复执行安全：找不到锚点就跳过并提示，不会写坏文件。
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
changed = []


def replace_once(rel, old, new, label):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if new in text and old not in text:
        print(f"skip  {rel} :: {label}（已是新内容）")
        return
    if old not in text:
        print(f"MISS  {rel} :: {label}（锚点没找到）")
        return
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    changed.append(f"{rel} :: {label}")
    print(f"ok    {rel} :: {label}")


def replace_line(rel, prefix, new_lines, label):
    path = ROOT / rel
    lines = path.read_text(encoding="utf-8").split("\n")
    hit = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if not hit:
        print(f"MISS  {rel} :: {label}")
        return
    i = hit[0]
    if any(new_lines[0].startswith(p) for p in [prefix]):
        pass
    lines[i:i + 1] = new_lines
    path.write_text("\n".join(lines), encoding="utf-8")
    changed.append(f"{rel} :: {label}")
    print(f"ok    {rel} :: {label}")


# ---------------------------------------------------------------- 1. 社区数据源
replace_once(
    "src/shared/workbench-core.js",
    """  const COMMUNITY = [
    {name:'一群',value:'1057540028',image:'qq-group-1.jpg'},
    {name:'二群',value:'1077074552',image:'qq-group-2.jpg'},
    {name:'三群',value:'618179023',image:'qq-group-3.jpg'}
  ];""",
    """  const COMMUNITY = [
    {name:'TG 频道',value:'https://t.me/lbwapi',href:'https://t.me/lbwapi',action:'open'},
    {name:'TG 私聊',value:'@jiali66888',href:'https://t.me/jiali66888',action:'open'}
  ];""",
    "COMMUNITY 数据源",
)

replace_once(
    "server.js",
    """const COMMUNITY = {
  qq: [
    { name: "一群", value: "1057540028" },
    { name: "二群", value: "1077074552" },
    { name: "三群", value: "618179023" },
  ],
};""",
    """const COMMUNITY = {
  tg: [
    { name: "TG 频道", value: "https://t.me/lbwapi", href: "https://t.me/lbwapi" },
    { name: "TG 私聊", value: "@jiali66888", href: "https://t.me/jiali66888" },
  ],
};""",
    "meta.community",
)

# ---------------------------------------------------------------- 2. 外链白名单
replace_once(
    "server.js",
    "if (!/^https:\\/\\/(?:github\\.com|(?:www\\.)?coldcoffeeai\\.com)(\\/|$)/i.test(url)) throw new Error('这个链接打不开');",
    "if (!/^https:\\/\\/(?:github\\.com|(?:www\\.)?lbwapishop\\.online|t\\.me|telegram\\.me)(\\/|$)/i.test(url)) throw new Error('这个链接打不开');",
    "外链白名单",
)

# ---------------------------------------------------------------- 3. 中转页联系行
replace_once(
    "src/workbench/workbench.js",
    """  $('relay-groups').replaceChildren(...core.COMMUNITY.map(group=>{
    const row=document.createElement('div');row.className='relay-group-row';const info=document.createElement('div');
    const name=document.createElement('strong');name.textContent=group.name;const num=document.createElement('code');num.textContent=group.value;
    info.append(name,num);row.append(info,button('复制群号',()=>copy(group.value)));return row;
  }));""",
    """  $('relay-groups').replaceChildren(...core.COMMUNITY.map(item=>{
    const row=document.createElement('div');row.className='relay-group-row';const info=document.createElement('div');
    const name=document.createElement('strong');name.textContent=item.name;const num=document.createElement('code');num.textContent=item.value;
    info.append(name,num);row.append(info,button('打开',()=>openLink(item.href)));return row;
  }));""",
    "中转页联系行",
)

# ---------------------------------------------------------------- 4. 社区页渲染
replace_line(
    "src/workbench/workbench.js",
    "function renderCommunity()",
    [
        "function openLink(url){if(window.coldbrew?.openExternal)return window.coldbrew.openExternal(url).catch(e=>toast(e.message));window.open(url,'_blank','noopener,noreferrer');return Promise.resolve();}",
        "function renderCommunity(){$('community').replaceChildren(...core.COMMUNITY.map((item,index)=>{const card=document.createElement('article');card.className='community-card';const label=document.createElement('div');label.className='eyebrow';label.textContent=`LBW / 0${index+1}`;const title=document.createElement('h2');title.textContent=item.name;const jump=button(`打开 ${item.name}`,()=>openLink(item.href),'community-link');jump.setAttribute('aria-label',`打开${item.name}`);const row=document.createElement('div');row.className='group-number';const value=document.createElement('code');value.textContent=item.value;row.append(value,button('复制',()=>copy(item.value)));card.append(label,title,jump,row);return card;}));}",
    ],
    "renderCommunity",
)

# ---------------------------------------------------------------- 5. 社区页文案
replace_once(
    "src/workbench/index.html",
    """<section id="page-community" class="page"><div class="page-heading"><div class="eyebrow closed-kicker">闭源 · 定制</div><h1>需要闭源破甲，或者定制破甲，进群找管理。</h1><p>开源破甲在「一键破甲」里自己装。闭源破甲和定制破甲，进下面三个群找管理。Key 还是去 coldcoffeeai.com 买。用法和售后也在群里问。</p></div><div id="community" class="community-grid"></div><div class="community-footer"><img class="logo brand-avatar" src="../../assets/brand-avatar-v4.png" alt="冷咖啡漫画头像" width="40" height="40"><div><h2>冷咖啡中转</h2><p>Key 在官网买。贴上就能用。</p></div></div></section>""",
    """<section id="page-community" class="page"><div class="page-heading"><div class="eyebrow closed-kicker">闭源 · 定制</div><h1>需要闭源破甲，或者定制破甲，直接找管理。</h1><p>开源破甲在「一键破甲」里自己装。闭源破甲、定制破甲在 TG 上谈：频道 t.me/lbwapi，私聊 @jiali66888。Key 去 lbwapishop.online 钱包页买。用法和售后也在 TG 问。</p></div><div id="community" class="community-grid"></div><div class="community-footer"><img class="logo brand-avatar" src="../../assets/brand-avatar-v4.png" alt="LBW 头像" width="40" height="40"><div><h2>LBW 中转</h2><p>Key 在 lbwapishop.online 买。贴上就能用。</p></div></div></section>""",
    "社区页文案",
)

# ---------------------------------------------------------------- 6. 小白页联系按钮
replace_once(
    "src/workbench/index.html",
    """<div class="newbie-groups"><button type="button" data-qq="1057540028">一群 1057540028</button><button type="button" data-qq="1077074552">二群 1077074552</button><button type="button" data-qq="618179023">三群 618179023</button><button id="newbie-groups" type="button">二维码</button></div>""",
    """<div class="newbie-groups"><button type="button" data-tg="https://t.me/lbwapi">TG 频道</button><button type="button" data-tg="https://t.me/jiali66888">TG 私聊 @jiali66888</button><button id="newbie-groups" type="button">联系方式</button></div>""",
    "小白页联系按钮",
)

replace_once(
    "src/workbench/newbie.js",
    """  stage.querySelectorAll('[data-qq]').forEach((button) => {
    button.addEventListener('click', () => {
      if (typeof copy === 'function') copy(button.dataset.qq);
      else toast(button.dataset.qq);
    });
  });""",
    """  stage.querySelectorAll('[data-tg]').forEach((button) => {
    button.addEventListener('click', async () => {
      const url = button.dataset.tg;
      if (window.coldbrew?.openExternal) {
        try { await window.coldbrew.openExternal(url); return; } catch (error) { toast(error.message); }
      }
      window.open(url, '_blank', 'noopener,noreferrer');
    });
  });""",
    "小白页联系按钮事件",
)

print()
print(f"完成：{len(changed)} 处结构调整")
