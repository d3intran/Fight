"""
俯视倾斜假设的实测校验：源动画的脊柱到底「后仰」还是「前倾」？
用法: blender -b -P plan_03_lean_audit.py -- <SRC_GLB>

方法（与骨骼朝向约定无关，只用关节坐标）：
  lateral = normalize(R_Hip - L_Hip)            横轴
  fwd     = up × lateral                        前向基准（符号用 run 动画自校准：跑动躯干必前倾）
  torso   = normalize(Neck - Pelvis)            躯干轴
  lean    = atan2(dot(torso,fwd), dot(torso,up))   正=前倾  负=后仰
"""
import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC = argv[0]
WANT = argv[1].split(",") if len(argv) > 1 else ["idle1", "idle2", "run", "run_fast", "attack1", "spell1"]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
sc = bpy.context.scene
sc.render.fps = 30

def hp(n, rest=False):
    b = arm.data.bones.get(n)
    if rest:
        return (arm.matrix_world @ b.head_local) if b else None
    pb = arm.pose.bones.get(n)
    return (arm.matrix_world @ pb.matrix).translation if pb else None

def axis(n):
    """骨自身 Y 轴在世界中的方向（静止）"""
    b = arm.data.bones.get(n)
    return (arm.matrix_world.to_3x3() @ b.matrix_local.to_3x3() @ Vector((0, 1, 0))).normalized() if b else None

UP = Vector((0, 0, 1))

def frame_metrics():
    lh, rh = hp("L_Hip"), hp("R_Hip")
    pv, nk, hd = hp("Pelvis"), hp("Neck"), hp("Head")
    if None in (lh, rh, pv, nk, hd):
        return None
    lat = (rh - lh); lat.z = 0.0
    if lat.length < 1e-6:
        return None
    lat.normalize()
    fwd = UP.cross(lat).normalized()
    torso = (nk - pv)
    if torso.length < 1e-6:
        return None
    t = torso.normalized()
    lean = math.degrees(math.atan2(t.dot(fwd), t.dot(UP)))
    # 颈段
    nseg = (hd - nk)
    nlean = math.degrees(math.atan2(nseg.normalized().dot(fwd), nseg.normalized().dot(UP))) if nseg.length > 1e-6 else 0.0
    # 头骨自身轴（若指向头顶，则其相对竖直的偏差≈头部俯仰的镜像）
    hax = axis("Head")
    hl = math.degrees(math.atan2(hax.dot(fwd), hax.dot(UP))) if hax else 0.0
    # 头/骨盆水平偏移（沿前向）
    off = (hd - pv)
    return lean, nlean, hl, off.dot(fwd), off.length

def stats(vals):
    v = sorted(vals)
    n = len(v)
    return v[0], v[n // 2], v[-1], sum(v) / n

print("=" * 100)
print("### 俯视倾斜假设实测  ::  %s" % SRC.split("/")[-1])
print("=" * 100)
print("正值 = 前倾（朝角色面朝方向）  负值 = 后仰")
print()

acts = {a.name: a for a in bpy.data.actions}
rows = []
for want in WANT:
    act = None
    for nm, a in acts.items():
        if nm == want or nm.endswith("_" + want) or nm.endswith(want):
            act = a; break
    if act is None:
        print("  !! 找不到 %s" % want); continue
    arm.animation_data.action = act
    F0, F1 = int(act.frame_range[0]), int(act.frame_range[1])
    lean, nlean, hl, off, offl = [], [], [], [], []
    for f in range(F0, F1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        m = frame_metrics()
        if m is None:
            continue
        lean.append(m[0]); nlean.append(m[1]); hl.append(m[2]); off.append(m[3]); offl.append(m[4])
    if not lean:
        continue
    a, b, c, d = stats(lean)
    rows.append((want, len(lean), a, b, c, d, offl))

print("%-14s %5s %26s %14s" % ("动作", "帧数", "躯干轴 倾角 min/中位/max/均值", "头-盆水平距"))
print("-" * 100)
for want, n, mn, md, mx, mean, offl in rows:
    print("%-14s %5d     %7.1f / %6.1f / %6.1f / %6.1f %14.4f" % (want, n, mn, md, mx, mean, sum(offl) / len(offl)))

print()
print("--- 用 run 自校准符号（跑动躯干必然前倾）---")
runrow = [r for r in rows if r[0] == "run"]
if runrow:
    r = runrow[0]
    print("run 均值 = %.1f°  → 若为负，说明上面表格的符号是反的（即负=前倾）" % r[5])
    sign = -1.0 if r[5] < 0 else 1.0
    print("校准后（正=前倾）:")
    for want, n, mn, md, mx, mean, offl in rows:
        print("   %-14s 中位 %+7.1f°  均值 %+7.1f°" % (want, md * sign, mean * sign))
else:
    print("没有 run 可校准")

print()
print("--- 静止姿态（bind pose）基线 ---")
rest = {}
lh, rh = hp("L_Hip", True), hp("R_Hip", True)
lat = (rh - lh); lat.z = 0.0; lat.normalize()
fwd = UP.cross(lat).normalized()
pv, nk, hd = hp("Pelvis", True), hp("Neck", True), hp("Head", True)
t = (nk - pv).normalized()
print("静止躯干轴倾角 = %+.1f°   前向基准 fwd = (%.3f, %.3f, %.3f)" % (
    math.degrees(math.atan2(t.dot(fwd), t.dot(UP))), fwd.x, fwd.y, fwd.z))
print("静止 pelvis=%s neck=%s  (Z: %.3f / %.3f)" % (
    ["%.3f" % v for v in pv], ["%.3f" % v for v in nk], pv.z, nk.z))
print("=== DONE ===")
