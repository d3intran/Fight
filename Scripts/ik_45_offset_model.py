# -*- coding: utf-8 -*-
"""判定 retarget pose 的「偏移 → 世界朝向」映射约定，并**解析求出**正确偏移。

## 推导（这一步是整个标定问题的钥匙）

设 `W_ret(b)` = 骨 b 在 **retarget pose** 下的组件空间朝向，`D(b,f)` = 从 retarget pose
到第 f 帧动画的旋转（世界轴）。则

    W_anim(b,f) = W_ret(b) · D(b,f)        （源与目标共用同一个 D，这正是重定向的语义）

于是
    E(b) := W_anim_src(b,f) · W_anim_tgt(b,f)⁻¹
          = W_ret_src(b) · D · D⁻¹ · W_ret_tgt(b)⁻¹
          = W_ret_src(b) · W_ret_tgt(b)⁻¹      ← **与 f 无关**

⇒ **`ik_39` 量到的 E(b) 就是「两套 retarget pose 的世界朝向差」**，
  而且它可测（从导出的动画算），无需读 retarget pose 本身。
  把它消成单位阵 = 标定完成。这也解释了为什么 E 逐帧恒定。

## 要解的方程
目标是 `W_ret_tgt_new(b) = W_ret_src(b) = E(b) · W_ret_tgt_old(b)`。

设 retarget pose 的局部旋转有两种可能约定：
  - **A（前乘）**：`L_ret(b) = O(b) · L_rest(b)`
  - **B（后乘）**：`L_ret(b) = L_rest(b) · O(b)`
其中 `L_rest` 来自 `get_ref_pose_transform`（ref pose 的父相对变换），`O` 是 API 读到的偏移。

按 FK 自根向叶推进，两种约定都能解出 `O_new(b)`（见下方代码）。

## 本脚本只读 + 自检，不改任何资产
判据：把两种约定各自推出的 `E_pred(b)` 与**实测** `E_meas(b)` 比。
差 ≈ 0 的那种约定就是 UE 的真实约定。
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

RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
MESH_SRC = "/Game/Character/Darius/LOL_Source/SK_LOL_Darius"
MESH_TGT = "/Game/Character/Darius/SK_Darius_GodKing"
E = unreal.RetargetSourceOrTarget
IDQ = (0.0, 0.0, 0.0, 1.0)

ANIM_SRC = "/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_idle1"
# ⚠️ 必须与**当前 retarget pose** 对应的那次导出一致（读 Saved/retarget_cycle.json）
CFG = "E:/UE/Fight/Saved/retarget_cycle.json"
_TGT_DIR = "/Game/Character/Darius/Anims_TP"
if os.path.isfile(CFG):
    try:
        with open(CFG, encoding="utf-8") as fh:
            _TGT_DIR = json.load(fh).get("out_dir") or _TGT_DIR
    except Exception:
        pass
ANIM_TGT = _TGT_DIR + "/A_Darius_idle1"

# 源骨 -> 目标骨
# ⚠️ 源骨架里**没有** `Hips`，躯干根叫 `Pelvis`（2026-09-19 踩：`find_bone_path_to_root`
#    对不存在的骨名**返回空数组而不报错**，于是静默算出垃圾值，ik_39 里那行 pelvis 就是垃圾）。
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
def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


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


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


# ---------------------------------------------------------------- 骨架读取
def read_skeleton(mesh_path):
    """返回 (骨名列表, parent 映射, ref pose 局部变换)。借临时 SkeletalMeshActor。"""
    sm = eal.load_asset(mesh_path)
    a = actor_sub.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
    a.set_actor_label("Probe_Skel45")
    comp = a.get_editor_property("skeletal_mesh_component")
    try:
        comp.set_skinned_asset_and_update(sm)
    except Exception:
        comp.set_skeletal_mesh(sm)
    n = int(comp.get_num_bones())
    names = [str(comp.get_bone_name(i)) for i in range(n)]
    parents, locals_ = {}, {}
    for i, bn in enumerate(names):
        try:
            p = comp.get_parent_bone(bn)
            parents[bn] = str(p) if isinstance(p, str) else names[int(p)]
        except Exception:
            parents[bn] = None
        try:
            t = comp.get_ref_pose_transform(bn)
            r = t.rotation
            locals_[bn] = ((t.translation.x, t.translation.y, t.translation.z),
                           (r.x, r.y, r.z, r.w))
        except Exception as ex:
            locals_[bn] = ((0.0, 0.0, 0.0), IDQ)
    actor_sub.destroy_actor(a)
    return names, parents, locals_


def chain_of(bone, parents):
    out = []
    b = bone
    guard = 0
    while b is not None and guard < 600:
        out.append(b)
        b = parents.get(b)
        guard += 1
    return out[::-1]


def fk_world(bone, parents, loc_of):
    """loc_of(bone) -> (t, q)。返回 (pos, world_quat)。"""
    p, q = (0.0, 0.0, 0.0), IDQ
    for bn in chain_of(bone, parents):
        t, bq = loc_of(bn)
        off = mv(qmat(q), t)
        p = (p[0] + off[0], p[1] + off[1], p[2] + off[2])
        q = qmul(q, bq)
    return p, q


def world_from_anim(anim, bone, frame):
    chain = [str(x) for x in AL.find_bone_path_to_root(anim, bone)][::-1]
    p, q = (0.0, 0.0, 0.0), IDQ
    for bn in chain:
        t = AL.get_bone_pose_for_frame(anim, bn, frame, False)
        bq = (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w)
        sc = (t.translation.x, t.translation.y, t.translation.z)
        off = mv(qmat(q), sc)
        p = (p[0] + off[0], p[1] + off[1], p[2] + off[2])
        q = qmul(q, bq)
    return p, q


# ---------------------------------------------------------------- 读数据
rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)
src_names, src_parents, src_loc = read_skeleton(MESH_SRC)
tgt_names, tgt_parents, tgt_loc = read_skeleton(MESH_TGT)
L("源骨 %d / 目标骨 %d" % (len(src_names), len(tgt_names)))

off = {}
n_off = 0
for bn in tgt_names:
    o = None
    for args in ((bn, E.TARGET), (E.TARGET, bn)):
        try:
            q = ctrl.get_rotation_offset_for_retarget_pose_bone(*args)
            o = (q.x, q.y, q.z, q.w)
            break
        except Exception:
            o = None
    if o is None:
        o = IDQ
    elif qang(o, IDQ) > 0.05:
        n_off += 1
    off[bn] = o
L("目标侧有非零偏移的骨 = %d" % n_off)

# ---------------------------------------------------------------- 实测 E
sa = eal.load_asset(ANIM_SRC)
ta = eal.load_asset(ANIM_TGT)
E_meas = {}
_src_set = set(src_names)
for sb, tb in PAIRS:
    if sb not in _src_set:
        LW("  源骨 %r 不存在于 %s" % (sb, MESH_SRC.split("/")[-1]))
        continue
    try:
        _, qs = world_from_anim(sa, sb, 0)
        _, qt = world_from_anim(ta, tb, 0)
        E_meas[tb] = qmul(qs, qinv(qt))
    except Exception as ex:
        LW("  E_meas %s 失败: %s" % (tb, str(ex)[:70]))

# ---------------------------------------------------------------- 两种约定下的预测
def predict(case):
    """按约定推出 W_ret_tgt(b)（用 API 读到的偏移 + ref pose）。"""
    W = {}
    for bn in tgt_names:
        par = tgt_parents.get(bn)
        Wpar = W.get(par, IDQ) if par else IDQ
        Lr = tgt_loc[bn][1]
        o = off[bn]
        Lret = qmul(o, Lr) if case == "A" else qmul(Lr, o)
        W[bn] = qmul(Wpar, Lret)
    return W


L("")
L("################ 判据：E_pred 与 E_meas 的角度差（越小说明该约定越对）")
for case in ("A", "B"):
    Wt = predict(case)
    L("")
    L("   ---- 约定 %s（%s）" % (case, "L_ret = O · L_rest" if case == "A" else "L_ret = L_rest · O"))
    L("   %-12s %9s   %s" % ("骨", "差(度)", "E_pred 转 rotator"))
    diffs = []
    for sb, tb in PAIRS:
        if tb not in E_meas:
            continue
        _, qs = fk_world(sb, src_parents, lambda b: (src_loc[b][0], src_loc[b][1]))
        Epred = qmul(qs, qinv(Wt[tb]))
        d = qang(Epred, E_meas[tb])
        diffs.append(d)
        try:
            rr = unreal.Quat(*Epred).rotator()
            rs = "(%.1f, %.1f, %.1f)" % (rr.roll, rr.pitch, rr.yaw)
        except Exception:
            rs = "?"
        L("   %-12s %9.2f   %s" % (tb, d, rs))
    if diffs:
        L("   ⇒ 平均差 %.2f°  最大 %.2f°" % (sum(diffs) / len(diffs), max(diffs)))

L("")
L("################ 参考：实测 E_meas 本身")
for sb, tb in PAIRS:
    if tb not in E_meas:
        continue
    try:
        rr = unreal.Quat(*E_meas[tb]).rotator()
        L("   %-12s |E|=%.1f°  rotator=(%.1f, %.1f, %.1f)"
          % (tb, qang(E_meas[tb], IDQ), rr.roll, rr.pitch, rr.yaw))
    except Exception:
        pass
L("=== DONE ===")
