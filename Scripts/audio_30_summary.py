r"""汇总全部音频触发数据为一张主表。

输入：
  Docs/Audio/_intermediate/audio_event_graph.json   —— bank 侧：事件名 -> Event -> wem 集合
  Docs/Audio/anim_events.json         —— 动画侧：动画/帧 -> 事件名
  资产目录的 wav 文件            —— wem id -> 本地音频文件
输出：
  Docs/Audio/audio_master.json / .csv —— 可查主表
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"E:\UE\Assets\Darius_GodKing_LOL_Original")
DOCS = Path(r"E:\UE\Fight\Docs\Audio")   # 交付物（会进 git）
INTER = DOCS / "_intermediate"           # 中间产物

# ---------------------------------------------------------------- wem -> 本地文件

def index_wavs():
    """wem short id -> 本地 wav 相对路径。

    文件名约定：<前缀>_<序号>_<wem short id>.wav
    （无论是从 bank 的 DIDX 解出，还是从 wpk 的文件名取，末段都是 wem id）
    """
    idx = {}
    dirs = [p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("Audio_")]
    for d in dirs:
        for p in d.glob("*.wav"):
            m = re.search(r"_(\d+)\.wav$", p.name)
            if m:
                idx.setdefault(int(m.group(1)), []).append(str(p.relative_to(ROOT)))
    return idx


# ---------------------------------------------------------------- 语义分类

VO_RULES = [
    ("移动 / Move",              r"Move"),
    ("攻击 / Attack",            r"Attack|Crit"),
    ("技能施放 / Cast",          r"_cast3D|Spell3DPMax"),
    ("击杀 / Kill",              r"Kill"),
    ("死亡 / Death",             r"Death"),
    ("复活 / Respawn",           r"Respawn"),
    ("回城 / Recall",            r"Recall"),
    ("嘲讽互动 / Emote",         r"Joke|Laugh|Taunt"),
    ("首次遭遇 / FirstEncounter", r"FirstEncounter"),
    ("队友集结 / RallyTeam",     r"RallyTeam"),
    ("购买装备 / BuyItem",       r"BuyItem"),
    ("使用道具 / UseItem",       r"UseItem"),
]

SFX_RULES = [
    ("平A 起手 / BasicAttack Cast",  r"DariusBasicAttack_OnCast|BasicAttack2_OnCast"),
    ("平A 命中 / BasicAttack Hit",   r"DariusBasicAttack_OnHit|BasicAttack2_OnHit"),
    ("平A 打击感 / Foley",           r"BasicAttack_foley"),
    ("暴击 / Crit",                  r"CritAttack"),
    ("Q 大杀四方 / Cleave",          r"Cleave"),
    ("W 致残打击 / NoxianTactics",   r"NoxianTactics"),
    ("E 无情铁手 / AxeGrabCone",     r"AxeGrabCone"),
    ("R 断头台 / Execute",           r"Execute"),
    ("被动流血 / Hemo",              r"Hemo"),
    ("死亡 / Death",                 r"Death"),
    ("舞蹈 / Dance",                 r"[Dd]ance"),
    ("笑话 / Joke",                  r"[Jj]oke"),
    ("嘲讽 / Taunt",                 r"[Tt]aunt"),
    ("回城 / Recall",                r"[Rr]ecall"),
    ("复活 / Respawn",               r"[Rr]espawn"),
]


def classify(name, rules):
    for label, pat in rules:
        if re.search(pat, name):
            return label
    return "其他 / Other"


def main():
    graph = json.loads((INTER / "audio_event_graph.json").read_text(encoding="utf-8"))
    anim = json.loads((DOCS / "anim_events.json").read_text(encoding="utf-8"))
    wav_idx = index_wavs()

    # 动画侧：事件名 -> [(动画, 帧区间)]
    anim_by_event = defaultdict(list)
    anim_rows = []
    for r in anim:
        if r["kind"] != "SOUND":
            continue
        detail = r.get("detail") or ""
        if not detail:
            continue
        anim_by_event[detail].append((r["clip"], r["start"], r["end"]))
        anim_rows.append(r)

    rows = []
    for bank_tag, events in graph.items():
        is_vo = bank_tag.startswith("vo")
        for e in events:
            names = e["names"] or [f"<未命名 Event 0x{e['event_id']:08X}>"]
            for nm in names:
                wems = e["wems"]
                files = []
                for w in wems:
                    files += wav_idx.get(w, [])
                triggers = anim_by_event.get(nm, [])
                rows.append({
                    "bank": bank_tag,
                    "type": "VO 语音" if is_vo else "SFX 音效",
                    "category": classify(nm, VO_RULES if is_vo else SFX_RULES),
                    "event_name": nm,
                    "event_id": e["event_id"],
                    "variants": e["wem_count"],
                    "wem_ids": "|".join(str(w) for w in wems),
                    "files": "|".join(files),
                    "anim_triggers": "|".join(f"{c}@{s}~{en}" for c, s, en in triggers),
                })

    rows.sort(key=lambda r: (r["bank"], r["category"], r["event_name"]))

    (DOCS / "audio_master.json").write_text(
        json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    with open(DOCS / "audio_master.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---- 控制台摘要
    print(f"主表 {len(rows)} 行\n")
    by = defaultdict(list)
    for r in rows:
        by[(r["bank"], r["category"])].append(r)
    for (bank, cat) in sorted(by):
        print(f"\n### {bank} / {cat}  ({len(by[(bank,cat)])} 条)")
        for r in by[(bank, cat)]:
            t = f"  动画触发: {r['anim_triggers']}" if r["anim_triggers"] else ""
            print(f"   {r['event_name']:<62} 变体 x{r['variants']:<3} 文件 x{len(r['files'].split('|')) if r['files'] else 0}{t}")

    # 统计覆盖率
    tot = sum(len(e["names"]) for evs in graph.values() for e in evs)
    named = sum(1 for r in rows if not r["event_name"].startswith("<未命名"))
    print(f"\n{'='*90}")
    print(f"事件名总数 {tot}（含未命名占位 {tot-named} 个）")
    print(f"本地音频文件索引: {len(wav_idx)} 个 wem id")
    print(f"动画驱动事件: {len(anim_rows)} 条")
    print(f"输出: {DOCS / 'audio_master.csv'}")


if __name__ == "__main__":
    main()
