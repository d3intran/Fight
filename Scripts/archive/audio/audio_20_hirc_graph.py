r"""解析 Wwise bank，建立「事件名 → Event → EventAction → Sound/Container → wem → wav」完整链路。

背景（已实测验证）：
  - LOL 音频事件名以明文存在于 bin 的 SoundEventData.mSoundName
  - Wwise 用 FNV-1(小写) 32 位哈希把名字转成 Event id
    验证：Play_sfx_DariusSkin15_DariusBasicAttack_foley -> 4103663980 (命中 bank)
  - bank 被剥离了 STID 名字表，所以名字必须从 bin 侧拿

本脚本不依赖具体版本的结构体定义，采用「已知 id 集合 + 引用关系」的方式
重建 HIRC 对象图，稳健性优先。
"""
import json
import re
import struct
import sys
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audio_10_bnk_parse import iter_chunks, parse_hirc, HIRC_TYPES  # noqa: E402

ROOT = Path(r"E:\UE\Assets\Darius_GodKing_LOL_Original")
LOGIC = ROOT / "Audio_Logic"
DOCS = Path(r"E:\UE\Fight\Docs\Audio")   # 交付物（会进 git）
INTER = DOCS / "_intermediate"           # 中间产物


# ---------------------------------------------------------------- 哈希

def fnv1_lower(s: str) -> int:
    """Wwise 的 AK::SoundEngine::GetIDFromString —— FNV-1，输入小写。"""
    h = 2166136261
    for ch in s.lower().encode("utf-8"):
        h = (h * 16777619) & 0xFFFFFFFF
        h ^= ch
    return h


# ---------------------------------------------------------------- wem id 集合

def wem_ids_from_bnk(path: Path):
    """从 audio bank 的 DIDX 取全部 wem short id。"""
    d = path.read_bytes()
    ids = {}
    for cid, off, size, pl in iter_chunks(d):
        if cid == "DIDX":
            n = size // 12
            for i in range(n):
                fid, foff, fsize = struct.unpack("<III", pl[i * 12:i * 12 + 12])
                ids[fid] = fsize
    return ids


def wem_ids_from_wpk(path: Path):
    """从 wpk 取全部 wem short id（文件名即 id）。"""
    d = path.read_bytes()
    magic, ver, cnt = struct.unpack("<4sII", d[:12])
    offs = struct.unpack(f"<{cnt}I", d[12:12 + cnt * 4])
    ids = {}
    for off in offs:
        doff, dsize, nlen = struct.unpack("<III", d[off:off + 12])
        raw = d[off + 12:off + 12 + nlen * 2]
        try:
            name = raw.decode("utf-16-le").rstrip("\x00")
        except Exception:
            continue
        m = re.match(r"(\d+)", name)
        if m:
            ids[int(m.group(1))] = dsize
    return ids


# ---------------------------------------------------------------- HIRC 图

def u32s_in(body: bytes, start=4):
    """枚举 body 中 4 字节对齐的 u32（跳过 id 本身）。"""
    out = []
    for i in range(start, len(body) - 3, 4):
        out.append(struct.unpack("<I", body[i:i + 4])[0])
    return out


def u32s_any(body: bytes, start=4):
    """枚举 body 中**任意字节偏移**的 u32。

    Wwise 的 CAkSound / CAkContainer 结构里存在 u8 字段，
    导致关键 id（如 source_id）落在非 4 字节对齐位置，必须逐字节扫描。
    """
    out = []
    for i in range(start, len(body) - 3):
        out.append((i, struct.unpack("<I", body[i:i + 4])[0]))
    return out


def pick_refs(body: bytes, pool: set, self_id: int, max_n=64):
    """从 body 中挑出「引用了 pool 内 id」的字段，按偏移去重保序。

    pool 通常是「本 bank 内全部 HIRC object id」，命中概率极低，误报可忽略。
    """
    seen, out = set(), []
    for off, v in u32s_any(body):
        if v in pool and v != self_id and v not in seen:
            seen.add(v)
            out.append((off, v))
            if len(out) >= max_n:
                break
    return out


def sound_wem(body: bytes, wem_pool: set):
    """CAkSound：source_id（wem short id）固定在 offset 9。

    实测样本（skin15 sfx events bank）：
        id(4) | plugin_id(1) | flags(4) | source_id(4)@9 | size(4)@13
    为稳健起见，offset 9 未命中时退化为全扫描。
    """
    if len(body) >= 13:
        v = struct.unpack("<I", body[9:13])[0]
        if v in wem_pool:
            return v
    for off, v in u32s_any(body, start=4):
        if v in wem_pool:
            return v
    return None


