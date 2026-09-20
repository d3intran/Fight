# -*- coding: utf-8 -*-
"""看斧头网格沿各轴的「质量分布」，判断斧头（刃）在哪一端。"""
import bpy
import sys
import os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = argv[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print("=== %s  meshes=%d" % (os.path.basename(SRC), len(meshes)))
pts = []
for m in meshes:
    for v in m.data.vertices:
        pts.append(m.matrix_world @ v.co)
if not pts:
    print("no verts")
    sys.exit(1)
lo = [min(p[i] for p in pts) for i in range(3)]
hi = [max(p[i] for p in pts) for i in range(3)]
print("bbox min=%s max=%s size=%s" % (
    [round(v, 3) for v in lo], [round(v, 3) for v in hi],
    [round(hi[i] - lo[i], 3) for i in range(3)]))
long_axis = max(range(3), key=lambda i: hi[i] - lo[i])
print("最长轴 = %s (长度 %.3f)" % ("XYZ"[long_axis], hi[long_axis] - lo[long_axis]))

for axis in range(3):
    span = hi[axis] - lo[axis]
    if span <= 1e-6:
        continue
    NB = 10
    cnt = [0] * NB
    cross = [0.0] * NB
    for p in pts:
        b = min(NB - 1, int((p[axis] - lo[axis]) / span * NB))
        cnt[b] += 1
    # 每个 bin 的横向展开（近似截面尺寸）
    other = [i for i in range(3) if i != axis]
    for b in range(NB):
        sub = [p for p in pts if min(NB - 1, int((p[axis] - lo[axis]) / span * NB)) == b]
        if sub:
            cross[b] = max((max(q[o] for q in sub) - min(q[o] for q in sub)) for o in other)
    print("  沿 %s：bin 顶点数 = %s" % ("XYZ"[axis], cnt))
    print("        截面尺寸 = %s" % [round(c, 3) for c in cross])
print("=== DONE ===")
