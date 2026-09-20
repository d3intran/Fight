import math
import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

# 上半身取 Mixamo 持斧静止姿；下半身（骨盆+腿脚）保留原待机；再叠一点呼吸
UP_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Mixamo"
LOW_PATH = "/Game/Character/Darius/Anims_TP_v2/A_Darius_idle1"
NEW_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"

SPINE_ROOT = "spine_01"
REDERIVE = ["weapon_jnt"]

# 程序化呼吸：骨名 -> (幅值°, 周期数)。0 幅值 = 完全静止。
BREATH = [("spine_02", 1.5, 1.0), ("neck_01", 1.0, 1.0)]


def qconj(q):
    return (-q[0], -q[1], -q[2], q[3])


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def qrot(q, v):
    x, y, z, w = q
    m = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def qaxis(axis, deg):
    a = math.radians(deg) * 0.5
    s = math.sin(a)
    return (axis[0] * s, axis[1] * s, axis[2] * s, math.cos(a))


def qnorm(q):
    n = math.sqrt(sum(c * c for c in q))
    return tuple(c / n for c in q) if n > 1e-12 else (0.0, 0.0, 0.0, 1.0)


def qslerp(a, b, t):
    d = sum(x * y for x, y in zip(a, b))
    if d < 0.0:
        b = tuple(-c for c in b)
        d = -d
    if d > 0.9995:
        return qnorm(tuple(a[i] + (b[i] - a[i]) * t for i in range(4)))
    th0 = math.acos(max(-1.0, min(1.0, d)))
    th = th0 * t
    return qnorm(tuple(a[i] * math.sin(th0 - th) / math.sin(th0) +
                       b[i] * math.sin(th) / math.sin(th0) for i in range(4)))


def qangle(a, b):
    d = abs(sum(x * y for x, y in zip(a, b)))
    return math.degrees(2.0 * math.acos(max(-1.0, min(1.0, d))))


def vlerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


up = eal.load_asset(UP_PATH)
low = eal.load_asset(LOW_PATH)
if not up or not low:
    unreal.log_error("源加载失败")
    raise SystemExit(1)


def track_names(a):
    return [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]


low_names = track_names(low)
low_lc = {n.lower(): n for n in low_names}
parents, chains = {}, {}
for b in low_names:
    rc = [str(x) for x in AL.find_bone_path_to_root(low, b)]
    parents[b] = rc[1] if len(rc) > 1 else None
    chains[b] = rc[::-1]

upper = set()
stack = [SPINE_ROOT]
while stack:
    cur = stack.pop()
    if cur in upper:
        continue
    upper.add(cur)
    for b, p in parents.items():
        if p == cur:
            stack.append(b)
unreal.log("### spine_01 子树 = %d 根；LOW 轨道 %d 根" % (len(upper), len(low_names)))


def read_poses(a, names):
    nf = int(AL.get_num_frames(a))
    out = {b: ([], [], []) for b in names}
    objs = [unreal.Name(b) for b in names]
    for f in range(nf + 1):
        poses = AL.get_bone_poses_for_frame(a, objs, f, False)
        for i, b in enumerate(names):
            t = poses[i]
            out[b][0].append((t.translation.x, t.translation.y, t.translation.z))
            out[b][1].append((t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w))
            out[b][2].append((t.scale3d.x, t.scale3d.y, t.scale3d.z))
    return out


up_t = read_poses(up, low_names)
low_t = read_poses(low, low_names)
n_up = len(up_t["pelvis"][0]) - 1
NKEY = len(low_t["pelvis"][0])
unreal.log("### UP %d 帧 / LOW %d 帧（目标 key=%d）" % (n_up, NKEY - 1, NKEY))
ratio = float(n_up) / float(NKEY - 1)


def resample(src):
    p, r, s = src
    ns = len(p) - 1
    op, orr, os_ = [], [], []
    for i in range(NKEY):
        f = (i * ratio) % ns
        j0 = int(math.floor(f))
        j1 = (j0 + 1) % ns
        u = f - j0
        op.append(vlerp(p[j0], p[j1], u))
        orr.append(qslerp(r[j0], r[j1], u))
        os_.append(vlerp(s[j0], s[j1], u))
    return op, orr, os_


