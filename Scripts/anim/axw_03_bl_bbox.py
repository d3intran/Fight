# -*- coding: utf-8 -*-
"""逐帧网格包围盒审计：判断角色是否沉入地面。只读，不改任何资产。"""
import bpy
import sys
import os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = argv[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)

arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print("=== %s" % os.path.basename(SRC))
print("armatures=%d meshes=%d" % (len(arms), len(meshes)))
for a in arms:
    print("  ARM %-46s loc=%s rot=%s scale=%s" % (
        a.name,
        [round(v, 3) for v in a.matrix_world.translation],
        [round(v, 2) for v in a.rotation_euler],
        [round(v, 4) for v in a.matrix_world.to_scale()]))
for m in meshes:
    print("  MESH %-46s verts=%d mats=%s" % (
        m.name, len(m.data.vertices),
        [s.material.name if s.material else "-" for s in m.material_slots][:4]))

arm = arms[0] if arms else None
if arm is None:
    sys.exit(1)

acts = list(bpy.data.actions)
print("  actions = %s" % [(a.name, tuple(round(x) for x in a.frame_range)) for a in acts])
sc = bpy.context.scene
f0, f1 = 0, 0
if arm.animation_data and arm.animation_data.action:
    r = arm.animation_data.action.frame_range
    f0, f1 = int(r[0]), int(r[1])
print("  action frame range = %d..%d" % (f0, f1))

bones = ["root", "pelvis", "foot_l", "foot_r", "ball_l", "ball_r", "head", "spine_03"]
bones = [b for b in bones if b in arm.pose.bones]
print("  probed bones = %s" % bones)

dg = bpy.context.evaluated_depsgraph_get()


def bbox_at(f):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    dgl = bpy.context.evaluated_depsgraph_get()
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for m in meshes:
        me = m.evaluated_get(dgl)
        try:
            ms = me.to_mesh()
            for v in ms.vertices:
                w = m.matrix_world @ v.co
                for i in range(3):
                    lo[i] = min(lo[i], w[i])
                    hi[i] = max(hi[i], w[i])
            me.to_mesh_clear()
        except Exception as e:
            print("   eval fail %s" % e)
    return lo, hi


step = max(1, (f1 - f0) // 12)
print("  frame | mesh bbox min(x,y,z)          | max z  | pelvis z | foot_l z | foot_r z")
for f in range(f0, f1 + 1, step):
    lo, hi = bbox_at(f)
    pz = (arm.matrix_world @ arm.pose.bones["pelvis"].matrix).translation.z if "pelvis" in arm.pose.bones else 0
    flz = (arm.matrix_world @ arm.pose.bones["foot_l"].matrix).translation.z if "foot_l" in arm.pose.bones else 0
    frz = (arm.matrix_world @ arm.pose.bones["foot_r"].matrix).translation.z if "foot_r" in arm.pose.bones else 0
    print("  f%-4d | %-28s | %7.3f | %8.3f | %8.3f | %8.3f" % (
        f, [round(v, 3) for v in lo], hi[2], pz, flz, frz))

print("=== DONE ===")
