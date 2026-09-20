"""Blender 探查 2XKO 目标骨架"""
import bpy, sys
from mathutils import Vector

SRC = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, automatic_bone_orientation=True)

arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print("armatures:", [a.name for a in arms])
print("meshes:", [(m.name, len(m.data.vertices), len(m.data.materials)) for m in meshes])
arm = arms[0]
print("armature matrix_world:")
print(arm.matrix_world)
print("bone count:", len(arm.data.bones))
print("root bones:", [b.name for b in arm.data.bones if b.parent is None])

keys = ["root", "pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
        "thigh_l", "calf_l", "foot_l", "ball_l", "toe_l",
        "thigh_r", "calf_r", "foot_r", "ball_r", "toe_r",
        "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
        "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r", "weapon_jnt"]
for k in keys:
    b = arm.data.bones.get(k)
    if not b:
        print(f"{k}: <missing>")
        continue
    h = arm.matrix_world @ b.head_local
    t = arm.matrix_world @ b.tail_local
    v = (t - h)
    print(f"{k:14s} head=({h.x:8.2f},{h.y:8.2f},{h.z:8.2f}) len={v.length:7.2f} dir=({v.normalized().x:6.3f},{v.normalized().y:6.3f},{v.normalized().z:6.3f})")

# 网格包围盒
dg = bpy.context.evaluated_depsgraph_get()
mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
for m in meshes:
    ev = m.evaluated_get(dg)
    for v in ev.data.vertices:
        w = ev.matrix_world @ v.co
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
print("mesh bbox min:", tuple(round(v,2) for v in mn), "max:", tuple(round(v,2) for v in mx))
print("=== DONE ===")
