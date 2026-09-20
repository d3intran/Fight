import math
import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

UP_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Mixamo"      # 上半身
LOW_PATH = "/Game/Character/Darius/Anims_TP_v2/A_Darius_idle1"       # 基准（长度/轨道集合）
LB_PATH = "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"       # 下半身来源
NEW_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"

SPINE_ROOT = "spine_01"
REDERIVE = ["weapon_jnt"]
LB_FRAME = 2           # 走路里「左右次序正确 + 站姿最窄(74.7cm) + 两脚高度差小」的帧
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
    return qnorm(tuple(a[i] * math.sin(th0 - th0 * t) / math.sin(th0) +
                       b[i] * math.sin(th0 * t) / math.sin(th0) for i in range(4)))


def vlerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def qangle(a, b):
    d = abs(sum(x * y for x, y in zip(a, b)))
    return math.degrees(2.0 * math.acos(max(-1.0, min(1.0, d))))


up = eal.load_asset(UP_PATH)
low = eal.load_asset(LOW_PATH)
lb = eal.load_asset(LB_PATH)
if not (up and low and lb):
    unreal.log_error("源加载失败")
    raise SystemExit(1)


def track_names(a):
    return [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]


low_names = track_names(low)
lb_names = track_names(lb)
OUTER = [n for n in lb_names if n.lower().startswith("darius_godking_mesh")][0]
unreal.log("### LOW 轨道 %d / LB 轨道 %d / 最外层骨 = %s" % (len(low_names), len(lb_names), OUTER))

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
unreal.log("### spine_01 子树 %d 根；下半身（非子树）%d 根"
           % (len(upper), len([b for b in low_names if b not in upper])))


def read_all(a, names, frames=None):
    nf = int(AL.get_num_frames(a))
    fl = frames if frames is not None else list(range(nf + 1))
    objs = [unreal.Name(b) for b in names]
    out = {b: ([], [], []) for b in names}
    for f in fl:
        poses = AL.get_bone_poses_for_frame(a, objs, min(f, nf), False)
        for i, b in enumerate(names):
            t = poses[i]
            out[b][0].append((t.translation.x, t.translation.y, t.translation.z))
            out[b][1].append((t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w))
            out[b][2].append((t.scale3d.x, t.scale3d.y, t.scale3d.z))
    return out


# 基准（决定长度与轨道集合）
low_t = read_all(low, low_names)
NKEY = len(low_t["pelvis"][0])
unreal.log("### 目标 key = %d（%d 帧）" % (NKEY, NKEY - 1))
# 上半身源（2 帧）
up_t = read_all(up, low_names)
# 下半身源：走路的第 LB_FRAME 帧，冻成常量
lb_t = read_all(lb, low_names + ([OUTER] if OUTER not in low_names else []), frames=[LB_FRAME])

ctrl = eal.load_asset(NEW_PATH).controller
unreal.log("### 目标 keys=%d" % ctrl.get_model_interface().get_number_of_keys())

merged = {}
const_ok = 0
for b in low_names:
    if b in upper:
        src = up_t.get(b)
        if src and src[0]:
            n = len(src[0]) - 1
            op, orr, os_ = [], [], []
            for i in range(NKEY):
                f = (i * float(n) / float(NKEY - 1)) % n
                j0 = int(math.floor(f))
                j1 = (j0 + 1) % n
                u = f - j0
                op.append(vlerp(src[0][j0], src[0][j1], u))
                orr.append(qslerp(src[1][j0], src[1][j1], u))
                os_.append(vlerp(src[2][j0], src[2][j1], u))
            merged[b] = (op, orr, os_)
        continue
    v = lb_t.get(b)
    if v and v[0]:
        merged[b] = ([v[0][0]] * NKEY, [v[1][0]] * NKEY, [v[2][0]] * NKEY)
        const_ok += 1
unreal.log("### 下半身按走路第 %d 帧冻成常量：%d 根；上半身取 Mixamo 源：%d 根"
           % (LB_FRAME, const_ok, len([b for b in merged if b in upper])))

# 最外层骨（LOW 没有这条轨道，补上，让接地基准与走路一致）
outer_v = lb_t.get(OUTER)
if outer_v and outer_v[0]:
    try:
        ctrl.add_bone_track(OUTER, False)
        unreal.log("### add_bone_track(%s) ok" % OUTER)
    except Exception as ex:
        unreal.log("### add_bone_track ERR %s" % str(ex)[:70])
    merged[OUTER] = ([outer_v[0][0]] * NKEY, [outer_v[1][0]] * NKEY, [outer_v[2][0]] * NKEY)

