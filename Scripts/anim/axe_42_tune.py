"""手动调握斧方式 —— 改 `SK_Darius_GodKing` 上 `hand_rSocket` 的 相对旋转 / 相对位置。

斧头 `WeaponAxe`（BP 上的 StaticMeshComponent）相对变换是 0，
所以它的世界姿态 = `hand_rSocket` 的世界姿态。

=== 两个旋钮 ===
  BLADE_DOWN : True  = 斧刃（斧头 +Y 端）朝下；False = 用原始朝向
  GRIP_FROM_HEAD_CM : 手握在「离斧头多少厘米」处。斧头全长 172cm、网格原点在正中间，
                      所以 86 = 握正中（原来的状态，像端长棍）、40 = 握在靠近斧头处、
                      0 = 握在斧头上。设 86 即不偏移。
跑完打印「斧头 / 尾端」相对手的高度，方便你判断合不合适。
"""
import math
import unreal

MESH_PATH = "/Game/Character/Darius/SK_Darius_GodKing"
SOCK = "hand_rSocket"
REF_ANIM = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"   # 用它的第 0 帧当参考姿势
REF_FRAME = 0

BLADE_DOWN = True
GRIP_FROM_HEAD_CM = 86.0        # 86 = 握正中（推荐起点）；40 = 握在靠近斧头处；0 = 握在斧头上
PALM_PULL_CM = 15.0             # 往掌心收多少 cm（把斧柄拉到手心里；0 = 不动）

ORIG_ROT = (-106.334, -70.982, 9.342)   # 原始 socket 相对旋转（AGENTS.md §3.2）
ORIG_LOC = (0.18965, 0.10080, 0.00982)  # 原始 socket 相对位置（单位 = 1/100 cm）
SHAFT_CM = 172.0                # 斧头全长（世界尺寸 21×172×77）
BONE_UNIT = 100.0               # socket 的 location 单位是 1/100 cm（骨架最外层 scale=100）


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def qconj(q):
    return (-q[0], -q[1], -q[2], q[3])


def qnorm(q):
    n = math.sqrt(sum(c * c for c in q))
    return tuple(c / n for c in q) if n > 1e-12 else (0.0, 0.0, 0.0, 1.0)


def qrot(q, v):
    x, y, z, w = q
    m = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def minarc(a, b):
    a, b = qnorm(a), qnorm(b)
    d = sum(x * y for x, y in zip(a, b))
    if d > 0.999999:
        return (0.0, 0.0, 0.0, 1.0)
    c = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0], 0.0)
    c = qnorm(c)
    ang = math.acos(max(-1.0, min(1.0, d))) * 0.5
    s = math.sin(ang)
    return (c[0] * s, c[1] * s, c[2] * s, math.cos(ang))


def rpy(p, y, r):
    qp = (math.sin(math.radians(p) / 2), 0.0, 0.0, math.cos(math.radians(p) / 2))
    qy = (0.0, math.sin(math.radians(y) / 2), 0.0, math.cos(math.radians(y) / 2))
    qr = (0.0, 0.0, math.sin(math.radians(r) / 2), math.cos(math.radians(r) / 2))
    return qnorm(qmul(qmul(qy, qp), qr))


mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
sock = mesh.find_socket(SOCK)
unreal.log("### 改前：")
for p in ("relative_location", "relative_rotation", "relative_scale"):
    unreal.log("   %-18s = %s" % (p, sock.get_editor_property(p)))

# ---- 参考姿势下 hand_r 的 component 旋转
anim = unreal.EditorAssetLibrary.load_asset(REF_ANIM)
names = [str(x) for x in anim.controller.get_model_interface().get_bone_track_names()]
lc = {n.lower(): n for n in names}
chain = [str(x) for x in unreal.AnimationLibrary.find_bone_path_to_root(anim, "hand_r")][::-1]
poses = unreal.AnimationLibrary.get_bone_poses_for_frame(
    anim, [unreal.Name(b) for b in names], REF_FRAME, False)
loc = {}
for i, b in enumerate(names):
    t = poses[i]
    loc[b] = ((t.translation.x, t.translation.y, t.translation.z),
              (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
              (t.scale3d.x, t.scale3d.y, t.scale3d.z))
Qh = (0.0, 0.0, 0.0, 1.0)
for bn in chain:
    k = bn if bn in loc else lc.get(bn.lower())
    tr = loc.get(k) if k else None
    if tr:
        Qh = qmul(Qh, tr[1])

if BLADE_DOWN:
    w = qrot(qconj(Qh), (0.0, 0.0, -1.0))                 # 目标：斧头 +Y 指向 component 的 -Z
    cur = qrot(rpy(*ORIG_ROT), (0.0, 1.0, 0.0))
    q_new = qnorm(qmul(minarc(cur, w), rpy(*ORIG_ROT)))
else:
    q_new = rpy(*ORIG_ROT)
rot = unreal.MathLibrary.quat_rotator(unreal.Quat(q_new[0], q_new[1], q_new[2], q_new[3]))

# ---- 沿斧柄滑动：让「离斧头 GRIP_FROM_HEAD_CM 处」落在 socket 上
p = (SHAFT_CM / 2.0) - GRIP_FROM_HEAD_CM      # 网格原点到握点的距离（沿 +Y）
axis_local = qrot(q_new, (0.0, 1.0, 0.0))     # 斧头 +Y 在 hand 骨空间的方向
# ★ 幂等：一律从 ORIG_LOC 出发算，不要读当前值（否则重复跑会一直沿柄滑）
new_loc = unreal.Vector(ORIG_LOC[0] - p * axis_local[0] / BONE_UNIT - PALM_PULL_CM / BONE_UNIT,
                        ORIG_LOC[1] - p * axis_local[1] / BONE_UNIT,
                        ORIG_LOC[2] - p * axis_local[2] / BONE_UNIT)

sock.set_editor_property("relative_rotation", rot)
sock.set_editor_property("relative_location", new_loc)
unreal.log("### 改后：")
unreal.log("   relative_rotation = pitch=%.3f yaw=%.3f roll=%.3f" % (rot.pitch, rot.yaw, rot.roll))
unreal.log("   relative_location = (%.5f, %.5f, %.5f)" % (new_loc.x, new_loc.y, new_loc.z))
unreal.log("   （scale 保持 %.4f 不动）" % sock.get_editor_property("relative_scale").x)
unreal.log("   ⇒ 握点离斧头 %.0f cm、离尾端 %.0f cm" % (GRIP_FROM_HEAD_CM, SHAFT_CM - GRIP_FROM_HEAD_CM))
unreal.log("   ⇒ 若手在 105cm 高：斧头在 %.0f cm 高，尾端在 %.0f cm 高"
           % (105 - GRIP_FROM_HEAD_CM, 105 + (SHAFT_CM - GRIP_FROM_HEAD_CM)))
unreal.log("   save -> %s" % unreal.EditorAssetLibrary.save_asset(MESH_PATH))
unreal.log("### DONE")