if eal.does_asset_exist(NEW_PATH):
    new = eal.load_asset(NEW_PATH)
    unreal.log("### 复用已存在的目标")
else:
    new = eal.duplicate_asset(LOW_PATH, NEW_PATH)
    if not new:
        unreal.log_error("duplicate 失败")
        raise SystemExit(1)
ctrl = new.controller
unreal.log("### 目标 %s keys=%d" % (new.get_path_name(),
                                    ctrl.get_model_interface().get_number_of_keys()))

base_ok = 0
for b in low_names:
    if ctrl.set_bone_track_keys(
            b,
            [unreal.Vector(*v) for v in low_t[b][0]],
            [unreal.Quat(v[0], v[1], v[2], v[3]) for v in low_t[b][1]],
            [unreal.Vector(*v) for v in low_t[b][2]],
            False):
        base_ok += 1
unreal.log("### 基准（LOW 全轨）写入 %d/%d" % (base_ok, len(low_names)))

merged = {b: (list(low_t[b][0]), list(low_t[b][1]), list(low_t[b][2])) for b in low_names}
written = 0
for b in sorted(upper):
    if not up_t.get(b) or not up_t[b][0]:
        continue
    op, orr, os_ = resample(up_t[b])
    if ctrl.set_bone_track_keys(b, [unreal.Vector(*v) for v in op],
                               [unreal.Quat(v[0], v[1], v[2], v[3]) for v in orr],
                               [unreal.Vector(*v) for v in os_], False):
        written += 1
        merged[b] = (op, orr, os_)
unreal.log("### 上半身写入 %d/%d" % (written, len(upper)))


def fk(bone, fi):
    P, Q, S = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
    for bn in chains.get(bone, []):
        k = bn if bn in merged else low_lc.get(bn.lower())
        tr = merged.get(k) if k else None
        if tr is None or not tr[0]:
            continue
        t, q, s = tr[0][fi], tr[1][fi], tr[2][fi]
        off = qrot(Q, (t[0] * S[0], t[1] * S[1], t[2] * S[2]))
        P = (P[0] + off[0], P[1] + off[1], P[2] + off[2])
        Q = qmul(Q, q)
        S = (S[0] * s[0], S[1] * s[1], S[2] * s[2])
    return P, Q, S


# ---------------- 程序化呼吸（在 component 空间绕「右轴」做俯仰，再折回局部）
for bone, amp, cyc in BREATH:
    if bone not in merged:
        unreal.log("   呼吸：跳过 %s（无轨道）" % bone)
        continue
    par = parents.get(bone)
    new_rot = []
    for i in range(NKEY):
        pr, pq, ps = fk(par, i)
        right = qrot(pq, (1.0, 0.0, 0.0))
        dR = qaxis(right, amp * math.sin(2.0 * math.pi * cyc * i / float(NKEY)))
        q_loc = merged[bone][1][i]
        q_new = qnorm(qmul(qmul(qconj(pq), dR), qmul(pq, q_loc)))
        new_rot.append(q_new)
    merged[bone] = (merged[bone][0], new_rot, merged[bone][2])
    ok = ctrl.set_bone_track_keys(bone,
                                 [unreal.Vector(*v) for v in merged[bone][0]],
                                 [unreal.Quat(v[0], v[1], v[2], v[3]) for v in new_rot],
                                 [unreal.Vector(*v) for v in merged[bone][2]], False)
    unreal.log("   呼吸：%s 幅值 %.1f° × %d 周期  写入=%s" % (bone, amp, cyc, ok))

