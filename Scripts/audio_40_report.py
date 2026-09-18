r"""生成《德莱厄斯 音频触发逻辑探明报告》自包含 HTML。

数据源：Docs/Audio/audio_master.json + Docs/Audio/anim_events.json
输出：Docs/Audio/德莱厄斯_音频触发逻辑探明报告.html
"""
import html
import json
from collections import defaultdict
from pathlib import Path

DOCS = Path(r"E:\UE\Fight\Docs\Audio")   # 交付物（会进 git）
OUT = DOCS / "德莱厄斯_音频触发逻辑探明报告.html"

master = json.loads((DOCS / "audio_master.json").read_text(encoding="utf-8"))
anim = json.loads((DOCS / "anim_events.json").read_text(encoding="utf-8"))

SFX = [r for r in master if r["type"].startswith("SFX")]
VO = [r for r in master if r["type"].startswith("VO")]

# 技能分组顺序
SKILL_ORDER = [
    "平A 起手 / BasicAttack Cast", "平A 命中 / BasicAttack Hit", "平A 打击感 / Foley",
    "暴击 / Crit",
    "Q 大杀四方 / Cleave", "W 致残打击 / NoxianTactics",
    "E 无情铁手 / AxeGrabCone", "R 断头台 / Execute",
    "被动流血 / Hemo", "死亡 / Death", "舞蹈 / Dance", "笑话 / Joke",
    "嘲讽 / Taunt", "回城 / Recall", "复活 / Respawn", "其他 / Other",
]
VO_ORDER = [c for c, _ in [
    ("移动 / Move", 0), ("攻击 / Attack", 0), ("技能施放 / Cast", 0),
    ("击杀 / Kill", 0), ("死亡 / Death", 0), ("复活 / Respawn", 0),
    ("回城 / Recall", 0), ("嘲讽互动 / Emote", 0),
    ("首次遭遇 / FirstEncounter", 0), ("队友集结 / RallyTeam", 0),
    ("购买装备 / BuyItem", 0), ("使用道具 / UseItem", 0), ("其他 / Other", 0),
]]


def esc(s):
    return html.escape(str(s), quote=True)


def rows_html(rows, order, key="category"):
    by = defaultdict(list)
    for r in rows:
        by[r[key]].append(r)
    out = []
    for cat in order + sorted(set(by) - set(order)):
        if cat not in by:
            continue
        out.append(f'<tr class="grp"><td colspan="5">{esc(cat)} '
                   f'<span class="cnt">{len(by[cat])}</span></td></tr>')
        for r in sorted(by[cat], key=lambda x: x["event_name"]):
            files = [f for f in r["files"].split("|") if f]
            flist = "<br>".join(
                f'<code>{esc(f)}</code>' for f in files[:8])
            if len(files) > 8:
                flist += f'<br><span class="more">… 共 {len(files)} 个文件</span>'
            if not flist:
                flist = '<span class="none">—</span>'
            trig = r["anim_triggers"]
            trig_html = ("<br>".join(f'<code>{esc(t)}</code>'
                                     for t in trig.split("|") if t)
                         if trig else '<span class="none">—</span>')
            out.append(
                "<tr>"
                f'<td class="ev">{esc(r["event_name"])}</td>'
                f'<td class="num">{r["variants"]}</td>'
                f'<td class="num">{len(files)}</td>'
                f'<td class="fl">{flist}</td>'
                f'<td class="tr">{trig_html}</td>'
                "</tr>")
    return "\n".join(out)


# 动画事件（按 clip 分组，只展示音效/粒子）
anim_sound = [r for r in anim if r["kind"] == "SOUND"]
anim_part = [r for r in anim if r["kind"] == "PARTICLE"]


def anim_rows(rows):
    out = []
    for r in sorted(rows, key=lambda x: (x["skin"], x["clip"])):
        fr = "—"
        if r["start"] is not None or r["end"] is not None:
            fr = f'{r["start"] if r["start"] is not None else "0"} ~ {r["end"] if r["end"] is not None else "∞"}'
        out.append(
            "<tr>"
            f'<td>{esc(r["skin"])}</td>'
            f'<td class="ev">{esc(r["clip"])}</td>'
            f'<td>{esc(r["type"])}</td>'
            f'<td class="num">{esc(fr)}</td>'
            f'<td class="ev">{esc(r["detail"])}</td>'
            f'<td>{esc(r["bones"] or "—")}</td>'
            "</tr>")
    return "\n".join(out)


