"""扫描 Darius WAD，列出所有与 音频/语音/技能/角色定义 相关的条目。

用途：为「LOL 音频触发逻辑考古」建立文件清单。
"""
import sys
from pathlib import Path
from cdtb.wad import Wad

WADS = {
    "main": r"E:\WeGameApps\英雄联盟\Game\DATA\FINAL\Champions\Darius.wad.client",
    "zh_CN": r"E:\WeGameApps\英雄联盟\Game\DATA\FINAL\Champions\Darius.zh_CN.wad.client",
    "en_US": r"E:\WeGameApps\英雄联盟\Game\DATA\FINAL\Champions\Darius.en_US.wad.client",
}

KEYWORDS = (".bin", ".bnk", ".wpk", ".wem", ".event", "spell", "audio", "character")


def main():
    for tag, path in WADS.items():
        p = Path(path)
        if not p.exists():
            print(f"[SKIP] {tag}: 不存在 {path}")
            continue
        wad = Wad(path)
        wad.sanitize_paths()
        files = [f for f in wad.files if f.path]
        print(f"\n{'='*90}\n[{tag}] 总条目 {len(files)}\n{'='*90}")

        bins = sorted({f.path for f in files if f.path.lower().endswith(".bin")})
        print(f"--- .bin 文件（{len(bins)}）---")
        for b in bins:
            print("   ", b)

        others = sorted({f.path for f in files
                         if f.path.lower().endswith((".bnk", ".wpk"))})
        print(f"--- .bnk / .wpk（{len(others)}）---")
        for b in others:
            print("   ", b)


if __name__ == "__main__":
    main()
