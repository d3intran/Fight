# -*- coding: utf-8 -*-
"""探针：定位「骨骼在 y≈-104、网格在 0 附近」的坐标系错位。

用法: blender -b -P <本脚本> -- <FBX> [--auto]
    --auto 时用 automatic_bone_orientation=True 导入（对照）

输出：骨架对象变换、关键骨 head/matrix 的 world 位置、以及网格**求值后**的 world 包围盒。
"""
import bpy
import sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = argv[0]
AUTO = "--auto" in argv

bpy.ops.wm.read_factory_settings(use_empty=True)
if AUTO:
    bpy.ops.import_scene.fbx(filepath=SRC, automatic_bone_orientation=True)
else:
    bpy.ops.import_scene.fbx(filepath=SRC)

arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print("=== %s（auto=%s）===" % (SRC.split("\\")[-1], AUTO))
print("armature=%d mesh=%d objects=%d" % (len(arms), len(meshes), len(bpy.data.objects)))
for o in bpy.data.objects:
    print("   obj %-40s type=%-9s parent=%s" % (o.name, o.type, o.parent.name if o.parent else "-"))

for a in arms:
    print("ARM %s" % a.name)
    print("   matrix_world loc=%s scale=%s  bones=%d"
          % ([round(v, 3) for v in a.matrix_world.translation],
             [round(v, 3) for v in a.matrix_world.to_scale()], len(a.data.bones)))
    for n in ("root", "pelvis", "spine_01", "head", "thigh_l", "foot_l"):
        pb = a.pose.bones.get(n)
        if pb is None:
            print("   %-10s (骨架中无此骨)" % n)
            continue
        wh = a.matrix_world @ pb.head
        mt = (a.matrix_world @ pb.matrix).translation
        print("   %-10s head_world=%s  matrix_t=%s"
              % (n, [round(v, 3) for v in wh], [round(v, 3) for v in mt]))

dg = bpy.context.evaluated_depsgraph_get()
for m in meshes:
    try:
        me = m.evaluated_get(dg)
        ms = me.to_mesh()
        vs = [m.matrix_world @ v.co for v in ms.vertices]
        me.to_mesh_clear()
    except Exception as e:
        print("   (evaluated failed: %s)" % e)
        vs = [m.matrix_world @ v.co for v in m.data.vertices]
    if not vs:
        continue
    lo = [min(v[i] for v in vs) for i in range(3)]
    hi = [max(v[i] for v in vs) for i in range(3)]
    print("MESH %-34s verts=%-7d eval_bbox=%s..%s"
          % (m.name, len(vs), [round(x, 2) for x in lo], [round(x, 2) for x in hi]))
print("=== DONE ===")
