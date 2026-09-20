"""
算披风「钉住行」（肩部那圈）的顶点索引，输出 JSON 给布料图的 Selection 节点用。

判据（两条取并集，都基于骨架保证的信息，不靠猜）：
  A) 权重：`cape_chain_01_*` 上的权重和 > 0.5（第一段链骨驱动的顶点）
  B) 高度：披风 sheet 顶部 6% 高度带内的顶点（防止权重稀疏时漏掉最上一圈）
输出：Saved/cape_pin_indices.json  { "indices": [...], "count": n, "total": N, "z_range": [zmin,zmax] }
用法: blender -b -P <本文件> -- <FBX> <OUT_JSON>
"""
import json
import os
import sys
import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
IN_FBX, OUT_JSON = argv[0], argv[1]
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=IN_FBX)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = [o for o in bpy.data.objects if o.type == 'MESH']


def mats(o):
    return " ".join(s.material.name for s in o.material_slots if s.material)


cape = next(o for o in meshes if "Cape" in mats(o))
M = arm.matrix_world.inverted() @ cape.matrix_world
P = np.asarray([[*(M @ v.co)] for v in cape.data.vertices], dtype=np.float32)
zmin, zmax = float(P[:, 2].min()), float(P[:, 2].max())
gidx = {g.index: g.name for g in cape.vertex_groups}
top_bones = {i for i, n in gidx.items() if n.startswith("cape_chain_01_")}
print("### 网格 %s 顶点 %d   z=[%.3f, %.3f]" % (cape.name, len(P), zmin, zmax))
print("### 第一段链骨顶点组: %s" % [gidx[i] for i in sorted(top_bones)])

by_weight = set()
for v in cape.data.vertices:
    w = sum(g.weight for g in v.groups if g.group in top_bones)
    if w > 0.5:
        by_weight.add(v.index)

z_thr = zmin + (zmax - zmin) * 0.94
by_height = {i for i in range(len(P)) if P[i, 2] >= z_thr}

sel = by_weight | by_height
print("### 权重判据 %d 个；高度判据(z>=%.3f) %d 个；并集 %d / %d (%.1f%%)" % (
    len(by_weight), z_thr, len(by_height), len(sel), len(P), 100.0 * len(sel) / len(P)))

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump({"indices": sorted(sel), "count": len(sel), "total": len(P),
               "z_range": [zmin, zmax], "z_threshold": z_thr,
               "by_weight": sorted(by_weight), "by_height": sorted(by_height)}, f)
print("### 写出 %s" % OUT_JSON)
print("### DONE")
