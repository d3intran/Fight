import math
import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

IDLE = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"
SOCK = "hand_rSocket"
SOCK_ROT = (-106.334, -70.982, 9.342)      # 项目笔记记录的 socket 相对旋转（度, pitch/yaw/roll）


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
    a = qnorm(a)
    b = qnorm(b)
    d = sum(x * y for x, y in zip(a, b))
    if d > 0.999999:
        return (0.0, 0.0, 0.0, 1.0)
    if d < -0.999999:
        ax = (1.0, 0.0, 0.0)
        if abs(a[0]) > 0.9:
            ax = (0.0, 1.0, 0.0)
        c = qnorm((a[1] * ax[2] - a[2] * ax[1], a[2] * ax[0] - a[0] * ax[2],
                   a[0] * ax[1] - a[1] * ax[0], 0.0))
        return c
    c = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0], 0.0)
    c = qnorm(c)
    ang = math.acos(max(-1.0, min(1.0, d))) * 0.5
    s = math.sin(ang)
    return (c[0] * s, c[1] * s, c[2] * s, math.cos(ang))


def rpy_deg_to_quat(p, y, r):
    qp = (math.sin(math.radians(p) / 2), 0.0, 0.0, math.cos(math.radians(p) / 2))
    qy = (0.0, math.sin(math.radians(y) / 2), 0.0, math.cos(math.radians(y) / 2))
    qr = (0.0, 0.0, math.sin(math.radians(r) / 2), math.cos(math.radians(r) / 2))
    return qnorm(qmul(qmul(qy, qp), qr))


# ---------- 1. 找 socket（实测只在 SkeletalMesh 上，1 个：hand_rSocket）
mesh = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
holder = mesh
sock = mesh.find_socket(SOCK)
unreal.log("### %s -> %s （mesh socket 总数 %d）" % (SOCK, sock, mesh.num_sockets()))
if sock is None:
    unreal.log_error("没找到 %s" % SOCK)
    raise SystemExit(1)
for prop in ("bone_name", "relative_location", "relative_rotation", "relative_scale"):
    try:
        unreal.log("   %-18s = %s" % (prop, sock.get_editor_property(prop)))
    except Exception as ex:
        unreal.log("   %-18s ERR %s" % (prop, str(ex)[:50]))

# ---------- 2. 当前斧头 +Y 在 component 空间指向哪（用待机第 0 帧的手）
idle = eal.load_asset(IDLE)
names = [str(x) for x in idle.controller.get_model_interface().get_bone_track_names()]
lc = {n.lower(): n for n in names}
chain = [str(x) for x in AL.find_bone_path_to_root(idle, "hand_r")][::-1]
poses = AL.get_bone_poses_for_frame(idle, [unreal.Name(b) for b in names], 0, False)
loc = {}
for i, b in enumerate(names):
    t = poses[i]
    loc[b] = ((t.translation.x, t.translation.y, t.translation.z),
              (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
              (t.scale3d.x, t.scale3d.y, t.scale3d.z))
Q = (0.0, 0.0, 0.0, 1.0)
for bn in chain:
    k = bn if bn in loc else lc.get(bn.lower())
    tr = loc.get(k) if k else None
    if tr:
        Q = qmul(Q, tr[1])
q_hand = Q
q_sock_rel = rpy_deg_to_quat(*SOCK_ROT)
q_socket = qmul(q_hand, q_sock_rel)
cur_y = qrot(q_socket, (0.0, 1.0, 0.0))
unreal.log("### 当前：斧头 +Y（大刃）在 component 空间 = %s" % [round(v, 3) for v in cur_y])
unreal.log("   与「朝下」(0,0,-1) 夹角 %.1f° ；与「朝上」夹角 %.1f°"
           % (math.degrees(math.acos(max(-1, min(1, -cur_y[2])))),
              math.degrees(math.acos(max(-1, min(1, cur_y[2]))))))

# ---------- 3. 算新 socket 旋转：让 +Y 指向 component 空间的 -Z
target = (0.0, 0.0, -1.0)
w = qrot(qconj(q_hand), target)                  # 目标在 hand 骨空间里
cur_local = qrot(q_sock_rel, (0.0, 1.0, 0.0))    # 当前 +Y 在 hand 骨空间里
delta = minarc(cur_local, w)                     # 最小弧修正
q_new = qnorm(qmul(delta, q_sock_rel))
unreal.log("### 修正 %s：最小弧 %.1f°（hand 骨空间）"
           % (SOCK, math.degrees(2.0 * math.acos(max(-1.0, min(1.0, abs(delta[3])))))))

# 转回 rotator 便于写入
rot = unreal.MathLibrary.quat_rotator(unreal.Quat(q_new[0], q_new[1], q_new[2], q_new[3]))
unreal.log("   新相对旋转(rotator) = pitch=%.3f yaw=%.3f roll=%.3f" % (rot.pitch, rot.yaw, rot.roll))

sock.set_editor_property("relative_rotation", rot)
saved = False
try:
    saved = eal.save_asset("/Game/Character/Darius/SK_Darius_GodKing")
except Exception as ex:
    unreal.log("   save ERR %s" % str(ex)[:80])
unreal.log("### save -> %s" % saved)

# ---------- 4. 复核
sk2 = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
me2 = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
for tag, o in (("skeleton", sk2), ("mesh", me2)):
    try:
        for s in o.get_editor_property("sockets"):
            if str(s.get_editor_property("socket_name")) == SOCK:
                r2 = s.get_editor_property("relative_rotation")
                unreal.log("### 复核 %s: pitch=%.3f yaw=%.3f roll=%.3f" % (tag, r2.pitch, r2.yaw, r2.roll))
    except Exception:
        pass
unreal.log("### DONE")
