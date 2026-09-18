"""Blender 诊断：打印骨架变换与关键骨骼的动画世界坐标"""
import bpy, sys, math
from mathutils import Vector

SRC = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
sc = bpy.context.scene
if arm.animation_data and arm.animation_data.action:
    sc.frame_start = int(arm.animation_data.action.frame_range[0])
    sc.frame_end = int(arm.animation_data.action.frame_range[1])
print("arm.matrix_world:")
print(arm.matrix_world)
print("arm.scale:", arm.scale, "loc:", arm.location, "rot:", arm.rotation_euler)
print("scene fps:", sc.render.fps)

keys = ["Root", "Pelvis", "Spine1", "Spine2", "Neck", "Head",
        "L_Hip", "L_KneeUpper", "L_KneeLower", "L_Foot", "L_Toe",
        "R_Hip", "R_KneeUpper", "R_KneeLower", "R_Foot", "R_Toe",
        "L_Clavicle", "L_Shoulder", "L_Elbow", "L_Hand",
        "R_Clavicle", "R_Shoulder", "R_Elbow", "R_Hand", "SnapWeapon"]
for f in [0, 7, 14, 21]:
    sc.frame_set(f)
    bpy.context.view_layer.update()
    print(f"--- frame {f} ---")
    for k in keys:
        pb = arm.pose.bones.get(k)
        if pb is None:
            print(f"   {k}: <missing>")
            continue
        w = arm.matrix_world @ pb.head
        print(f"   {k:16s} world=({w.x:8.2f},{w.y:8.2f},{w.z:8.2f})")

# 网格评估后的真实包围盒
dg = bpy.context.evaluated_depsgraph_get()
sc.frame_set(0)
mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    ev = o.evaluated_get(dg)
    for v in ev.data.vertices:
        w = ev.matrix_world @ v.co
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
print("all mesh bounds min:", tuple(round(v,2) for v in mn), "max:", tuple(round(v,2) for v in mx))
print("=== DONE ===")
