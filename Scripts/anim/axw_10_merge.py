import math
import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

UP_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo"
LOW_PATH = "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"
NEW_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered"

SPINE_ROOT = "spine_01"
REDERIVE = ["weapon_jnt"]

# 上半身相对下半身的相位对齐量（单位：UP 的 key）。
# 起因：合并后手臂摆动由「UP 的臂骨」+「LOW 的骨盆旋转（它带着整个躯干转）」叠加。
# LOW 的骨盆转动与髋同向，而真实走路肩带应与髋**反向**转 ⇒ 手臂的对侧摆幅被抵消，
# 实测腿-臂相位差 156.8°（自然走路要 ~180°，UP 原片本身是 173.7°）。
# 实测「相位随正位移减小」：+2.58 key ⇒ −32.9°。取负号 1.81 key ≈ +23° ⇒ 拉回 ~180°。
# 设 0 即完全按原相位搬（不做任何对齐）。
UPPER_PHASE_SHIFT = -1.81

# ------------------------------------------------------------------ 数学工具
def qconj(q):
    return (-q[0], -q[1], -q[2], q[3])


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qrot(q, v):
    x, y, z, w = q
    m = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


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
    s0 = math.sin(th0 - th) / math.sin(th0)
    s1 = math.sin(th) / math.sin(th0)
    return qnorm(tuple(a[i] * s0 + b[i] * s1 for i in range(4)))


def qangle(a, b):
    d = abs(sum(x * y for x, y in zip(a, b)))
    return math.degrees(2.0 * math.acos(max(-1.0, min(1.0, d))))


def vlerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ------------------------------------------------------------------ 资产读取
up = eal.load_asset(UP_PATH)
low = eal.load_asset(LOW_PATH)


def track_names(anim):
    return [str(n) for n in anim.controller.get_model_interface().get_bone_track_names()]


def raw_chain(anim, bone):
    return [str(x) for x in AL.find_bone_path_to_root(anim, bone)]


up_names = track_names(up)
low_names = track_names(low)
unreal.log("### 轨道数 UP=%d LOW=%d" % (len(up_names), len(low_names)))

parents = {}
chains = {}
for b in up_names:
    rc = raw_chain(up, b)
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
unreal.log("### spine_01 子树 = %d 根骨" % len(upper))


def read_poses(anim, names):
    """{bone: (pos[], rot[], scl[])} 局部（父级相对）姿态，逐帧。"""
    nf = int(AL.get_num_frames(anim))
    out = {b: ([], [], []) for b in names}
    name_objs = [unreal.Name(b) for b in names]
    for f in range(nf + 1):
        poses = AL.get_bone_poses_for_frame(anim, name_objs, f, False)
        if len(poses) != len(names):
            unreal.log_error("get_bone_poses_for_frame 返回 %d != %d @f%d" % (len(poses), len(names), f))
            return None
        for i, b in enumerate(names):
            t = poses[i]
            out[b][0].append((t.translation.x, t.translation.y, t.translation.z))
            out[b][1].append((t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w))
            out[b][2].append((t.scale3d.x, t.scale3d.y, t.scale3d.z))
    return out


up_t = read_poses(up, low_names)
low_t = read_poses(low, low_names)
if up_t is None or low_t is None:
    raise SystemExit(1)

OUTER = "darius_godking_mesh_lod0_skeleton"
unreal.log("### 最外层骨自检（UP 没有这条轨道，看 UE 是否回落到静止姿势）")
for lbl, tr in (("UP", up_t), ("LOW", low_t)):
    v = tr.get(OUTER)
    if v and v[0]:
        unreal.log("   %-4s t[0]=%s  t[-1]=%s" % (
            lbl, [round(x, 4) for x in v[0][0]], [round(x, 4) for x in v[0][-1]]))
    else:
        unreal.log("   %-4s 无数据" % lbl)

n_up = len(up_t["pelvis"][0]) - 1
n_low = len(low_t["pelvis"][0]) - 1
unreal.log("### key counts: UP=%d (frames %d)  LOW=%d (frames %d)" % (n_up + 1, n_up, n_low + 1, n_low))
unreal.log("### 抽查 pelvis: UP[0]=%s  LOW[0]=%s" % (
    [round(v, 4) for v in up_t["pelvis"][0][0]], [round(v, 4) for v in low_t["pelvis"][0][0]]))
