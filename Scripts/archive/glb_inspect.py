"""解析 GLB 的 JSON chunk，输出骨骼节点名、层级、动画名与时长，无需任何 3D 库。"""
import json
import struct
import sys
import os


def read_glb_json(path):
    with open(path, "rb") as f:
        magic, ver, total = struct.unpack("<III", f.read(12))
        assert magic == 0x46546C67, "not a glb"
        while True:
            hdr = f.read(8)
            if len(hdr) < 8:
                break
            clen, ctype = struct.unpack("<II", hdr)
            data = f.read(clen)
            if ctype == 0x4E4F534A:
                return json.loads(data.decode("utf-8"))
    return None


def dump(path):
    g = read_glb_json(path)
    nodes = g.get("nodes", [])
    skins = g.get("skins", [])
    anims = g.get("animations", [])
    meshes = g.get("meshes", [])
    print("=" * 78)
    print("FILE:", os.path.basename(path))
    print(f"  nodes={len(nodes)} meshes={len(meshes)} skins={len(skins)} animations={len(anims)}")
    for i, s in enumerate(skins):
        joints = s.get("joints", [])
        print(f"  skin[{i}] name={s.get('name')} joints={len(joints)}")
        names = [nodes[j].get("name", "?") for j in joints]
        print("   joint names:", names[:40])
        # 打印前 3 层的树
        parent = {}
        for idx, n in enumerate(nodes):
            for c in n.get("children", []):
                parent[c] = idx

        def depth(i):
            d = 0
            while i in parent:
                i = parent[i]
                d += 1
            return d

        tree = sorted(joints, key=depth)
        for j in tree[:80]:
            print("     " + "  " * depth(j) + f"{nodes[j].get('name')} (#{j})")
    for i, a in enumerate(anims):
        ch = a.get("channels", [])
        print(f"  anim[{i}] name={a.get('name')} channels={len(ch)} samplers={len(a.get('samplers', []))}")
        acc = g.get("accessors", [])
        dur = 0.0
        for s in a.get("samplers", [])[:3]:
            ai = s.get("input")
            if ai is not None and ai < len(acc):
                mx = acc[ai].get("max")
                if mx:
                    dur = max(dur, mx[0])
        print(f"     approx duration: {dur:.3f}s")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        dump(p)