# ---------------- weapon_jnt 重新解算
wj_pos, wj_rot, wj_scl = [], [], []
for i in range(NKEY):
    cr = fk("weapon_jnt_r", i)
    cp = fk(parents.get("weapon_jnt"), i)
    Qi = qconj(cp[1])
    dt = tuple(cr[0][k] - cp[0][k] for k in range(3))
    lr = qrot(Qi, dt)
    wj_pos.append(tuple(lr[k] / cp[2][k] if abs(cp[2][k]) > 1e-9 else lr[k] for k in range(3)))
    wj_rot.append(qnorm(qmul(Qi, cr[1])))
    wj_scl.append(tuple(cr[2][k] / cp[2][k] if abs(cp[2][k]) > 1e-9 else 1.0 for k in range(3)))
unreal.log("### weapon_jnt 重解算写入 = %s" % ctrl.set_bone_track_keys(
    "weapon_jnt", [unreal.Vector(*v) for v in wj_pos],
    [unreal.Quat(v[0], v[1], v[2], v[3]) for v in wj_rot],
    [unreal.Vector(*v) for v in wj_scl], False))
merged["weapon_jnt"] = (wj_pos, wj_rot, wj_scl)

unreal.log("### save_asset -> %s" % eal.save_asset(NEW_PATH))

# ---------------- 校验
chk = eal.load_asset(NEW_PATH)
chk_t = read_poses(chk, low_names)


def cmp_tracks(a, b, bones, label):
    wr, wp, wb = 0.0, 0.0, None
    for bn in bones:
        ta, tb = a.get(bn), b.get(bn)
        if not ta or not tb or not ta[0]:
            continue
        for i in range(min(len(ta[0]), len(tb[0]))):
            dr = qangle(ta[1][i], tb[1][i])
            dp = math.sqrt(sum((ta[0][i][k] - tb[0][i][k]) ** 2 for k in range(3))) * 100.0
            if dr > wr:
                wr = dr
            if dp > wp:
                wp, wb = dp, bn
    unreal.log("### %-32s 最大角差 %.3f°  最大位移差 %.4f cm (%s)" % (label, wr, wp, wb))


lower = [b for b in low_names if b not in upper and b not in REDERIVE]
cmp_tracks(chk_t, low_t, lower, "下半身 vs 原待机 (应≈0)")
cmp_tracks(chk_t, merged, sorted(upper), "上半身 vs 重采样源 (应≈0)")

unreal.log("### 姿态（component space，前向 = 右轴 × 上）")
SEGS = [("pelvis", "spine_01"), ("spine_01", "spine_02"), ("spine_02", "spine_03"),
        ("spine_03", "neck_01"), ("neck_01", "head")]


def sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def nrm(v):
    n = math.sqrt(dot(v, v))
    return tuple(x / n for x in v) if n > 1e-9 else (0.0, 0.0, 0.0)


for tag, tr in (("新待机", chk_t), ("原待机", low_t)):
    for i in (0, NKEY // 2):
        right = nrm(sub(fk("thigh_r", i)[0], fk("thigh_l", i)[0]))
        fwd = nrm(cross(right, (0, 0, 1)))
        seg = []
        for a_, b_ in SEGS:
            v = sub(fk(b_, i)[0], fk(a_, i)[0])
            h = math.sqrt(v[0] ** 2 + v[1] ** 2)
            tilt = math.degrees(math.atan2(h, v[2])) if abs(v[2]) > 1e-6 else 90.0
            d = nrm((v[0], v[1], 0.0)) if h > 1e-6 else (0, 0, 0)
            seg.append("%s %5.1f°(前%+.2f 右%+.2f)" % (b_, tilt, dot(d, fwd), dot(d, right)))
        unreal.log("   %s key%-3d %s" % (tag, i, " | ".join(seg)))
    pel = fk("pelvis", 0)[0]
    for c in ("cape_chain_01_m", "cape_chain_05_m", "cape_chain_09_m"):
        v = sub(fk(c, 0)[0], pel)
        unreal.log("      %s 水平 %.1f 垂 %.1f" % (c, math.sqrt(v[0] ** 2 + v[1] ** 2), v[2]))
unreal.log("### DONE")
