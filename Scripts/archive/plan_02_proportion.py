"""
源(LOL) vs 目标(2XKO) 比例对照 —— 为重定向的步幅/缩放策略提供硬数据
用法: blender -b -P plan_02_proportion.py -- <SRC_GLB> <TGT_FBX>
"""
import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, TGT = argv[0], argv[1]

def imp(p, k):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=p, automatic_bone_orientation=True) if k == "fbx" \
        else bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == 'ARMATURE'][0]

bpy.ops.wm.read_factory_settings(use_empty=True)
src = imp(SRC, "glb")
tgt = imp(TGT, "fbx")

def H(a, n):
    b = a.data.bones.get(n)
    return (a.matrix_world @ b.head_local) if b else None

def d(a, n1, n2):
    p1, p2 = H(a, n1), H(a, n2)
    return (p1 - p2).length if (p1 and p2) else None

# ---- LOL 身体主链名称探测 ----
print("--- LOL 身体主链候选名 ---")
for b in src.data.bones:
    nm = b.name
    if any(k in nm for k in ("Elbow", "Hand", "Shoulder", "Knee", "Foot", "Toe", "Spine",
                             "Pelvis", "Head", "Neck", "Hip", "Clavicle")) and "Lion" not in nm \
            and "Buffbone" not in nm and "BuffBone" not in nm and "Pad" not in nm:
        p = b.parent.name if b.parent else "-"
        print("   %-26s parent=%-22s len=%.3f" % (nm, p, b.length))

def chain_len(a, names):
    tot, miss = 0.0, []
    for i in range(len(names) - 1):
        v = d(a, names[i], names[i + 1])
        if v is None:
            miss.append(names[i] + "/" + names[i + 1])
        else:
            tot += v
    return tot, miss

print()
print("=" * 92)
print("%-26s %14s %14s %10s" % ("度量", "LOL源", "2XKO目标", "比值(目标/源)"))
print("=" * 92)

PAIRS = [
    ("身高(toe->head)",        ("L_Toe", "Head"),            ("toe_l", "head")),
    ("腿长(hip->ankle)",       ("L_Hip", "L_Foot"),          ("thigh_l", "foot_l")),
    ("  大腿(hip->knee)",      ("L_Hip", "L_KneeUpper"),     ("thigh_l", "calf_l")),
    ("  小腿(knee->ankle)",    ("L_KneeUpper", "L_Foot"),    ("calf_l", "foot_l")),
    ("脚长(ankle->toe)",       ("L_Foot", "L_Toe"),          ("foot_l", "toe_l")),
    ("臂长(shoulder->wrist)",  ("L_Shoulder", "L_Hand"),     ("upperarm_l", "hand_l")),
    ("  上臂",                 ("L_Shoulder", "L_Elbow"),    ("upperarm_l", "lowerarm_l")),
    ("  前臂",                 ("L_Elbow", "L_Hand"),        ("lowerarm_l", "hand_l")),
    ("肩宽(左右肩)",           ("L_Shoulder", "R_Shoulder"), ("upperarm_l", "upperarm_r")),
    ("锁骨长",                 ("L_Clavicle", "L_Shoulder"), ("clavicle_l", "upperarm_l")),
    ("髋宽(左右髋)",           ("L_Hip", "R_Hip"),           ("thigh_l", "thigh_r")),
    ("脊柱(pelvis->neck)",     ("Pelvis", "Neck"),           ("pelvis", "neck_01")),
    ("颈长",                   ("Neck", "Head"),             ("neck_01", "head")),
    ("头到地(pelvis->toe)",    ("Pelvis", "L_Toe"),          ("pelvis", "toe_l")),
    ("手到地(hand->toe)",      ("L_Hand", "L_Toe"),          ("hand_l", "toe_l")),
]
for label, s_pair, t_pair in PAIRS:
    vs = d(src, *s_pair)
    vt = d(tgt, *t_pair)
    if vs is None or vt is None:
        print("%-26s %14s %14s   (缺骨)" % (label, "%.4f" % vs if vs else "-", "%.4f" % vt if vt else "-"))
        continue
    print("%-26s %14.4f %14.4f %10.4f" % (label, vs, vt, vt / vs))

print()
print("--- 关键比率 ---")
def ratio(a, n1, n2, base1, base2):
    v = d(a, n1, n2); b = d(a, base1, base2)
    return v / b if (v and b) else None
print("源  腿长/身高     = %.4f" % (ratio(src, "L_Hip", "L_Foot", "L_Toe", "Head") or 0))
print("目标 腿长/身高     = %.4f" % (ratio(tgt, "thigh_l", "foot_l", "toe_l", "head") or 0))
print("源  臂长/身高     = %.4f" % (ratio(src, "L_Shoulder", "L_Hand", "L_Toe", "Head") or 0))
print("目标 臂长/身高     = %.4f" % (ratio(tgt, "upperarm_l", "hand_l", "toe_l", "head") or 0))
print("源  肩宽/身高     = %.4f" % (ratio(src, "L_Shoulder", "R_Shoulder", "L_Toe", "Head") or 0))
print("目标 肩宽/身高     = %.4f" % (ratio(tgt, "upperarm_l", "upperarm_r", "toe_l", "head") or 0))
print("=== DONE ===")
