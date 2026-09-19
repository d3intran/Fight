r"""从动画配置 bin 提取全部动画事件（音效 / 粒子 / 骨骼 / 子网格）。

LOL 的「何时播报」由动画事件驱动，结构为：

    Characters/<Champ>/Animations/<Skin>
      └ mClipDataMap[<动画名>]
          └ mEventDataMap[<事件标记名>]
              ├ __type = SoundEventData      -> mSoundName（Wwise event 名）
              ├ __type = ParticleEventData   -> mEffectKey（粒子系统名）
              ├ __type = SubmeshVisibilityEventData -> mShowSubmeshList
              └ __type = JointSnapEventData  -> 骨骼吸附
              （附 mStartFrame / mEndFrame 指定触发帧）

输出 CSV + JSON，供 UE 侧还原打击点与音画同步。
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audio_11_bin_dump import load_json  # noqa: E402

ROOT = Path(r"E:\UE\Assets\Darius_GodKing_LOL_Original\Audio_Logic\main")
DOCS = Path(r"E:\UE\Fight\Docs\Audio")   # 交付物（会进 git）

TARGETS = [
    ("skin0(base)", ROOT / "anim__skin0.bin"),
    ("skin15(神王)", ROOT / "anim__skin15.bin"),
]


def collect(anim_root: dict, skin_tag: str):
    rows = []
    for champ_path, champ in anim_root.items():
        if not isinstance(champ, dict):
            continue
        clips = champ.get("mClipDataMap") or {}
        for clip_name, clip in clips.items():
            if not isinstance(clip, dict):
                continue
            events = clip.get("mEventDataMap") or {}
            for ev_mark, ev in events.items():
                if not isinstance(ev, dict):
                    continue
                etype = ev.get("__type", "?")
                base = {
                    "skin": skin_tag,
                    "clip": clip_name,
                    "mark": ev_mark,
                    "type": etype,
                    "start": ev.get("mStartFrame"),
                    "end": ev.get("mEndFrame"),
                }
                if etype == "SoundEventData":
                    base["detail"] = ev.get("mSoundName", "")
                    base["kind"] = "SOUND"
                elif etype == "ParticleEventData":
                    base["detail"] = ev.get("mEffectKey", "")
                    base["kind"] = "PARTICLE"
                elif etype == "SubmeshVisibilityEventData":
                    base["detail"] = "|".join(ev.get("mShowSubmeshList") or [])
                    base["kind"] = "SUBMESH"
                elif etype == "JointSnapEventData":
                    base["detail"] = f"{ev.get('mJointNameToOverride')}->{ev.get('mJointNameToSnapTo')}"
                    base["kind"] = "JOINT"
                else:
                    base["detail"] = ""
                    base["kind"] = "OTHER"
                # 附加骨骼 / 挂点信息
                pairs = ev.get("mParticleEventDataPairList") or []
                bones = [p.get("mBoneName") for p in pairs if isinstance(p, dict)]
                base["bones"] = "|".join(b for b in bones if b)
                rows.append(base)
    return rows


def main():
    all_rows = []
    for tag, path in TARGETS:
        if not path.exists():
            print(f"[SKIP] {path.name} 不存在")
            continue
        data = load_json(path)
        rows = collect(data, tag)
        all_rows += rows
        print(f"\n{'='*100}\n{tag}  {path.name}  -> 事件 {len(rows)} 条\n{'='*100}")
        from collections import Counter
        print("  类型分布:", dict(Counter(r["kind"] for r in rows)))
        for r in rows:
            print(f"  [{r['kind']:<8}] clip={r['clip']:<18} mark={r['mark']:<26} "
                  f"frame={str(r['start']):>6}~{str(r['end']):<6} {r['detail'][:70]}")

    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "anim_events.json").write_text(
        json.dumps(all_rows, indent=1, ensure_ascii=False), encoding="utf-8")
    csv_path = DOCS / "anim_events.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["skin", "clip", "mark", "type", "kind",
                                          "start", "end", "detail", "bones"])
        w.writeheader()
        w.writerows(all_rows)
    print(f"\n共 {len(all_rows)} 条 -> {csv_path} / anim_events.json")


if __name__ == "__main__":
    main()
