r"""解析 LOL bin（PROP 格式）为 JSON，并按关键词搜索音频相关字段。

用途：从 darius.bin / skin15.bin 中挖出音效与语音的触发配置。
"""
import json
import re
import sys
from pathlib import Path

from cdtb.binfile import BinFile


def _fallback(o):
    """BinPathValue 等 cdtb 自定义类型统一降级为 str"""
    for attr in ("value", "path", "name"):
        v = getattr(o, attr, None)
        if v is not None and not callable(v):
            return v
    return repr(o)


def load_json(path: Path):
    bf = BinFile(str(path))
    return json.loads(json.dumps(bf.to_serializable(), default=_fallback, ensure_ascii=False))


def walk(node, path=""):
    """深度遍历，yield (路径, 值)"""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, node


def main():
    bin_path = Path(sys.argv[1])
    out_json = Path(sys.argv[2]) if len(sys.argv) > 2 else bin_path.with_suffix(".json")
    keywords = sys.argv[3].split(",") if len(sys.argv) > 3 else [
        "audio", "event", "vo", "sound", "sfx", "music", "bank", "voice", "emote", "spell",
    ]

    data = load_json(bin_path)
    out_json.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"已导出 JSON: {out_json}  ({out_json.stat().st_size:,} bytes)")

    print(f"\n{'='*100}\n顶层条目\n{'='*100}")
    for k, v in data.items():
        if k.startswith("__"):
            print(f"   {k}: {v}")
            continue
        kind = type(v).__name__
        n = len(v) if isinstance(v, (dict, list)) else ""
        print(f"   {k:<40} {kind:<6} {n}")

    print(f"\n{'='*100}\n含关键词的字段路径（去重后）\n{'='*100}")
    hits = {}
    for p, val in walk(data):
        low = p.lower()
        if any(kw in low for kw in keywords):
            hits.setdefault(p, []).append(val)

    for p in sorted(hits):
        vals = hits[p]
        uniq = []
        for v in vals:
            if v not in uniq:
                uniq.append(v)
        show = uniq[:8]
        extra = f"  ... (+{len(uniq)-8} 种)" if len(uniq) > 8 else ""
        print(f"   {p}   x{len(vals)}")
        for v in show:
            s = repr(v)
            print(f"        {s[:150]}{'...' if len(s)>150 else ''}{extra}")


if __name__ == "__main__":
    main()
