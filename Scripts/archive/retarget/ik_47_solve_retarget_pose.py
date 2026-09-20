# -*- coding: utf-8 -*-
"""★ 解析求解 retarget pose：把每根骨的偏移直接算出来，而不是靠 auto align 猜。

## 数学（这轮推导的核心）

设 `W_ret(b)` = 骨 b 在 retarget pose 下的组件空间朝向，`D(b,f)` = retarget pose → 第 f 帧的旋转。
源与目标共用同一个 D（这正是重定向的语义），于是

    W_anim(b,f) = W_ret(b) · D(b,f)
    E(b) := W_anim_src(b,f) · W_anim_tgt(b,f)⁻¹ = W_ret_src(b) · W_ret_tgt(b)⁻¹   ← 与 f 无关

⇒ `E(b)` 就是「目标 retarget pose 离源 retarget pose 差多少」，**可从导出的动画实测**
  （不需要读 retarget pose 本身）。把它消成单位阵 = 标定完成。

## 解法
1. 由 ref pose 局部旋转 `L_rest`（`get_ref_pose_transform(索引)`）与 API 读到的偏移 `O_old`，
   FK 出当前 retarget pose 的世界朝向 `W_old(b)`。
   - 约定 A：`L_ret = O · L_rest`
   - 约定 B：`L_ret = L_rest · O`
2. 反解 `L_rest`（不依赖约定）：`L_rest = O_old⁻¹ · (W_old(par)⁻¹ W_old(b))`  （A）
                     或 `L_rest = (W_old(par)⁻¹ W_old(b)) · O_old⁻¹`        （B）
3. 期望世界朝向 `W_des(b) = F(b) · W_old(b)`，其中 `F(b) = E(b)`（绝对）
   或 `F(b) = E(ref)⁻¹ · E(b)`（相对参考骨，保住全局朝向不被改写）。
   没有实测 E 的骨（源无对应物）保持自己的旧局部旋转：`W_des(b) = W_des(par) · L_ret_old(b)`。
4. `O_new(b) = W_des(par)⁻¹ · W_des(b) · L_rest(b)⁻¹`（A）
   `O_new(b) = L_rest(b)⁻¹ · (W_des(par)⁻¹ · W_des(b))`（B）

## 配置（Saved/retarget_cycle.json）
`"solver": {"case": "A", "root_ref": "pelvis" | null, "apply": true, "frames": 5}`
"""
import json
import math
import os
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

CFG = "E:/UE/Fight/Saved/retarget_cycle.json"
RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
MESH_SRC = "/Game/Character/Darius/LOL_Source/SK_LOL_Darius"
MESH_TGT = "/Game/Character/Darius/SK_Darius_GodKing"
ANIM_SRC = "/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_idle1"
E = unreal.RetargetSourceOrTarget
IDQ = (0.0, 0.0, 0.0, 1.0)

cfg = {}
if os.path.isfile(CFG):
    with open(CFG, encoding="utf-8") as fh:
        cfg = json.load(fh)
sol = cfg.get("solver") or {}
CASE = str(sol.get("case", "A")).upper()
ROOT_REF = sol.get("root_ref", "pelvis")
APPLY = bool(sol.get("apply", False))
NFRAMES = int(sol.get("frames", 5))
# ⚠️ 两个目录要分清：
#   `pose_anim_dir` = **与当前 retarget pose 对应的那次导出**（量 E 必须用它）
#   `out_dir`       = 下一轮 ik_11 要写的新目录
TGT_DIR = cfg.get("pose_anim_dir") or cfg.get("out_dir") or "/Game/Character/Darius/Anims_TP"
ANIM_TGT = TGT_DIR + "/A_Darius_idle1"

PAIRS = [
    ("Pelvis", "pelvis"), ("Spine1", "spine_01"), ("Spine2", "spine_03"),
    ("Neck", "neck_01"), ("Head", "head"),
    ("L_Clavicle", "clavicle_l"), ("L_Shoulder", "upperarm_l"),
    ("L_Elbow", "lowerarm_l"), ("L_Hand", "hand_l"),
    ("R_Clavicle", "clavicle_r"), ("R_Shoulder", "upperarm_r"),
    ("R_Elbow", "lowerarm_r"), ("R_Hand", "hand_r"),
    ("L_Hip", "thigh_l"), ("L_KneeLower", "calf_l"), ("L_Foot", "foot_l"),
    ("R_Hip", "thigh_r"), ("R_KneeLower", "calf_r"), ("R_Foot", "foot_r"),
]


# ---------------------------------------------------------------- 四元数
def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qinv(q):
    x, y, z, w = q
    n = x * x + y * y + z * z + w * w
    return IDQ if n < 1e-12 else (-x / n, -y / n, -z / n, w / n)


def qang(a, b):
    d = abs(a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3])
    return math.degrees(2.0 * math.acos(max(-1.0, min(1.0, d))))


