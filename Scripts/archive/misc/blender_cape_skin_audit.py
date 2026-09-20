"""
Blender 无头：审计披风蒙皮归属（披风顶点到底受哪些骨影响）
用法: blender -b -P <本文件> -- <FBX>
"""
import bpy
import sys
from collections import Counter, defaultdict

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = argv[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE']
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print("### 导入 %s" % SRC)
print("### armature=%d  mesh=%d" % (len(arm), len(meshes)))

gname = [g.name for g in arm[0].pose.bones] if arm else []
cape_bones = [n for n in gname if "cape" in n.lower()]
print("### 骨架骨数=%d  披风骨=%d" % (len(gname), len(cape_bones)))

for me in meshes:
    gidx = {g.index: g.name for g in me.vertex_groups}
    capeg = set(n for n in gidx.values() if "cape" in n.lower())
    print("\n=== 网格 %s  顶点=%d  面=%d  组=%d  材质槽=%s" % (
        me.name, len(me.data.vertices), len(me.data.polygons), len(gidx),
        [s.material.name if s.material else None for s in me.material_slots]))
    dom = Counter()
    cape_w = defaultdict(float)
    n_with_cape = 0
    n_cape_dominant = 0
    for v in me.data.vertices:
        if not v.groups:
            dom["<无权重>"] += 1
            continue
        ws = [(gidx.get(g.group, "?"), g.weight) for g in v.groups]
        bn, bw = max(ws, key=lambda kv: kv[1])
        dom[bn] += 1
        cw = sum(w for n, w in ws if n in capeg)
        if cw > 1e-6:
            n_with_cape += 1
        if bn in capeg:
            n_cape_dominant += 1
        for n, w in ws:
            if n in capeg:
                cape_w[n] += w
    print("--- 主权重归属 TOP15: %s" % dom.most_common(15))
    print("--- 受披风骨影响的顶点数 = %d / %d (%.1f%%)" % (
        n_with_cape, len(me.data.vertices), 100.0 * n_with_cape / max(1, len(me.data.vertices))))
    print("--- 披风骨为主权重的顶点数 = %d" % n_cape_dominant)
    print("--- 披风骨权重累计(按骨) TOP12: %s" % sorted(cape_w.items(), key=lambda kv: -kv[1])[:12])

# 披风链几何长度（决定碰撞胶囊多长）
if arm:
    print("\n=== 披风链 rest 长度 (cm 按 FBX 单位) ===")
    for chain in ("cape_chain_01_l", "cape_chain_01_m", "cape_chain_01_r"):
        cur = chain
        segs = []
        while cur:
            b = arm[0].data.bones.get(cur)
            if b is None:
                break
            segs.append((cur, round(b.length * 100, 2)))
            kids = [c.name for c in b.children if "cape" in c.name.lower()]
            cur = kids[0] if kids else None
        print("   %s" % segs)
print("### DONE")
