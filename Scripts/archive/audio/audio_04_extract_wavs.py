r"""把 audio bank 内嵌的 wem 解出为 wav（vgmstream 转码）。

支持两类输入：
  *_audio.bnk —— Wwise bank，含 DIDX/DATA chunk，内嵌 wem
  *_audio.wpk —— Riot 的 wem 包（r3d2），文件名为 wem short id

输出命名保留 wem short id，便于与 bank 图（audio_event_graph.json）对齐。
"""
import struct
import subprocess
import sys
from pathlib import Path

VGM = Path(r"E:\UE\Fight\Scripts\tools\vgmstream\vgmstream-cli.exe")
ROOT = Path(r"E:\UE\Assets\Darius_GodKing_LOL_Original")


def extract_bnk(bnk: Path, out_dir: Path, prefix: str):
    d = bnk.read_bytes()
    i_didx = d.find(b"DIDX")
    i_data = d.find(b"DATA")
    if i_didx == -1 or i_data == -1:
        print(f"  [skip] {bnk.name} 无 DIDX/DATA")
        return 0
    didx_len = struct.unpack("<I", d[i_didx + 4:i_didx + 8])[0]
    count = didx_len // 12
    data_start = i_data + 8
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for i in range(count):
        off = i_didx + 8 + i * 12
        fid, foff, fsize = struct.unpack("<III", d[off:off + 12])
        wem = d[data_start + foff:data_start + foff + fsize]
        tmp = out_dir / f"_tmp_{fid}.wem"
        wav = out_dir / f"{prefix}_{i:02d}_{fid}.wav"
        tmp.write_bytes(wem)
        r = subprocess.run([str(VGM), "-o", str(wav), str(tmp)],
                           capture_output=True)
        tmp.unlink(missing_ok=True)
        if wav.exists():
            n += 1
    print(f"  {bnk.name}: {n}/{count} -> {out_dir}")
    return n


def extract_wpk(wpk: Path, out_dir: Path, prefix: str):
    d = wpk.read_bytes()
    magic, ver, cnt = struct.unpack("<4sII", d[:12])
    offs = struct.unpack(f"<{cnt}I", d[12:12 + cnt * 4])
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for i, off in enumerate(offs):
        doff, dsize, nlen = struct.unpack("<III", d[off:off + 12])
        name = d[off + 12:off + 12 + nlen * 2].decode("utf-16-le").rstrip("\x00")
        wem = d[doff:doff + dsize]
        tmp = out_dir / f"_tmp_{i}.wem"
        wav = out_dir / f"{prefix}_{i:03d}_{Path(name).stem}.wav"
        tmp.write_bytes(wem)
        subprocess.run([str(VGM), "-o", str(wav), str(tmp)], capture_output=True)
        tmp.unlink(missing_ok=True)
        if wav.exists():
            n += 1
    print(f"  {wpk.name}: {n}/{cnt} -> {out_dir}")
    return n


def main():
    logic = ROOT / "Audio_Logic"
    jobs = [
        # (源文件, 输出目录, 前缀)
        (logic / "main/base__darius_base_sfx_audio.bnk", ROOT / "Audio_SFX_Base", "sfxbase"),
        (logic / "main/skin15__darius_skin15_sfx_audio.bnk", ROOT / "Audio_SFX_Skin15", "sfxskin15"),
        (logic / "zh_CN/base__darius_base_vo_audio.wpk", ROOT / "Audio_VO_zh_CN_Base", "vozhbase"),
        (logic / "zh_CN/skin15__darius_skin15_vo_audio.wpk", ROOT / "Audio_VO_zh_CN", "vozh"),
        (logic / "en_US/skin15__darius_skin15_vo_audio.wpk", ROOT / "Audio_VO_en_US", "voen"),
    ]
    total = 0
    for src, out, pref in jobs:
        if not src.exists():
            print(f"  [MISS] {src}")
            continue
        print(f"[{src.name}]")
        if src.suffix == ".bnk":
            total += extract_bnk(src, out, pref)
        else:
            total += extract_wpk(src, out, pref)
    print(f"\n合计导出 {total} 个 wav")


if __name__ == "__main__":
    main()