def qavg(qs):
    """半球对齐后分量平均再归一化（避免正负号翻转把平均毁掉）。"""
    if not qs:
        return IDQ
    ref = qs[0]
    acc = [0.0, 0.0, 0.0, 0.0]
    for q in qs:
        s = 1.0 if sum(q[i] * ref[i] for i in range(4)) >= 0 else -1.0
        for i in range(4):
            acc[i] += s * q[i]
    n = sum(x * x for x in acc) ** 0.5
    return tuple(x / n for x in acc) if n > 1e-9 else IDQ


def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


# ---------------------------------------------------------------- 骨架
def read_skeleton(mesh_path):
    sm = eal.load_asset(mesh_path)
    a = actor_sub.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
    a.set_actor_label("Probe_Solver")
    comp = a.get_editor_property("skeletal_mesh_component")
    try:
        comp.set_skinned_asset_and_update(sm)
    except Exception:
        comp.set_skeletal_mesh(sm)
    n = int(comp.get_num_bones())
    names = [str(comp.get_bone_name(i)) for i in range(n)]
    parents, loc = {}, {}
    for i, bn in enumerate(names):
        pname = None
        for arg in (i, bn):
            try:
                p = comp.get_parent_bone(arg)
                pname = str(p) if isinstance(p, str) else names[int(p)]
                break
            except Exception:
                pname = None
        parents[bn] = pname
        try:
            t = comp.get_ref_pose_transform(i)      # ← 必须是索引
            r = t.rotation
            loc[bn] = ((t.translation.x, t.translation.y, t.translation.z),
                       (r.x, r.y, r.z, r.w))
        except Exception:
            loc[bn] = ((0.0, 0.0, 0.0), IDQ)
    # 自检：ref pose 局部变换 FK 出来的位置，应与 get_ref_pose_position 一致
    bad = []
    for i, bn in enumerate(names[:40]):
        try:
            ref = comp.get_ref_pose_position(i)
            ref = (ref.x, ref.y, ref.z)
        except Exception:
            continue
        pos, q = (0.0, 0.0, 0.0), IDQ
        cur, guard = bn, 0
        chain = []
        while cur and guard < 600:
            chain.append(cur)
            cur = parents.get(cur)
            guard += 1
        for c in chain[::-1]:
            t, bq = loc[c]
            off = mv(qmat(q), t)
            pos = (pos[0] + off[0], pos[1] + off[1], pos[2] + off[2])
            q = qmul(q, bq)
        d = sum((pos[k] - ref[k]) ** 2 for k in range(3)) ** 0.5
        if d > 1.0:
            bad.append("%s:%.1fcm" % (bn, d))
    actor_sub.destroy_actor(a)
    return names, parents, loc, bad


def chain_of(bone, parents):
    out, b, g = [], bone, 0
    while b and g < 600:
        out.append(b)
        b = parents.get(b)
        g += 1
    return out[::-1]


def world_from_anim(anim, bone, frame):
    ch = [str(x) for x in AL.find_bone_path_to_root(anim, bone)][::-1]
    if not ch:
        raise ValueError("empty chain for %s" % bone)
    q = IDQ
    for bn in ch:
        t = AL.get_bone_pose_for_frame(anim, bn, frame, False)
        q = qmul(q, (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w))
    return q


# ---------------------------------------------------------------- 数据
rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)
src_names, src_parents, src_loc, _ = read_skeleton(MESH_SRC)
tgt_names, tgt_parents, tgt_loc, bad = read_skeleton(MESH_TGT)
L("源骨 %d / 目标骨 %d" % (len(src_names), len(tgt_names)))
L("ref pose 局部变换自检：%s" % ("全部通过" if not bad else "异常 %s" % bad[:5]))

O_old = {}
for bn in tgt_names:
    q = None
    for args in ((bn, E.TARGET), (E.TARGET, bn)):
        try:
            q = ctrl.get_rotation_offset_for_retarget_pose_bone(*args)
            break
        except Exception:
            q = None
    O_old[bn] = (q.x, q.y, q.z, q.w) if q is not None else IDQ

# 实测 E（多帧四元数平均）
sa = eal.load_asset(ANIM_SRC)
ta = eal.load_asset(ANIM_TGT)
L("anim: src=%s  tgt=%s" % (sa.get_name() if sa else None, ta.get_name() if ta else None))
try:
    nfr = min(int(AL.get_num_frames(sa)), int(AL.get_num_frames(ta)))
except Exception:
    nfr = 1
frames = [int(round(i * (nfr - 1) / max(1, NFRAMES - 1))) for i in range(NFRAMES)] if nfr > 1 else [0]
L("E 采样帧 = %s（共 %d 帧）" % (frames, nfr))