ratio = float(n_up) / float(n_low)

NKEY = n_low + 1


def resample(src, shift=0.0):
    """把源动画的 key 重采样到 NKEY，可选**循环**相位平移 shift（单位=源 key）。"""
    p, r, s = src
    ns = len(p) - 1
    op, orr, os_ = [], [], []
    for i in range(NKEY):
        f = (i * ratio + shift) % ns
        j0 = int(math.floor(f))
        j1 = (j0 + 1) % ns
        u = f - j0
        op.append(vlerp(p[j0], p[j1], u))
        orr.append(qslerp(r[j0], r[j1], u))
        os_.append(vlerp(s[j0], s[j1], u))
    return op, orr, os_


# ------------------------------------------------------------------ 建立目标资产
if eal.does_asset_exist(NEW_PATH):
    new = eal.load_asset(NEW_PATH)
    unreal.log("### 目标已存在，直接复用 -> %s" % new.get_path_name())
else:
    new = eal.duplicate_asset(LOW_PATH, NEW_PATH)
    if not new:
        unreal.log_error("duplicate_asset 失败")
        raise SystemExit(1)
ctrl = new.controller
mi = ctrl.get_model_interface()
unreal.log("### 目标资产 %s ; 模型 keys=%d frames=%d" % (
    new.get_path_name(), mi.get_number_of_keys(), mi.get_number_of_frames()))

# 先把全部轨道按 LOW 重写一遍（幂等，保证基准干净）
base_ok = 0
for b in low_names:
    if not low_t[b][0]:
        continue
    if ctrl.set_bone_track_keys(
            b,
            [unreal.Vector(*v) for v in low_t[b][0]],
            [unreal.Quat(v[0], v[1], v[2], v[3]) for v in low_t[b][1]],
            [unreal.Vector(*v) for v in low_t[b][2]],
            False):
        base_ok += 1
unreal.log("### 基准（LOW 全轨）写入 %d/%d" % (base_ok, len(low_names)))

merged = {}
for b in low_names:
    merged[b] = (list(low_t[b][0]), list(low_t[b][1]), list(low_t[b][2]))

written = 0
failed = []
for b in sorted(upper):
    if not up_t.get(b) or not up_t[b][0]:
        continue
    op, orr, os_ = resample(up_t[b], UPPER_PHASE_SHIFT)
    ok = ctrl.set_bone_track_keys(
        b,
        [unreal.Vector(*v) for v in op],
        [unreal.Quat(v[0], v[1], v[2], v[3]) for v in orr],
        [unreal.Vector(*v) for v in os_],
        False)
    if ok:
        written += 1
        merged[b] = (op, orr, os_)
    else:
        failed.append(b)
unreal.log("### 上半身写入 %d/%d，失败 %d %s" % (written, len(upper), len(failed), failed[:8]))


# ------------------------------------------------------------------ 重新解算 weapon_jnt
def fk(bone, fi, tracks):
    chain = chains.get(bone) or []
    lc = {k.lower(): k for k in tracks}
    P, Q, S = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
    for bn in chain:
        key = bn if bn in tracks else lc.get(bn.lower())
        tr = tracks.get(key) if key else None
        if tr is None or not tr[0]:
            continue          # 缺轨道（如 UP 没有最外层骨）-> 按静止处理
        t, q, s = tr[0][fi], tr[1][fi], tr[2][fi]
        off = qrot(Q, (t[0] * S[0], t[1] * S[1], t[2] * S[2]))
        P = (P[0] + off[0], P[1] + off[1], P[2] + off[2])
        Q = qmul(Q, q)
        S = (S[0] * s[0], S[1] * s[1], S[2] * s[2])
    return P, Q, S