written = 0
for b, (op, orr, os_) in merged.items():
    if ctrl.set_bone_track_keys(b, [unreal.Vector(*v) for v in op],
                               [unreal.Quat(v[0], v[1], v[2], v[3]) for v in orr],
                               [unreal.Vector(*v) for v in os_], False):
        written += 1
unreal.log("### 写入 %d / %d 根" % (written, len(merged)))


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


for bone, amp, cyc in BREATH:
    if bone not in merged:
        continue
    par = parents.get(bone)
    new_rot = []
    for i in range(NKEY):
        pr, pq, ps = fk(par, i)
        right = qrot(pq, (1.0, 0.0, 0.0))
        dR = qaxis(right, amp * math.sin(2.0 * math.pi * cyc * i / float(NKEY)))
        q_new = qnorm(qmul(qmul(qconj(pq), dR), qmul(pq, merged[bone][1][i])))
        new_rot.append(q_new)
    merged[bone] = (merged[bone][0], new_rot, merged[bone][2])
    ctrl.set_bone_track_keys(bone, [unreal.Vector(*v) for v in merged[bone][0]],
                            [unreal.Quat(v[0], v[1], v[2], v[3]) for v in new_rot],
                            [unreal.Vector(*v) for v in merged[bone][2]], False)
unreal.log("### 呼吸已叠（%s）" % BREATH)

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
ctrl.set_bone_track_keys("weapon_jnt", [unreal.Vector(*v) for v in wj_pos],
                        [unreal.Quat(v[0], v[1], v[2], v[3]) for v in wj_rot],
                        [unreal.Vector(*v) for v in wj_scl], False)
merged["weapon_jnt"] = (wj_pos, wj_rot, wj_scl)
unreal.log("### weapon_jnt 重解算 ok")

unreal.log("### save -> %s" % eal.save_asset(NEW_PATH))

# ---------------- 校验
chk = eal.load_asset(NEW_PATH)
chk_t = read_all(chk, list(merged.keys()))
unreal.log("### 与走路第 %d 帧逐骨比对（下半身应≈0）" % LB_FRAME)
worst = (0.0, None)
for b in merged:
    if b in upper or b == "weapon_jnt":
        continue
    v = lb_t.get(b)
    if not v or not v[0]:
        continue
    d = qangle(chk_t[b][1][0], v[1][0])
    if d > worst[0]:
        worst = (d, b)
unreal.log("   下半身最大角差 %.3f° (%s)" % worst)
unreal.log("### 与 Mixamo 源比对（上半身应≈0）")
worst2 = (0.0, None)
for b in upper:
    if b not in merged:
        continue
    d = qangle(chk_t[b][1][0], merged[b][1][0])
    if d > worst2[0]:
        worst2 = (d, b)
unreal.log("   上半身最大角差 %.3f° (%s)" % worst2)
unreal.log("### 循环接缝")
w = (0.0, None)
for b in merged:
    a0 = chk_t[b][0][0]
    a1 = chk_t[b][0][-1]
    d = math.sqrt(sum((a0[k] - a1[k]) ** 2 for k in range(3)))
    if d > w[0]:
        w = (d, b)
unreal.log("   最大 %.4f cm (%s)" % w)

# ---- 腿部左右次序（★ 自校准：角色右轴 = 锁骨线的水平分量，不依赖任何坐标约定）
sv = tuple(fk("clavicle_r", 0)[0][i] - fk("clavicle_l", 0)[0][i] for i in range(3))
nn = math.hypot(sv[0], sv[1]) or 1.0
right = (sv[0] / nn, sv[1] / nn)
pel0 = fk("pelvis", 0)[0]


def lat(b):
    p = fk(b, 0)[0]
    return (p[0] - pel0[0]) * right[0] + (p[1] - pel0[1]) * right[1]


unreal.log("### 腿部左右次序（左应<0、右应>0）")
for lvl, a_, b_ in (("髋", "thigh_l", "thigh_r"), ("膝", "calf_l", "calf_r"),
                    ("踝", "foot_l", "foot_r"), ("掌", "ball_l", "ball_r"), ("趾", "toe_l", "toe_r")):
    la, lb2 = lat(a_), lat(b_)
    unreal.log("   %-3s %-9s %+7.1f  %-9s %+7.1f  次序差 %+7.1f  %s"
               % (lvl, a_, la, b_, lb2, lb2 - la, "交叉!" if lb2 - la < 0 else "正常"))
unreal.log("   脚间距 %.1f cm   鞋底高 %.1f / %.1f" % (
    math.dist(fk("ball_l", 0)[0], fk("ball_r", 0)[0]),
    fk("ball_l", 0)[0][2], fk("ball_r", 0)[0][2]))
unreal.log("### DONE")
