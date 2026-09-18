r"""Wwise SoundBank 结构解析器（轻量，无第三方依赖）。

用途：从 LOL 的 *_events.bnk 中提取
  1. 全部 chunk 结构（BKHD/HIRC/STID/DIDX/DATA...）
  2. STID 里的 event / object 名字表
  3. HIRC 里的对象清单（Event / EventAction / Sound / Container ...）

参考 Wwise 2016.2 bank 格式。
"""
import struct
import sys
from pathlib import Path

HIRC_TYPES = {
    1: "Settings", 2: "Sound", 3: "EventAction", 4: "Event",
    5: "RandomSequenceContainer", 6: "SwitchContainer", 7: "ActorMixer",
    8: "AudioBus", 9: "BlendContainer", 10: "MusicSegment",
    11: "MusicTrack", 12: "MusicSwitchContainer", 13: "MusicPlaylistContainer",
    14: "Attenuation", 15: "DialogueEvent", 16: "FxShareSet", 17: "FxCustom",
    18: "AuxiliaryBus", 19: "LFO", 20: "Envelope", 21: "AudioDevice",
    22: "TimeModulator", 23: "LayerContainer", 24: "MusicTransition",
}


def iter_chunks(data: bytes):
    pos = 0
    n = len(data)
    while pos + 8 <= n:
        cid = data[pos:pos + 4]
        size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        payload = data[pos + 8:pos + 8 + size]
        yield cid.decode("latin1"), pos + 8, size, payload
        pos += 8 + size


def parse_bkhd(payload: bytes):
    if len(payload) < 8:
        return {}
    d = struct.unpack("<I", payload[:4])[0]
    ver = struct.unpack("<I", payload[4:8])[0]
    return {"soundbank_id": d, "version": ver,
            "ver_str": f"{(ver >> 16) & 0xFFFF}.{(ver >> 8) & 0xFF}.{ver & 0xFF}"}


def parse_stid(payload: bytes, verbose=True):
    """STID: 连续条目 { bank_id:u32, str_size:u32, str:char[str_size] }"""
    out = []
    pos = 0
    n = len(payload)
    while pos + 8 <= n:
        bid = struct.unpack("<I", payload[pos:pos + 4])[0]
        slen = struct.unpack("<I", payload[pos + 4:pos + 8])[0]
        pos += 8
        if slen == 0 or pos + slen > n:
            break
        raw = payload[pos:pos + slen]
        pos += slen
        name = raw.split(b"\x00", 1)[0].decode("utf-8", "replace")
        out.append((bid, name))
    return out


def parse_hirc(payload: bytes):
    """HIRC: count:u32, 然后每个对象 { type:u8, size:u32, data }"""
    if len(payload) < 4:
        return []
    count = struct.unpack("<I", payload[:4])[0]
    pos = 4
    objs = []
    n = len(payload)
    for _ in range(count):
        if pos + 5 > n:
            break
        otype = payload[pos]
        osize = struct.unpack("<I", payload[pos + 1:pos + 5])[0]
        body = payload[pos + 5:pos + 5 + osize]
        oid = struct.unpack("<I", body[:4])[0] if len(body) >= 4 else 0
        objs.append((otype, oid, body))
        pos += 5 + osize
    return objs


def analyze(path: Path, dump_hirc=True):
    data = path.read_bytes()
    print(f"\n{'='*100}\n{path.name}  ({len(data):,} bytes)\n{'='*100}")
    chunks = list(iter_chunks(data))
    print("--- chunks ---")
    for cid, off, size, _ in chunks:
        print(f"   {cid}  offset={off:<10} size={size:,}")

    names = {}
    for cid, off, size, payload in chunks:
        if cid == "BKHD":
            info = parse_bkhd(payload)
            print(f"   BKHD: {info}")
        elif cid == "STID":
            stid = parse_stid(payload)
            names = {bid: nm for bid, nm in stid}
            print(f"\n--- STID 名字表（{len(stid)} 条）---")
            for bid, nm in stid:
                print(f"   {bid:>12} (0x{bid:08X})  {nm}")
        elif cid == "HIRC" and dump_hirc:
            objs = parse_hirc(payload)
            from collections import Counter
            cnt = Counter(HIRC_TYPES.get(t, f"?{t}") for t, _, _ in objs)
            print(f"\n--- HIRC 对象（{len(objs)} 个）---")
            for k, v in cnt.most_common():
                print(f"   {k:<26} x{v}")
            print(f"\n--- HIRC 明细（前 60）---")
            for i, (t, oid, body) in enumerate(objs[:60]):
                nm = names.get(oid, "")
                print(f"   [{i:>3}] type={t:<3} {HIRC_TYPES.get(t,'?'):<24} id={oid:<12} {nm}")
    return chunks, names


if __name__ == "__main__":
    for p in sys.argv[1:]:
        analyze(Path(p))
