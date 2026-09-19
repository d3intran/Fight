"""Blender 探查：打印 LOL 骨架中关键链的父子关系与静止姿态朝向"""
import bpy, sys, math
from mathutils import Vector

SRC = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]

keys = ["Root", "Pelvis", "Spine1", "Spine2", "Neck", "Head",
        "L_Hip", "L_KneeUpper", "L_KneeLower", "L_Foot", "L_Toe",
        "R_Hip", "R_KneeUpper", "R_KneeLower", "R_Foot", "R_Toe",
        "L_Clavicle", "L_Shoulder", "L_ElbowUpper", "L_Elbow", "L_Hand",
        "R_Clavicle", "R_Shoulder", "R_ElbowUpper", "R_Elbow", "R_Hand",
        "SnapWeapon", "L_Cape1", "C_Cape1", "R_Cape1"]

def chain(b):
    out = []
    cur = b
    while cur:
        out.append(cur.name)
        cur = cur.parent
    return " < ".join(out)

for k in keys:
    b = arm.data.bones.get(k)
    if not b:
        print(f"{k}: <missing>")
        continue
    v = (b.tail_local - b.head_local).normalized()
    print(f"{k:14s} len={ (b.tail_local-b.head_local).length:7.2f}  dir=({v.x:6.3f},{v.y:6.3f},{v.z:6.3f})  chain: {chain(b)}")

print()
print("=== 所有根骨骼 ===")
for b in arm.data.bones:
    if b.parent is None:
        print("  ", b.name)
print("=== 骨骼总数 ===", len(arm.data.bones))
print("=== armature matrix ===")
print(arm.matrix_world)
print("=== DONE ===")