def build_graph(bnk_path: Path, wem_ids: dict, all_ids: set, verbose=True):
    """返回 events: {event_id: {'actions': [...], 'sounds': [...], 'wems': [...]}}"""
    d = bnk_path.read_bytes()
    hirc = None
    for cid, off, size, pl in iter_chunks(d):
        if cid == "HIRC":
            hirc = pl
    if hirc is None:
        return {}

    objs = parse_hirc(hirc)
    by_type = defaultdict(dict)
    for t, oid, body in objs:
        by_type[t][oid] = body

    # 1) Sound -> wem id
    sound_to_wem = {}
    for oid, body in by_type[2].items():
        sound_to_wem[oid] = sound_wem(body, wem_ids)

    # 2) Container(5/6/9/23) -> 子对象（Sound 或子 Container）
    obj_ids = set()
    for t in (2, 5, 6, 9, 23):
        obj_ids |= set(by_type[t].keys())

    container_children = {}
    for t in (5, 6, 9, 23):
        for oid, body in by_type[t].items():
            kids = [v for _, v in pick_refs(body, obj_ids, oid)]
            container_children[oid] = kids

    def resolve_wems(oid, depth=0, seen=None):
        """递归展开 container / sound -> wem id 集合"""
        seen = seen or set()
        if oid in seen or depth > 6:
            return []
        seen.add(oid)
        if oid in by_type[2]:
            w = sound_to_wem.get(oid)
            return [w] if w else []
        out = []
        for k in container_children.get(oid, []):
            out += resolve_wems(k, depth + 1, seen)
        return out

    # 3) EventAction -> targets
    action_targets = {}
    for oid, body in by_type[3].items():
        action_targets[oid] = [v for _, v in pick_refs(body, obj_ids, oid)]

    # 4) Event -> actions
    # CAkEvent body 实测格式：id(u32) | scope(u8) | action_ids(u32[])  —— 无 count 字段，
    # 数组长度由 body 长度推出。已验证：len=13 -> 2 个 action，且均在 EventAction 集合内。
    events = {}
    for oid, body in by_type[4].items():
        acts = []
        if len(body) >= 9:
            n = (len(body) - 5) // 4
            if n > 0:
                cand = list(struct.unpack(f"<{n}I", body[5:5 + n * 4]))
                if all(c in by_type[3] for c in cand):
                    acts = cand
        if not acts:
            acts = [v for _, v in pick_refs(body, set(by_type[3].keys()), oid)]
        events[oid] = acts

    return {
        "events": events,
        "actions": action_targets,
        "sounds": sound_to_wem,
        "containers": container_children,
        "resolve": resolve_wems,
        "by_type": by_type,
    }


def main():
    INTER.mkdir(parents=True, exist_ok=True)

    # ---- 收集 wem id 全集
    sfx_wems = {}
    for p in (ROOT / "Audio_SFX").glob("*_audio.bnk"):
        sfx_wems.update(wem_ids_from_bnk(p))
    for p in LOGIC.glob("*/base__*sfx_audio.bnk"):
        sfx_wems.update(wem_ids_from_bnk(p))
    for p in LOGIC.glob("*/skin15__*sfx_audio.bnk"):
        sfx_wems.update(wem_ids_from_bnk(p))

    vo_wems = {}
    for p in LOGIC.glob("*/skin15__*vo_audio.wpk"):
        vo_wems.update(wem_ids_from_wpk(p))
    for p in LOGIC.glob("*/base__*vo_audio.wpk"):
        vo_wems.update(wem_ids_from_wpk(p))

    print(f"wem id 全集：sfx={len(sfx_wems)}  vo={len(vo_wems)}")

    # ---- 事件名（从 bin 扫描结果）
    name_file = LOGIC / "all_event_names.txt"
    names = [l.strip() for l in name_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    name_by_hash = {}
    for n in names:
        name_by_hash.setdefault(fnv1_lower(n), []).append(n)
    print(f"事件名 {len(names)} 个，去重哈希 {len(name_by_hash)} 个")

    # ---- 逐个 bank 解析
    banks = [
        ("sfx/base", LOGIC / "main/base__darius_base_sfx_events.bnk", sfx_wems),
        ("sfx/skin15", LOGIC / "main/skin15__darius_skin15_sfx_events.bnk", sfx_wems),
        ("vo/base", LOGIC / "zh_CN/base__darius_base_vo_events.bnk", vo_wems),
        ("vo/skin15", LOGIC / "zh_CN/skin15__darius_skin15_vo_events.bnk", vo_wems),
    ]

    result = {}
    for tag, path, wems in banks:
        if not path.exists():
            print(f"[SKIP] {tag} 缺失")
            continue
        all_ids = set()
        d = path.read_bytes()
        for cid, off, size, pl in iter_chunks(d):
            if cid == "HIRC":
                for t, oid, body in parse_hirc(pl):
                    all_ids.add(oid)
        g = build_graph(path, wems, all_ids)
        ev = g["events"]
        resolved = 0
        named = 0
        rows = []
        for eid, acts in ev.items():
            wem_set = []
            for a in acts:
                for tgt in g["actions"].get(a, []):
                    wem_set += g["resolve"](tgt)
            wem_set = list(dict.fromkeys(wem_set))
            nm = name_by_hash.get(eid, [])
            if nm:
                named += 1
            if wem_set:
                resolved += 1
            rows.append({"event_id": eid, "names": nm, "actions": acts,
                         "wems": wem_set, "wem_count": len(wem_set)})
        print(f"\n[{tag}] Event {len(ev)} 个 | 反查到名字 {named} 个 | 解析到音频 {resolved} 个")
        for r in rows:
            if r["names"]:
                print(f"   {r['names'][0]:<70} wem x{r['wem_count']}")
        result[tag] = rows

    (INTER / "audio_event_graph.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n已写出 {INTER / 'audio_event_graph.json'}")


if __name__ == "__main__":
    main()
