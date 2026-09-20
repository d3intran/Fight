"""确定 LOL 源模型的前后方向（独立于任何假设）：
   披风必然在身后、脚尖必然在身前 —— 用这两个锚点定死 forward 的符号。
用法: blender -b -P plan_04_facing.py -- <SRC_GLB>"""
import bpy, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]

def H(n, rest=True):
    b = arm.data.bones.get(n)
    if not b:
        return None
    return arm.matrix_world @ (b.head_local if rest else b.tail_local)

pv = H("Pelvis", False)
print("Pelvis(head) = %s" % ["%.3f" % v for v in H("Pelvis")])
print("Pelvis(tail) = %s" % ["%.3f" % v for v in pv])
print()
print("%-24s %10s %10s %10s" % ("骨骼", "X", "Y", "Z   (相对 Pelvis)"))
print("-" * 62)
for n in ["Neck", "Head", "Cape", "C_Cape1", "C_Cape2", "C_Cape3",
          "L_Cape1", "R_Cape1", "L_Toe", "R_Toe", "L_Foot", "R_Foot",
          "L_KneeLower", "L_KneeUpper", "Axe_Handle", "Axe_Head", "Weapon",
          "SnapWeapon2Hand", "L_Shoulder", "R_Shoulder", "Lion_Root",
          "Throne", "Gem", "L_Hand", "R_Hand"]:
    p = H(n)
    if p is None:
        print("%-24s  (无此骨)" % n)
        continue
    d = p - pv
    print("%-24s %10.3f %10.3f %10.3f" % (n, d.x, d.y, d.z))

# 网格层面：披风网格 vs 躯干网格的 Y 范围（完全独立于骨骼）
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print()
print("--- 网格对象 Y 范围（相对 Pelvis）---")
for o in sorted(meshes, key=lambda x: x.name):
    ys = [(o.matrix_world @ v.co).y for v in o.data.vertices]
    if not ys:
        continue
    print("%-30s Y: %8.3f ~ %8.3f" % (o.name, min(ys) - pv.y, max(ys) - pv.y))
print("=== DONE ===")
