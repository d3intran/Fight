"""
战斧几何完整性审计（Blender 无头）
用法: blender -b -P axe_03_geom_audit.py -- <FBX> <LABEL>

输出：每个网格对象的 顶点/面/材质/世界包围盒；
对"斧头对象"额外给出沿长轴的顶点+径向分布直方图（用于判断斧刃是否还在）。
"""
import bpy, sys, os, collections
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC = argv[0]
LABEL = argv[1] if len(argv) > 1 else os.path.basename(SRC)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, automatic_bone_orientation=True)

print("=" * 100)
print("### %s  ::  %s" % (LABEL, SRC))
print("=" * 100)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
if arms:
    print("ARMATURE: %s  bones=%d" % (arms[0].name, len(arms[0].data.bones)))
    wb = [b.name for b in arms[0].data.bones if 'weapon' in b.name.lower() or 'axe' in b.name.lower()]
    print("  weapon-ish bones: %s" % wb)

print("-" * 100)
print("%-34s %8s %8s %-46s %s" % ("object", "verts", "faces", "materials", "world bbox (x,y,z) min -> max"))
print("-" * 100)

axe_like = []
for o in sorted(meshes, key=lambda x: x.name):
    mats = [s.material.name if s.material else "(none)" for s in o.material_slots]
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    if mn.x > 1e8:
        mn = mx = Vector((0, 0, 0))
    size = mx - mn
    print("%-34s %8d %8d %-46s (%.2f,%.2f,%.2f)->(%.2f,%.2f,%.2f) size=(%.2f,%.2f,%.2f)" % (
        o.name, len(o.data.vertices), len(o.data.polygons), ",".join(mats)[:45],
        mn.x, mn.y, mn.z, mx.x, mx.y, mx.z, size.x, size.y, size.z))
    if any('axe' in m.lower() for m in mats) or 'axe' in o.name.lower():
        axe_like.append(o)

def hist(o, tag):
    verts = [o.matrix_world @ v.co for v in o.data.vertices]
    if not verts:
        print("  (%s) 无顶点" % tag); return
    mn = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
    mx = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
    size = mx - mn
    axis = max(range(3), key=lambda i: size[i])
    print("")
    print(">>> 长轴分布 [%s] 对象=%s 轴=%s 长度=%.3f m" % (tag, o.name, "XYZ"[axis], size[axis]))
    # 轴中心线上的包围盒中心
    ctr = (mn + mx) * 0.5
    bins = 12
    cnt = collections.Counter()
    rad = {}
    for w in verts:
        t = (w[axis] - mn[axis]) / size[axis] if size[axis] > 1e-9 else 0.0
        b = min(bins - 1, int(t * bins))
        cnt[b] += 1
        others = [i for i in range(3) if i != axis]
        r = ((w[others[0]] - ctr[others[0]]) ** 2 + (w[others[1]] - ctr[others[1]]) ** 2) ** 0.5
        rad[b] = max(rad.get(b, 0.0), r)
    for b in range(bins):
        a0 = mn[axis] + size[axis] * b / bins
        a1 = mn[axis] + size[axis] * (b + 1) / bins
        print("   bin%02d  %s %.3f~%.3f  顶点=%6d  最大径向半径=%.3f m  %s" % (
            b, "XYZ"[axis], a0, a1, cnt[b], rad.get(b, 0.0), "#" * min(50, cnt[b] // 120)))

if not axe_like:
    print("")
    print("!! 未发现任何以 axe 命名的材质/对象")
for o in axe_like:
    hist(o, "axe-like")

print("")
print("总顶点: %d" % sum(len(o.data.vertices) for o in meshes))
print("=== DONE ===")
