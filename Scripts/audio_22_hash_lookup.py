r"""把 bin 里未识别的 `{xxxxxxxx}` 哈希反查成人类可读名字。

LOL bin 的属性名 / 条目路径用 FNV-1(小写) 32 位哈希存储。
CommunityDragon 公开了完整映射表（cdtb fetch-hashes 下载）。

用法：
    python audio_22_hash_lookup.py <输入.json> [输出.json]
"""
import json
import re
import sys
from pathlib import Path

HASH_DIR = Path.home() / "AppData/Local/cdragon/data/hashes/lol"
DOCS = Path(r"E:\UE\Fight\Docs\Audio")
INTER = DOCS / "_intermediate"

TABLES = ["hashes.binhashes.txt", "hashes.binfields.txt",
          "hashes.binentries.txt", "hashes.bintypes.txt", "hashes.rst.txt"]

HASH_RE = re.compile(r"^\{([0-9a-fA-F]{8})\}$")


def load_tables():
    tables = {}
    for name in TABLES:
        p = HASH_DIR / name
        if not p.exists():
            continue
        d = {}
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line or " " not in line:
                continue
            h, _, val = line.partition(" ")
            try:
                d[int(h, 16)] = val
            except ValueError:
                continue
        tables[name] = d
    return tables


def fnv1_lower(s: str) -> int:
    h = 2166136261
    for ch in s.lower().encode("utf-8"):
        h = (h * 16777619) & 0xFFFFFFFF
        h ^= ch
    return h


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DOCS / "anim_events.json"
    dst = (Path(sys.argv[2]) if len(sys.argv) > 2
           else INTER / (src.stem + "_named.json"))

    tables = load_tables()
    print("已加载哈希表:")
    for k, v in tables.items():
        print(f"   {k:<26} {len(v):,} 条")

    data = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        data = [data]

    # 同时构造「已知名字 -> 哈希」反向表，用于校验
    reverse = {}
    for tbl in tables.values():
        for h, name in tbl.items():
            reverse.setdefault(name, h)

    stats = {"hit": 0, "miss": 0}
    for row in data:
        for field in ("clip", "mark"):
            v = row.get(field)
            if not isinstance(v, str):
                continue
            m = HASH_RE.match(v)
            if not m:
                continue
            h = int(m.group(1), 16)
            found = None
            for tname, tbl in tables.items():
                if h in tbl:
                    found = (tbl[h], tname)
                    break
            if found:
                row[field + "_raw"] = v
                row[field] = found[0]
                stats["hit"] += 1
            else:
                stats["miss"] += 1

    print(f"\n反查结果: 命中 {stats['hit']} 个, 未命中 {stats['miss']} 个")
    dst.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"已写出 {dst}")

    # 展示未命中的哈希，便于进一步攻破
    misses = set()
    for row in data:
        for field in ("clip", "mark"):
            v = row.get(field)
            if isinstance(v, str) and HASH_RE.match(v):
                misses.add(v)
    if misses:
        print(f"\n仍未反查出的哈希 ({len(misses)}):")
        for v in sorted(misses):
            print("   ", v, "= fnv1_32(?)", int(v.strip('{}'), 16))


if __name__ == "__main__":
    main()