E_meas = {}
for sb, tb in PAIRS:
    if sb not in set(src_names):
        continue
    qs = []
    for f in frames:
        try:
            qs.append(qmul(world_from_anim(sa, sb, f), qinv(world_from_anim(ta, tb, f))))
        except Exception:
            pass
    if qs:
        E_meas[tb] = qavg(qs)
        spread = max(qang(q, qs[0]) for q in qs)
        L("   E(%-12s) |E|=%.1f°  帧间漂移=%.1f°" % (tb, qang(qavg(qs), IDQ), spread))

# ---------------------------------------------------------------- FK 出当前 retarget pose
W_old = {}
for bn in tgt_names:
    par = tgt_parents.get(bn)
    Wpar = W_old.get(par, IDQ) if par else IDQ
    Lr = tgt_loc[bn][1]
    Lret = qmul(O_old[bn], Lr) if CASE == "A" else qmul(Lr, O_old[bn])
    W_old[bn] = qmul(Wpar, Lret)

# 反解 L_rest（不依赖约定）
L_rest = {}
for bn in tgt_names:
    par = tgt_parents.get(bn)
    Wpar = W_old.get(par, IDQ) if par else IDQ
    Lret_old = qmul(qinv(Wpar), W_old[bn])
    L_rest[bn] = qmul(qinv(O_old[bn]), Lret_old) if CASE == "A" else qmul(Lret_old, qinv(O_old[bn]))

# ---------------------------------------------------------------- 期望世界朝向
Gref = qinv(E_meas[ROOT_REF]) if (ROOT_REF and ROOT_REF in E_meas) else IDQ
L("参考骨 ROOT_REF=%s ⇒ 全局补偿 G=%s" % (ROOT_REF, "启用" if ROOT_REF else "关闭"))

W_des = {}
n_fix = 0
for bn in tgt_names:                       # tgt_names 已是父先子后
    par = tgt_parents.get(bn)
    Wpar_old = W_old.get(par, IDQ) if par else IDQ
    if bn in E_meas:
        F = qmul(Gref, E_meas[bn]) if ROOT_REF else E_meas[bn]
        W_des[bn] = qmul(F, W_old[bn])
        n_fix += 1
    else:
        Lret_old = qmul(qinv(Wpar_old), W_old[bn])
        Wpar_des = W_des.get(par, IDQ) if par else IDQ
        W_des[bn] = qmul(Wpar_des, Lret_old)

L("将被改写的骨 = %d（有实测 E 的）" % n_fix)

# ---------------------------------------------------------------- 解 O_new
O_new = {}
for bn in tgt_names:
    par = tgt_parents.get(bn)
    Wpar_des = W_des.get(par, IDQ) if par else IDQ
    Lret_new = qmul(qinv(Wpar_des), W_des[bn])
    O_new[bn] = qmul(qinv(Lret_new), L_rest[bn]) if CASE == "A" else qmul(L_rest[bn], qinv(Lret_new))

L("")
L("################ 新旧偏移对照（只列有实测 E 的骨 + 变化显著的）")
L("   %-14s %-26s %-26s %s" % ("骨", "旧偏移 rotator", "新偏移 rotator", "变化(度)"))
for sb, tb in PAIRS:
    o_old, o_new = O_old[tb], O_new[tb]
    d = qang(o_old, o_new)
    try:
        ro = unreal.Quat(*o_old).rotator()
        rn = unreal.Quat(*o_new).rotator()
        s_old = "(%7.2f,%7.2f,%7.2f)" % (ro.roll, ro.pitch, ro.yaw)
        s_new = "(%7.2f,%7.2f,%7.2f)" % (rn.roll, rn.pitch, rn.yaw)
    except Exception:
        s_old, s_new = "?", "?"
    L("   %-14s %-26s %-26s %7.2f" % (tb, s_old, s_new, d))

# ---------------------------------------------------------------- 写回
if APPLY:
    L("")
    L("################ 写回 retarget pose（约定 %s）" % CASE)
    ok = 0
    for bn in tgt_names:
        if bn not in E_meas:
            continue
        q = unreal.Quat(*O_new[bn])
        wrote = False
        for args in ((bn, E.TARGET, q), (E.TARGET, bn, q), (bn, q, E.TARGET)):
            try:
                ctrl.set_rotation_offset_for_retarget_pose_bone(*args)
                wrote = True
                break
            except Exception:
                continue
        ok += 1 if wrote else 0
    L("   写入 %d / %d 根骨" % (ok, len(E_meas)))
    L("   存盘 -> %s" % eal.save_asset(RTG, only_if_is_dirty=False))
    LW("!! retarget pose 已改 ⇒ 必须重跑 ik_11 再跑 ik_37。")
else:
    L("")
    LW("APPLY=false —— 只算不写。把 Saved/retarget_cycle.json 的 solver.apply 改成 true 才写回。")
L("=== DONE ===")
