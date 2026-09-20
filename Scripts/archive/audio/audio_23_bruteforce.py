r"""暴力破解动画配置 bin 里未识别的 clip / event mark 哈希。

原理：LOL bin 用 FNV-1a(小写) 32 位哈希存名字（已用 AFKDetection2->e4460934 验证）。
      未被 Riot 注册的名字不会出现在 CDragon 的哈希表里，只能靠候选字典撞。

候选来源：
  1. Animations_RAW/*.anm 的文件名（去掉 darius_skin15_ 前缀）
  2. 已知明文 clip 名（Crit / Death / Dance ...）的各种大小写与后缀变体
  3. 音效事件标记名的常见模式（Audio_*）
"""
import itertools
import json
import re
import sys
from pathlib import Path

DOCS = Path(r"E:\UE\Fight\Docs\Audio")
INTER = DOCS / "_intermediate"
ANM_DIR = Path(r"E:\UE\Assets\Darius_GodKing_LOL_Original\Animations_RAW")

HASH_RE = re.compile(r"^\{([0-9a-fA-F]{8})\}$")


def fnv1a(s: str) -> int:
    h = 0x811c9dc5
    for b in s.encode("ascii", "ignore").lower():
        h = ((h ^ b) * 0x01000193) % 0x100000000
    return h


def build_dict():
    cands = set()

    # 1) 动画文件名
    for p in ANM_DIR.glob("*.anm"):
        stem = p.stem
        for pref in ("darius_skin15_", "darius_skin0_", "darius_"):
            if stem.startswith(pref):
                stem = stem[len(pref):]
                break
        cands.add(stem)
        cands.add(stem.replace("_", ""))
        # 下划线分段的各种组合
        parts = stem.split("_")
        for r in range(1, len(parts) + 1):
            for combo in itertools.combinations(parts, r):
                cands.add("_".join(combo))
                cands.add("".join(combo))
        cands.add(stem.capitalize())

    # 2) 常见动画名 / 技能名（含大小写变体）
    bases = [
        "Attack1", "Attack2", "Attack3", "Crit", "Death", "Dance", "Joke", "Taunt",
        "Laugh", "Recall", "Respawn", "Idle", "Run", "Walk", "Spell1", "Spell2",
        "Spell3", "Spell4", "Spell1_In", "Spell2_In", "Spell3_In", "Spell4_In",
        "Spell1_Out", "Spell2_Out", "Spell3_Out", "Spell4_Out",
        "Spell1_Trans", "Spell2_Trans", "Spell3_Trans", "Spell4_Trans",
        "Spell1_Cast", "Spell2_Cast", "Spell3_Cast", "Spell4_Cast",
        "Spell4_Multi", "Spell4_Trans2", "Spell4_Cast2", "Spell4_Trans3",
        "Death_Trans", "Death2", "Joke_In", "Joke_Loop", "Joke_Out",
        "Taunt_In", "Taunt_Loop", "Taunt_Out", "Dance_In", "Dance_Loop", "Dance_Out",
        "Recall_In", "Recall_Loop", "Recall_Out", "Run_Fast", "Run_Homeguard",
        "Run_Homeguard_RunIn", "Run_Homeguard_RunOut", "Channel", "Channel_In",
        "Channel_Loop", "Channel_Out", "Intro", "Emote", "Cheer", "Spawn",
        "Revive", "Stun", "Knockup", "Land", "Jump", "Dash", "BasicAttack",
        "BasicAttack2", "CritAttack", "Execute", "Cleave", "AxeGrabCone",
        "NoxianTactics", "HemoMax", "Hemo", "Bleed",
    ]
    for b in bases:
        cands.add(b)
        cands.add(b.lower())
        cands.add(b.upper())
        cands.add(b.replace("_", ""))
        cands.add(b.replace("_", " "))
    # 前后缀变体
    for b in list(bases):
        for pre in ("Spell", "Skin15", "Darius", "Skin", "Anim"):
            cands.add(pre + b)
        for suf in ("_Cast", "_Hit", "_Loop", "_In", "_Out", "_Start", "_End", "1", "2", "3"):
            cands.add(b + suf)

    # 3) 音效事件标记名模式
    for pre in ("Audio", "Sound", "Sfx", "SFX", "audio"):
        for body in ("Attack", "Attack1", "Attack2", "Crit", "Death", "Dance", "Joke",
                     "Taunt", "Laugh", "Recall", "Respawn", "Cast", "Hit", "Swing",
                     "Foley", "Voice", "VO", "Emote", "Idle", "Run", "Move", "Spell",
                     "Spell1", "Spell2", "Spell3", "Spell4", "Weapon", "Footstep"):
            cands.add(f"{pre}_{body}")
            cands.add(f"{pre}{body}")
            cands.add(f"{pre}_{body}_1")
            cands.add(f"{pre}_{body}1")
            cands.add(f"{body}_{pre}")
    cands |= {"FaceCamera", "Face_Camera", "SnapWeapon", "SnapWeapon2Hand",
              "wolf", "Wolf", "Throne", "BODY", "Body", "weapon", "Weapon"}
    return cands


def main():
    src = DOCS / "anim_events.json"
    data = json.loads(src.read_text(encoding="utf-8"))

    targets = set()
    for row in data:
        for f in ("clip", "mark"):
            v = row.get(f)
            if isinstance(v, str) and HASH_RE.match(v):
                targets.add(v)

    cands = build_dict()
    print(f"候选名 {len(cands):,} 个，待破解哈希 {len(targets)} 个")

    table = {fnv1a(c): c for c in cands}
    solved = {}
    for t in sorted(targets):
        h = int(t.strip("{}"), 16)
        if h in table:
            solved[t] = table[h]

    print(f"\n破解成功 {len(solved)} / {len(targets)}")
    for k, v in solved.items():
        print(f"   {k}  ->  {v}")

    unsolved = sorted(targets - set(solved))
    if unsolved:
        print(f"\n未破解 ({len(unsolved)}):")
        print("   " + ", ".join(unsolved))

    # 回写
    for row in data:
        for f in ("clip", "mark"):
            v = row.get(f)
            if isinstance(v, str) and v in solved:
                row[f + "_hash"] = v
                row[f] = solved[v]
    out = INTER / "anim_events_resolved.json"
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n已写出 {out}")


if __name__ == "__main__":
    main()
