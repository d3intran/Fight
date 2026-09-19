r"""在 Darius WAD 的全部 .bin 中搜索音频事件名明文。

LOL 的音效绑定以字符串形式存在 bin 的 SoundEventData.mSoundName 里
（已验证：`Play_sfx_DariusSkin15_DariusBasicAttack_foley` → FNV1 → bank Event id 命中）。

本脚本遍历所有 .bin，抽出全部 `Play_*` / `vo_*` 形态的字符串及其所属文件。
"""
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

from cdtb.wad import Wad

WAD = r"E:\WeGameApps\英雄联盟\Game\DATA\FINAL\Champions\Darius.wad.client"
OUT = Path(r"E:\UE\Assets\Darius_GodKing_LOL_Original\Audio_Logic")

# LOL 音频事件命名：Play_sfx_... / Play_vo_... / Play_... / vo_...
PAT = re.compile(rb"[A-Za-z][A-Za-z0-9_]{5,90}")
KEEP = re.compile(r"^(Play_|play_|vo_|VO_|VOE_|Sfx_|sfx_)", re.I)


def main():
    wad = Wad(WAD)
    wad.sanitize_paths()
    bins = [f for f in wad.files if f.path and f.path.lower().endswith(".bin")]
    print(f"共 {len(bins)} 个 .bin，开始扫描事件名明文...\n")

    found = defaultdict(set)   # path -> set(names)
    total_names = set()
    with open(WAD, "rb") as f_in:
        for f in bins:
            try:
                data = f.read_data(f_in)
            except Exception as e:
                print(f"  [ERR] {f.path}: {e}")
                continue
            names = set()
            for m in PAT.finditer(data):
                s = m.group().decode("ascii", "ignore")
                if KEEP.match(s) and not s.endswith("_"):
                    names.add(s)
            if names:
                found[f.path.replace("\\", "/")] = names
                total_names |= names

    print(f"{'='*100}\n命中文件 {len(found)} 个，去重事件名 {len(total_names)} 个\n{'='*100}")
    for path in sorted(found):
        print(f"\n### {path}  ({len(found[path])} 个)")
        for n in sorted(found[path]):
            print(f"    {n}")

    # 落盘
    OUT.mkdir(parents=True, exist_ok=True)
    lst = OUT / "all_event_names.txt"
    lst.write_text("\n".join(sorted(total_names)), encoding="utf-8")
    print(f"\n全部事件名已写入 {lst}")


if __name__ == "__main__":
    main()
