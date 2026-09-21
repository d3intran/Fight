"""枚举 UE 内置 MCP（127.0.0.1:8000/mcp）暴露过的 toolset 与工具名。

只读 `Saved/*toolset*.json` / `Saved/*schema*.json`（这些是 ue_mcp.py schema 调用的落盘快照），
不连接编辑器。用来固化「MCP 到底能做哪些事」的能力边界。
"""
import glob
import json
import os
import re

PAT = re.compile(r'"name"\s*:\s*"([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+)"')

for f in sorted(set(glob.glob("Saved/*toolset*.json") + glob.glob("Saved/*schema*.json")
                     + glob.glob("Saved/*types*.json"))):
    raw = open(f, encoding="utf-8").read()
    flat = raw.replace('\\"', '"').replace("\\\\", "\\")
    names = sorted(set(PAT.findall(flat)))
    tsets = sorted({n.split(".")[0] for n in names if "Toolset" in n})
    print("=" * 74)
    print("%-40s  工具数 = %d" % (os.path.basename(f), len(names)))
    if tsets:
        print("  toolset:", ", ".join(tsets))
    for n in names:
        print("    -", n)
