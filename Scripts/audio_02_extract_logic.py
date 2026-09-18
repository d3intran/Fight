r"""提取 LOL 德莱厄斯「音频触发逻辑」相关的全部原始文件。

补齐 extract_godking_assets.py 的遗漏：
  - data/characters/darius/darius.bin        ← 角色主定义（spells / VO 配置）
  - assets/.../*_sfx_events.bnk              ← 音效事件表（base + skin15）
  - assets/.../*_vo_events.bnk               ← 语音事件表（base + skin15）★ 之前完全没拿
  - assets/.../*_vo_audio.wpk                ← 语音音频包（zh/en）

输出到 E:\UE\Assets\Darius_GodKing_LOL_Original\Audio_Logic\
"""
import os
from pathlib import Path
from cdtb.wad import Wad

OUT = Path(r"E:\UE\Assets\Darius_GodKing_LOL_Original\Audio_Logic")

WADS = {
    "main": (r"E:\WeGameApps\英雄联盟\Game\DATA\FINAL\Champions\Darius.wad.client", None),
    "zh_CN": (r"E:\WeGameApps\英雄联盟\Game\DATA\FINAL\Champions\Darius.zh_CN.wad.client", "zh_CN"),
    "en_US": (r"E:\WeGameApps\英雄联盟\Game\DATA\FINAL\Champions\Darius.en_US.wad.client", "en_US"),
}


def want(path: str) -> bool:
    p = path.lower().replace("\\", "/")
    # 角色主定义
    if p.endswith("characters/darius/darius.bin"):
        return True
    # 神王皮肤定义（含 VO/粒子覆盖）
    if p.endswith("characters/darius/skins/skin15.bin"):
        return True
    # 事件表：只取 base 与 skin15
    if "_events.bnk" in p and ("/base/" in p or "/skin15/" in p):
        return True
    # 音频包 / 语音包：base + skin15
    if p.endswith((".wpk", "_audio.bnk")) and ("/base/" in p or "/skin15/" in p):
        return True
    return False


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for tag, (wad_path, locale) in WADS.items():
        if not Path(wad_path).exists():
            print(f"[SKIP] {tag} 不存在")
            continue
        wad = Wad(wad_path)
        wad.sanitize_paths()
        targets = [f for f in wad.files if f.path and want(f.path)]
        print(f"\n[{tag}] 命中 {len(targets)} 个文件")
        with open(wad_path, "rb") as f_in:
            for f in targets:
                rel = f.path.replace("\\", "/").lstrip("/")
                fname = os.path.basename(rel)
                sub = locale or "main"
                # 同名的 base/skin15 加前缀避免冲突
                stem = fname
                if "_base_" in stem:
                    stem = "base__" + stem
                elif "_skin15_" in stem:
                    stem = "skin15__" + stem
                dest = OUT / sub / stem
                dest.parent.mkdir(parents=True, exist_ok=True)
                data = f.read_data(f_in)
                dest.write_bytes(data)
                size = len(data)
                manifest.append((tag, rel, str(dest.relative_to(OUT)), size))
                print(f"   {size:>9,} B  -> {dest.relative_to(OUT)}")

    # 写清单
    with open(OUT / "MANIFEST.txt", "w", encoding="utf-8") as fo:
        for tag, rel, dest, size in manifest:
            fo.write(f"{tag}\t{size}\t{dest}\t{rel}\n")
    print(f"\n共导出 {len(manifest)} 个文件 -> {OUT}")


if __name__ == "__main__":
    main()
