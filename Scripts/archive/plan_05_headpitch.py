"""
「仰面望天」假设的直接检验：动画相对 bind pose 把躯干/颈/头 仰了多少度？
用法: blender -b -P plan_05_headpitch.py -- <SRC_GLB>
约定：forward = -Y（已由披风+Y、斧刃-Y 双向锚定）
      正 = 朝身前倾   负 = 向后仰
"""
import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
WANT = argv[1].split(",") if len(argv) > 1 else [
    "idle1", "idle2", "idlein", "run", "run_fast", "run_homeguard",
    "attack1", "attack2", "spell1", "spell4_5", "dance", "recall"]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
sc = bpy.context.scene
sc.render.fps = 30
FWD = Vector((0.0, -1.0, 0.0))   # 已锚定
UP = Vector((0.0, 0.0, 1.0))

def rest_pt(n):
    b = arm.data.bones.get(n)
    return (arm.matrix_world @ b.head_local) if b else None

def pose_pt(n):
    pb = arm.pose.bones.get(n)
    return (arm.matrix_world @ pb.matrix).translation if pb else None

def pose_axisY(n):
    pb = arm.pose.bones.get(n)
    if pb is None:
        return None
    return (arm.matrix_world.to_3x3() @ pb.matrix.to_3x3() @ Vector((0, 1, 0))).normalized()

def tilt(v):
    """v 相对世界竖直的倾角，正=朝身前倾"""
    return math.degrees(math.atan2(v.normalized().dot(FWD), v.normalized().dot(UP)))

# --- bind pose 基线 ---
R = {}
R["torso"] = tilt(rest_pt("Neck") - rest_pt("Pelvis"))
R["neck"] = tilt(rest_pt("Head") - rest_pt("Neck"))
b = arm.data.bones["Head"]
R["head"] = tilt((arm.matrix_world.to_3x3() @ b.matrix_local.to_3x3() @ Vector((0, 1, 0))).normalized())

print("=" * 104)
print("### 「仰面望天」检验   约定：正=前倾  负=后仰   (forward = -Y，经披风/斧刃双向锚定)")
print("=" * 104)
print("bind pose 基线：躯干 %+.1f°   颈段 %+.1f°   头骨轴 %+.1f°" % (R["torso"], R["neck"], R["head"]))
print()
print("%-14s %6s %22s %22s %22s" % ("动作", "帧数", "躯干(相对bind)", "颈段(相对bind)", "头骨轴(相对bind)"))
print("-" * 104)

acts = {a.name: a for a in bpy.data.actions}
for want in WANT:
    act = None
    for nm, a in acts.items():
        if nm == want or nm.endswith("_" + want) or nm.endswith(want):
            act = a; break
    if act is None:
        continue
    arm.animation_data.action = act
    F0, F1 = int(act.frame_range[0]), int(act.frame_range[1])
    ts, ns, hs = [], [], []
    for f in range(F0, F1 + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        ts.append(tilt(pose_pt("Neck") - pose_pt("Pelvis")) - R["torso"])
        ns.append(tilt(pose_pt("Head") - pose_pt("Neck")) - R["neck"])
        ax = pose_axisY("Head")
        hs.append(tilt(ax) - R["head"] if ax else 0.0)
    n = len(ts)
    def f3(v):
        return "%+6.1f /%+6.1f /%+6.1f" % (sorted(v)[0], sorted(v)[n // 2], sorted(v)[-1])
    print("%-14s %6d %22s %22s %22s" % (want, n, f3(ts), f3(ns), f3(hs)))

print()
print("解读：躯干/颈段/头骨 三列若都接近 0 → 动画没有相对静止姿态做后仰补偿")
print("      若为显著负值 → 确实存在「后仰/望天」；负值越大越严重")
print("=== DONE ===")
