import json, struct, sys, os

def glb_json(path):
    with open(path, "rb") as f:
        struct.unpack("<III", f.read(12))
        while True:
            hdr = f.read(8)
            if len(hdr) < 8: break
            clen, ctype = struct.unpack("<II", hdr)
            data = f.read(clen)
            if ctype == 0x4E4F534A:
                return json.loads(data.decode("utf-8"))

for p in sys.argv[1:]:
    g = glb_json(p)
    acc = g.get("accessors", [])
    print("=" * 70)
    print(os.path.basename(p), "| nodes:", len(g.get("nodes", [])), "| animations:", len(g.get("animations", [])))
    for i, a in enumerate(g.get("animations", [])):
        dur = 0.0
        for s in a.get("samplers", []):
            ai = s.get("input")
            if ai is not None and ai < len(acc) and acc[ai].get("max"):
                dur = max(dur, acc[ai]["max"][0])
        print(f"  [{i:02d}] {a.get('name'):42s} {dur:6.3f}s  channels={len(a.get('channels', []))}")