tot_variants = sum(r["variants"] for r in master)
tot_files = sum(len([f for f in r["files"].split("|") if f]) for r in master)

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>德莱厄斯（神王）音频触发逻辑探明报告</title>
<style>
  :root {{
    --bg:#f7f8fa; --card:#fff; --ink:#1a1d24; --sub:#5b6472; --line:#e3e7ee;
    --accent:#b4532a; --accent2:#2a6bb4; --code:#f0f2f6;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font:15px/1.7 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif; }}
  .wrap {{ max-width:1240px; margin:0 auto; padding:40px 28px 80px; }}
  h1 {{ font-size:28px; margin:0 0 6px; letter-spacing:-.3px; }}
  .lead {{ color:var(--sub); margin:0 0 28px; }}
  h2 {{ font-size:20px; margin:44px 0 14px; padding-bottom:8px;
    border-bottom:2px solid var(--line); }}
  h3 {{ font-size:16px; margin:26px 0 10px; color:var(--accent); }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
    padding:20px 22px; margin:16px 0; }}
  .kpis {{ display:flex; gap:14px; flex-wrap:wrap; margin:22px 0 6px; }}
  .kpi {{ flex:1 1 150px; background:var(--card); border:1px solid var(--line);
    border-radius:10px; padding:14px 16px; }}
  .kpi b {{ display:block; font-size:24px; color:var(--accent2); line-height:1.3; }}
  .kpi span {{ color:var(--sub); font-size:12.5px; }}
  table {{ width:100%; border-collapse:collapse; background:var(--card);
    border:1px solid var(--line); border-radius:10px; overflow:hidden;
    font-size:13.5px; margin:12px 0; }}
  th {{ background:#eef1f6; text-align:left; padding:10px 12px; font-weight:600;
    font-size:12.5px; color:var(--sub); border-bottom:1px solid var(--line);
    position:sticky; top:0; }}
  td {{ padding:9px 12px; border-bottom:1px solid var(--line); vertical-align:top; }}
  tr:last-child td {{ border-bottom:none; }}
  tr.grp td {{ background:#f2f5f9; font-weight:600; color:var(--accent);
    font-size:13px; }}
  .cnt {{ color:var(--sub); font-weight:400; }}
  .ev {{ font-family:ui-monospace,Consolas,monospace; font-size:12.5px;
    word-break:break-all; }}
  .num {{ text-align:right; font-variant-numeric:tabular-nums; color:var(--sub); }}
  .fl code, .tr code {{ background:var(--code); padding:1px 5px; border-radius:4px;
    font-size:11.5px; display:inline-block; margin:1px 0; }}
  .none {{ color:#b8c0cc; }}
  .more {{ color:var(--sub); font-size:11.5px; }}
  .flow {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
    padding:18px 20px; overflow-x:auto; }}
  .flow code {{ font-size:12.5px; }}
  .note {{ border-left:3px solid var(--accent2); background:#f2f6fc;
    padding:12px 16px; border-radius:0 8px 8px 0; margin:14px 0; font-size:13.5px; }}
  .warn {{ border-left-color:var(--accent); background:#fdf4f0; }}
  .search {{ width:100%; padding:10px 14px; font-size:14px; border:1px solid var(--line);
    border-radius:8px; margin:14px 0 6px; background:var(--card); }}
  ul {{ padding-left:20px; }} li {{ margin:5px 0; }}
  .tag {{ display:inline-block; background:var(--code); border-radius:5px;
    padding:1px 7px; font-size:12px; font-family:ui-monospace,Consolas,monospace; }}
  .hide {{ display:none !important; }}
  footer {{ margin-top:56px; color:var(--sub); font-size:12.5px;
    border-top:1px solid var(--line); padding-top:16px; }}
</style>
</head>
<body>
<div class="wrap">

<h1>德莱厄斯（神王）音频触发逻辑探明报告</h1>
<p class="lead">从《英雄联盟》客户端原始资产中逆向出「音效 / 语音何时播报、播的是哪个文件」的完整链路。
数据全部来自本机 WAD 解包，可复现、可验证。</p>

<div class="kpis">
  <div class="kpi"><b>{len(master)}</b><span>音频事件条目</span></div>
  <div class="kpi"><b>{tot_variants}</b><span>随机变体音频数</span></div>
  <div class="kpi"><b>{tot_files}</b><span>已定位 wav 文件</span></div>
  <div class="kpi"><b>{len(anim_sound)}</b><span>动画驱动的音效点</span></div>
  <div class="kpi"><b>{len(anim_part)}</b><span>动画驱动的粒子点</span></div>
</div>

<h2>一、核心结论：LOL 的音效到底怎么触发的</h2>

<div class="note warn">
<b>反直觉的发现：</b>技能音效<b>不在</b> <code>darius.bin</code> 的技能定义里。
通读 <code>data/characters/darius/darius.bin</code>（24 KB，含 Q/W/E/R/平A 全部数值）后确认，
里面只有冷却、射程、伤害、系数等纯数值字段，<b>唯一的音频相关字段是 <code>mApplyMaterialOnHitSound</code></b>。
音效事件是<b>按动画帧挂载</b>的。
</div>

<div class="card">
<b>完整触发链路（已逐环节验证）</b>
<div class="flow">
<pre>
① 动画配置 bin
   data/characters/darius/animations/skin15.bin
      mClipDataMap["Attack1"].mEventDataMap["&lt;事件标记&gt;"]
         ├ __type = SoundEventData     -> mSoundName = "Play_sfx_DariusSkin15_DariusBasicAttack_foley"
         ├ __type = ParticleEventData  -> mEffectKey = "Darius_BA_Swipe_01"
         ├ __type = SubmeshVisibilityEventData / JointSnapEventData
         └ mStartFrame / mEndFrame      -> 触发帧区间
                    │
                    │  Wwise 哈希：FNV-1 32 位，输入小写
                    ▼
② 事件表 bank（被剥离了名字表 STID，只剩哈希 ID）
   assets/sounds/.../skin15/darius_skin15_sfx_events.bnk
      Event(id=4103663980) -> EventAction -> Sound/Container -> wem short id
                    ▼
③ 音频数据 bank / 包
   darius_skin15_sfx_audio.bnk  (DIDX+DATA 内嵌 wem)
   darius_skin15_vo_audio.wpk   (r3d2 包，文件名为 wem id)
                    ▼
④ 本地 wav（vgmstream 转码）
</pre>
</div>
</div>

<h3>哈希算法的实测验证</h3>
<p>用 <code>Play_sfx_DariusSkin15_DariusBasicAttack_foley</code> 做 FNV-1（<b>先乘后异或</b>，输入转小写）得到
<code>4103663980</code>，在 bank 的 Event 集合中<b>命中</b>。这一步是整个逆向的钥匙 ——
它把 bin 里的明文名字与 bank 里的匿名哈希 ID 缝合起来。</p>

<div class="note">
<b>两个不同的哈希，别搞混：</b>
<ul>
<li><b>Wwise 音频事件</b>（音效/语音事件名）→ <span class="tag">FNV-1</span> 先乘后异或，输入小写</li>
<li><b>LOL bin 字段/条目</b>（如 <code>AFKDetection2 → e4460934</code>）→ <span class="tag">FNV-1a</span> 先异或后乘，输入小写</li>
</ul>
</div>

<h3>命名规范</h3>
<div class="card">
<pre><code>Play_sfx_&lt;英雄&gt;&lt;皮肤&gt;_&lt;技能&gt;_&lt;阶段&gt;      音效
Play_vo_&lt;英雄&gt;&lt;皮肤&gt;_&lt;触发场景&gt;&lt;2D|3D&gt;&lt;变体&gt;   语音</code></pre>
<ul>
<li><b>阶段</b>：<code>OnCast</code> 起手 / <code>OnHit</code> 命中 / <code>hit_inner</code>·<code>hit_outter</code> 内圈外圈 /
<code>hit_kill</code> 击杀 / <code>swing</code> 挥砍 / <code>foley</code> 衣物摩擦 /
<code>buffactivate</code> buff 激活 / <code>loop</code> 循环 / <code>leadin</code>·<code>leadout</code> 前奏尾奏 / <code>oba</code> 一次性变体</li>
<li><b>2D / 3D</b>：<code>2D</code> = 非定位音（UI 播报类，不随位置衰减）；
<code>3D</code> = 定位音（从角色位置发出，随距离衰减）</li>
<li><b>变体后缀</b>：<code>General</code> 通用 / <code>First</code> 首次 / <code>Penta</code> 五杀 /
<code>GarenSkin13</code> 等为特定对手/装备专用</li>
</ul>
</div>

<h2>二、平A 与 QWER 音效清单</h2>
<p>以下是神王皮肤（skin15）与基础皮肤（base）的完整技能音效事件。<b>变体数</b>表示该事件背后有多个随机音频，
每次触发随机播一个（Wwise RandomSequenceContainer）。</p>

<input class="search" id="s1" placeholder="搜索事件名 / 分类…（例如 Cleave、OnHit）">
<table id="t1">
<thead><tr><th style="width:36%">事件名（mSoundName）</th><th style="width:7%">变体</th>
<th style="width:7%">文件</th><th style="width:34%">对应 wav 文件</th><th style="width:16%">动画触发</th></tr></thead>
<tbody>
{rows_html(SFX, SKILL_ORDER)}
</tbody>
</table>

<h2>三、语音（VO）播报时机全表</h2>
<p>事件名本身就编码了触发场景。共 <b>{len(VO)}</b> 条。</p>

<div class="note">
<b>怎么读这张表：</b>例如 <code>Play_vo_DariusSkin15_Kill3DGeneral</code> 表示
「击杀敌方英雄时，从角色位置（3D）播放通用击杀台词」，背后有 27 个变体随机抽取。
<code>Play_vo_DariusSkin15_FirstEncounter3DAatrox</code> 表示「首次遇到亚托克斯时专属台词」。
</div>

<input class="search" id="s2" placeholder="搜索触发场景 / 英雄名…（例如 Kill、FirstEncounter、Aatrox）">
<table id="t2">
<thead><tr><th style="width:36%">事件名（mSoundName）</th><th style="width:7%">变体</th>
<th style="width:7%">文件</th><th style="width:50%">对应 wav 文件</th></tr></thead>
<tbody>
{rows_html(VO, VO_ORDER)}
</tbody>
</table>

<h2>四、动画事件表（音效 / 粒子 / 骨骼 / 子网格）</h2>
<p>这些是挂在动画帧上的事件点。<b>帧号是「何时播报」的直接答案</b>。</p>

<h3>音效事件</h3>
<table>
<thead><tr><th>皮肤</th><th>动画 Clip</th><th>事件类型</th><th>帧区间</th>
<th>音效名</th><th>挂点骨骼</th></tr></thead>
<tbody>
{anim_rows(anim_sound)}
</tbody>
</table>

<h3>粒子 / 特效事件</h3>
<table>
<thead><tr><th>皮肤</th><th>动画 Clip</th><th>事件类型</th><th>帧区间</th>
<th>特效名</th><th>挂点骨骼</th></tr></thead>
<tbody>
{anim_rows(anim_part)}
</tbody>
</table>

<h2>五、已知边界与待办</h2>
<div class="card">
<ul>
<li><b>代码驱动事件 vs 动画驱动事件。</b>
<code>OnCast</code> / <code>OnHit</code> 这类事件由游戏逻辑在技能结算时触发，<b>不挂在动画帧上</b>，
所以它们在动画事件表里查不到 —— 这是正常的，不代表数据缺失。</li>
<li><b>未命名 Event。</b>bank 里还有少量 Event 的哈希未能反查到名字
（base 9 个、skin15 约 17 个、vo 5 个）。原因：CDragon 公开哈希表只收录 Riot 注册过的字段名，
美术自定义的动画标记名（如 <code>{{bf57e8fe}}</code>）不在表内，且实测<b>不是</b> FNV-1a 名字哈希，
疑似编辑器分配的随机 ID。它们不影响已命名的技能/语音链路。</li>
<li><b>VO 精确时序。</b>数据给出的是「触发场景 + 音频池」。
具体冷却间隔、优先级抢占、同队同时触发时的去重，属于客户端运行时逻辑，不在资产内。</li>
<li><b>base 皮肤的音效事件远少于 skin15。</b>base 只有 4 条动画驱动音效
（Death / Joke / Taunt / Dance），神王皮肤有 13 条 —— 传说皮肤额外录制了
舞蹈、笑话、回城、复活等一整套专属音频。</li>
<li><b>base 与 skin15 的 bank 是「叠加」关系，不是替换。</b>
神王皮肤只覆盖它自己录过的部分事件，其余回落到 base。
最典型的例子是 <b>W 致残打击</b>：skin15 的 bank 里只有
<code>DariusNoxianTacticsONH_OnBuffActivate</code>（buff 激活），
而它的命中音效 <code>DariusNoxianTacticsONHAttack_OnHit</code> 只在 <b>base</b> bank 里。
若后续只导 skin15 的 bank 而丢掉 base，W 的命中就会没声音。</li>
</ul>
</div>

<h2>六、复现脚本</h2>
<table>
<thead><tr><th style="width:34%">脚本</th><th>作用</th></tr></thead>
<tbody>
<tr><td class="ev">Scripts/audio_01_scan_wad.py</td><td>扫描 WAD，列出全部 .bin / .bnk / .wpk</td></tr>
<tr><td class="ev">Scripts/audio_02_extract_logic.py</td><td>提取 darius.bin、动画 bin、事件表 bank、语音包</td></tr>
<tr><td class="ev">Scripts/audio_03_scan_event_names.py</td><td>从全部 bin 中抽出明文音频事件名（634 个）</td></tr>
<tr><td class="ev">Scripts/audio_04_extract_wavs.py</td><td>bank / wpk 解出 wav（vgmstream 转码，623 个）</td></tr>
<tr><td class="ev">Scripts/audio_10_bnk_parse.py</td><td>Wwise bank chunk 与 HIRC 对象解析</td></tr>
<tr><td class="ev">Scripts/audio_11_bin_dump.py</td><td>LOL bin（PROP）转 JSON 并关键词检索</td></tr>
<tr><td class="ev">Scripts/audio_20_hirc_graph.py</td><td>★ 建 Event→Action→Sound→wem 链路，并用 FNV-1 反查事件名</td></tr>
<tr><td class="ev">Scripts/audio_21_anim_events.py</td><td>★ 提取动画事件（音效/粒子/骨骼/子网格 + 帧号）</td></tr>
<tr><td class="ev">Scripts/audio_22_hash_lookup.py</td><td>用 CDragon 哈希表反查 bin 字段名</td></tr>
<tr><td class="ev">Scripts/audio_23_bruteforce.py</td><td>字典暴力破解未识别的动画标记哈希</td></tr>
<tr><td class="ev">Scripts/audio_30_summary.py</td><td>汇总主表（CSV / JSON）</td></tr>
</tbody>
</table>

<h3>运行环境</h3>
<div class="card">
<pre><code>uv venv E:/uv_env --python 3.12
uv pip install --python E:/uv_env/Scripts/python.exe --link-mode=copy cdtb
E:/uv_env/Scripts/python.exe -m cdtb fetch-hashes   # 下载 CDragon 哈希表（必须）</code></pre>
</div>

<h3>全流程重跑</h3>
<div class="card">
<pre><code># 1) 扫 WAD + 提原始文件（输出到 E:\\UE\\Assets\\Darius_GodKing_LOL_Original\\Audio_Logic）
E:/uv_env/Scripts/python.exe Scripts/audio_01_scan_wad.py
E:/uv_env/Scripts/python.exe Scripts/audio_02_extract_logic.py
E:/uv_env/Scripts/python.exe Scripts/audio_03_scan_event_names.py
E:/uv_env/Scripts/python.exe Scripts/audio_04_extract_wavs.py

# 2) 建链路 + 提动画事件（输出到 Docs/Audio）
E:/uv_env/Scripts/python.exe Scripts/audio_20_hirc_graph.py
E:/uv_env/Scripts/python.exe Scripts/audio_21_anim_events.py
E:/uv_env/Scripts/python.exe Scripts/audio_22_hash_lookup.py
E:/uv_env/Scripts/python.exe Scripts/audio_23_bruteforce.py
E:/uv_env/Scripts/python.exe Scripts/audio_30_summary.py
E:/uv_env/Scripts/python.exe Scripts/audio_40_report.py</code></pre>
</div>

<h2>七、产出文件清单</h2>
<div class="note">
所有交付物放在 <code>E:\\UE\\Fight\\Docs\\Audio\\</code>，<b>会进 git</b>。
（此前曾误放在 <code>Saved\\</code>，但 <code>.gitignore</code> 里有 <code>Saved/*</code>，
团队和 CI 都看不到，已迁出。）
</div>
<div class="card">
<pre><code>E:\\UE\\Fight\\Docs\\Audio\\
├─ 德莱厄斯_音频触发逻辑探明报告.html   ← 本报告
├─ audio_master.csv / .json             ← 主数据表（145 行）
├─ anim_events.csv / .json              ← 动画事件表（含帧号）
└─ _intermediate\                       ← 中间产物（可删，可重生成）
   ├─ audio_event_graph.json            bank 侧事件→wem 链路
   ├─ anim_events_named.json            哈希反查结果
   ├─ anim_events_resolved.json         字典暴破结果
   ├─ darius_bin.json / skin15_bin.json / anim_skin15.json
   └─ *_out.txt / dump_*.txt            各步骤控制台日志</code></pre>
</div>

<h2>八、原始文件清单</h2>
<div class="card">
<pre><code>E:\\UE\\Assets\\Darius_GodKing_LOL_Original\\
├─ Audio_Logic\\main\\darius.bin                     角色主定义（技能数值）
├─ Audio_Logic\\main\\skin15.bin                     神王皮肤定义
├─ Audio_Logic\\main\\anim__skin0.bin                基础皮肤动画事件
├─ Audio_Logic\\main\\anim__skin15.bin               神王皮肤动画事件 ★
├─ Audio_Logic\\main\\base__*_sfx_events.bnk        基础音效事件表
├─ Audio_Logic\\main\\skin15__*_sfx_events.bnk      神王音效事件表 ★
├─ Audio_Logic\\zh_CN\\*_vo_events.bnk               语音事件表 ★
├─ Audio_Logic\\zh_CN\\skin15__*_vo_audio.wpk        语音音频包（中文）
├─ Audio_SFX_Base\\          73 个 wav（基础音效）
├─ Audio_SFX_Skin15\\        56 个 wav（神王音效）
├─ Audio_VO_zh_CN\\         225 个 wav（神王中文语音）
├─ Audio_VO_zh_CN_Base\\     44 个 wav（基础中文语音）
├─ Audio_VO_en_US\\         225 个 wav（神王英文语音）
└─ Audio_Logic\\all_event_names.txt                634 个事件名清单</code></pre>
</div>

<footer>
数据来源：本机《英雄联盟》客户端 <code>Darius.wad.client</code> / <code>Darius.zh_CN.wad.client</code> / <code>Darius.en_US.wad.client</code>。<br>
解析工具：cdtb 1.3.0（WAD / BIN）、vgmstream-cli（wem→wav）、自研 Wwise bank 解析器。<br>
所有结论均经数值验证，未使用主观判断。
</footer>

</div>
<script>
function bind(inputId, tableId) {{
  const inp = document.getElementById(inputId);
  const rows = document.getElementById(tableId).querySelectorAll('tbody tr');
  inp.addEventListener('input', () => {{
    const q = inp.value.trim().toLowerCase();
    let grpPending = false, grpRow = null, grpVisible = false;
    rows.forEach(r => {{
      if (r.classList.contains('grp')) {{
        if (grpRow) grpRow.classList.toggle('hide', !grpVisible);
        grpRow = r; grpVisible = false;
        return;
      }}
      const hit = !q || r.textContent.toLowerCase().includes(q);
      r.classList.toggle('hide', !hit);
      if (hit) grpVisible = true;
    }});
    if (grpRow) grpRow.classList.toggle('hide', !grpVisible);
  }});
}}
bind('s1','t1'); bind('s2','t2');
</script>
</body>
</html>
"""

OUT.write_text(HTML, encoding="utf-8")
print(f"已生成 {OUT}  ({OUT.stat().st_size:,} bytes)")
print(f"  SFX 条目 {len(SFX)} | VO 条目 {len(VO)} | 动画音效 {len(anim_sound)} | 动画粒子 {len(anim_part)}")