wj_pos, wj_rot, wj_scl = [], [], []
for fi in range(NKEY):
    cr = fk("weapon_jnt_r", fi, merged)
    cp = fk(parents.get("weapon_jnt"), fi, merged)
    if cr is None or cp is None:
        unreal.log_error("FK 失败 @ key %d" % fi)
        break
    Qi = qconj(cp[1])
    dt = tuple(cr[0][i] - cp[0][i] for i in range(3))
    lr = qrot(Qi, dt)
    wj_pos.append(tuple(lr[i] / cp[2][i] if abs(cp[2][i]) > 1e-9 else lr[i] for i in range(3)))
    wj_rot.append(qnorm(qmul(Qi, cr[1])))
    wj_scl.append(tuple(cr[2][i] / cp[2][i] if abs(cp[2][i]) > 1e-9 else 1.0 for i in range(3)))

if wj_pos:
    ok = ctrl.set_bone_track_keys(
        "weapon_jnt",
        [unreal.Vector(*v) for v in wj_pos],
        [unreal.Quat(v[0], v[1], v[2], v[3]) for v in wj_rot],
        [unreal.Vector(*v) for v in wj_scl],
        False)
    unreal.log("### weapon_jnt 重解算写入 = %s" % ok)
    merged["weapon_jnt"] = (wj_pos, wj_rot, wj_scl)

eal.save_asset(NEW_PATH)
unreal.log("### 已保存 %s" % NEW_PATH)

# ------------------------------------------------------------------ 校验
chk = eal.load_asset(NEW_PATH)
chk_t = read_poses(chk, low_names)


def cmp_tracks(a, b, bones, label):
    wr, wp, wb = 0.0, 0.0, None
    for bn in bones:
        ta, tb = a.get(bn), b.get(bn)
        if not ta or not tb or not ta[0]:
            continue
        m = min(len(ta[0]), len(tb[0]))
        for i in range(m):
            dr = qangle(ta[1][i], tb[1][i])
            dp = math.sqrt(sum((ta[0][i][k] - tb[0][i][k]) ** 2 for k in range(3))) * 100.0
            if dr > wr:
                wr = dr
            if dp > wp:
                wp = dp
                wb = bn
    unreal.log("### %-34s 最大角度差 %.3f deg  最大位移差 %.4f cm (worst %s)" % (label, wr, wp, wb))


lower_bones = [b for b in low_names if b not in upper and b not in REDERIVE]
cmp_tracks(chk_t, low_t, lower_bones, "下半身 vs LOW (应≈0)")
cmp_tracks(chk_t, merged, sorted(upper), "上半身 vs 重采样源 (应≈0)")
cmp_tracks(chk_t, low_t, REDERIVE, "重解算骨 vs LOW (预期有差)")

unreal.log("### weapon_jnt 是否跟随 weapon_jnt_r（应≈0）")
for fi in range(0, NKEY, max(1, NKEY // 8)):
    a = fk("weapon_jnt", fi, chk_t)
    b = fk("weapon_jnt_r", fi, chk_t)
    d = math.sqrt(sum((a[0][i] - b[0][i]) ** 2 for i in range(3)))
    unreal.log("   key %-3d dist=%.4f cm  rot=%.3f deg" % (fi, d, qangle(a[1], b[1])))

unreal.log("### component-space 落点 (cm)")
REF = ("pelvis", "spine_03", "head", "hand_r", "weapon_jnt", "weapon_jnt_r",
       "thigh_l", "calf_l", "foot_l", "ball_l", "toe_l", "foot_r", "ball_r")
unreal.log("   %-14s %-26s %-26s %-26s" % ("bone", "MERGED", "LOW", "UP"))
for b in REF:
    a = fk(b, 0, chk_t)
    c = fk(b, 0, low_t)
    d = fk(b, 0, up_t)
    f = lambda v: [round(x, 1) for x in v[0]] if v else None
    unreal.log("   %-14s %-26s %-26s %-26s" % (b, f(a), f(c), f(d)))

unreal.log("### MERGED 每帧最低骨（排除 camera/root/sync）")
SKIP = ("camera", "root", "sync_joint", "darius_godking")
for fi in range(0, NKEY, max(1, NKEY // 10)):
    lows = []
    for b in low_names:
        if any(b.startswith(s) for s in SKIP):
            continue
        p = fk(b, fi, chk_t)
        if p:
            lows.append((p[0][2], b))
    lows.sort(key=lambda x: x[0])
    unreal.log("   key %-3d %s" % (fi, [(b, round(z, 1)) for z, b in lows[:3]]))
unreal.log("### DONE")
