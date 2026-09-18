"""诊断：逐个网格对象统计材质、顶点数、包围盒，以及「地面以下」几何的分布"""
import bpy, sys
from mathutils import Vector

SRC = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, automatic_bone_orientation=True)

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
print("armature:", arm.name, "bones:", len(arm.data.bones))
print()
print(f"{'object':32s} {'verts':>7s} {'material':34s}  bbox(min)                 bbox(max)")
print("-" * 130)
below_total = {}
for o in sorted([x for x in bpy.data.objects if x.type == 'MESH'], key=lambda x: x.name):
    mats = [s.material.name if s.material else "(none)" for s in o.material_slots]
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    n_below = 0
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
        if w.z < -0.02:
            n_below += 1
    below_total[o.name] = n_below
    print(f"{o.name:32s} {len(o.data.vertices):7d} {','.join(mats):34s}  "
          f"({mn.x:6.2f},{mn.y:6.2f},{mn.z:6.2f})  ({mx.x:6.2f},{mx.y:6.2f},{mx.z:6.2f})   地面以下顶点={n_below}")

print()
print("=== 地面以下 (z<-0.02) 顶点汇总 ===")
for k, v in sorted(below_total.items(), key=lambda kv: -kv[1]):
    if v:
        print(f"   {k}: {v}")
print()
print("=== 全身顶点 z 直方图 (每 0.25 一档，只列 z<0.6 的部分) ===")
import collections
hist = collections.Counter()
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    for v in o.data.vertices:
        z = (o.matrix_world @ v.co).z
        if z < 0.6:
            hist[round(z * 4) / 4.0] += 1
for z in sorted(hist):
    print(f"   z≈{z:6.2f}: {'#' * min(60, hist[z] // 20)} ({hist[z]})")
print("=== DONE ===")
