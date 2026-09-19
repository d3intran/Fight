"""
源/目标骨架结构审计（为重定向制定方案）
用法: blender -b -P plan_01_skel_audit.py -- <FILE> <KIND:glb|fbx> <LABEL>
输出：骨数、根骨、层级树、每骨长度、是否有 twist/ik/helper 骨、静止姿态特征
"""
import bpy, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, KIND, LABEL = argv[0], argv[1], argv[2]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, automatic_bone_orientation=True) if KIND == "fbx" \
    else bpy.ops.import_scene.gltf(filepath=SRC)

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
bones = arm.data.bones
print("=" * 100)
print("### %s   %s" % (LABEL, os.path.basename(SRC)))
print("=" * 100)
print("armature = %s   骨骼数 = %d" % (arm.name, len(bones)))
print("armature matrix_world:")
for r in arm.matrix_world:
    print("   ", ["%.4f" % x for x in r])
roots = [b.name for b in bones if b.parent is None]
print("根骨:", roots)

print()
print("--- 层级树（深度<=4）---")
def walk(b, d=0):
    if d > 4:
        return
    ln = (arm.matrix_world @ b.tail_local - arm.matrix_world @ b.head_local).length
    print("   " + "  " * d + "%-34s len=%.3f" % (b.name, ln))
    for c in b.children:
        walk(c, d + 1)
for r in roots:
    walk(bones[r])

names = [b.name for b in bones]
low = [n.lower() for n in names]
print()
print("--- 特征骨探测 ---")
for kw in ("twist", "roll", "ik", "ctrl", "control", "helper", "jnt", "root", "weapon", "prop",
           "attach", "hand", "foot", "toe", "ball", "clavicle", "shoulder", "thumb", "finger"):
    hits = [names[i] for i, n in enumerate(low) if kw in n]
    print("  %-10s (%2d): %s" % (kw, len(hits), hits[:14]))

# 静止姿态特征：肩宽 / 胯宽 / 身高 / 臂展 / 腿长
def head(n):
    b = bones.get(n)
    return (arm.matrix_world @ b.head_local) if b else None
def tail(n):
    b = bones.get(n)
    return (arm.matrix_world @ b.tail_local) if b else None

def dist(a, b):
    pa, pb = head(a), head(b)
    return (pa - pb).length if (pa and pb) else None

print()
print("--- 静止姿态关键尺寸 ---")
zmax = max((arm.matrix_world @ b.tail_local).z for b in bones)
zmin = min((arm.matrix_world @ b.head_local).z for b in bones)
print("  全身 z 范围: %.4f ~ %.4f  (身高 %.4f)" % (zmin, zmax, zmax - zmin))
for pair in [("L_Hip", "R_Hip"), ("thigh_l", "thigh_r"), ("pelvis", "thigh_l"),
             ("L_Shoulder", "R_Shoulder"), ("upperarm_l", "upperarm_r"),
             ("clavicle_l", "clavicle_r"), ("spine_01", "spine_02"),
             ("L_KneeUpper", "L_Foot"), ("calf_l", "foot_l"), ("thigh_l", "calf_l"),
             ("upperarm_l", "lowerarm_l"), ("lowerarm_l", "hand_l")]:
    d = dist(*pair)
    if d is not None:
        print("  %-30s = %.4f" % ("%s <-> %s" % pair, d))

print()
print("--- 各骨静止朝向（父->子方向 vs 自身 Y 轴夹角，用于判断滚转参考可靠性）---")
bad = []
for b in bones:
    if b.parent is None:
        continue
    pa = arm.matrix_world @ b.parent.head_local
    pb = arm.matrix_world @ b.head_local
    yaxis = (b.matrix_local.to_3x3() @ Vector((0, 1, 0))).normalized()
    v = pb - pa
    if v.length < 1e-6:
        continue
    ang = math.degrees(yaxis.angle(v.normalized()))
    if ang > 30:
        bad.append((b.name, ang))
bad.sort(key=lambda x: -x[1])
print("  偏离 >30° 的骨骼数: %d" % len(bad))
for n, a in bad[:25]:
    print("     %-34s %.1f°" % (n, a))
print("=== DONE ===")
