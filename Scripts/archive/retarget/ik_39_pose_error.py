# -*- coding: utf-8 -*-
"""逐骨**世界朝向误差**诊断器（比 ik_37 更细，用于定位与生成修正量）。

## 与 ik_37 的分工
- `ik_37` 量的是「关节连线方向」夹角 —— 是**门禁**（G1），但它只覆盖 13 段，
  且链尾骨（hand / foot / head）的自身朝向**不在**判据里。
- 本脚本量的是**每根骨的世界旋转**误差，并给出：
    `E(b) = Q_src_world(b) ∘ Q_tgt_world(b)⁻¹`  （把目标世界朝向转成源世界朝向所需的世界旋转）
  如果 `E(b)` 逐帧恒定 ⇒ 典型的 **retarget pose 静态偏移**，且 `E(b)` 就是要补的量。
  `drift`（E 随帧的最大漂移）大 ⇒ 不是静态偏移，得换方向查。

## 为什么用「世界旋转」而不是「局部旋转」
局部旋转依赖各自的绑定朝向约定（AGENTS.md §0.3 明确禁止）。
世界旋转只依赖「组件空间里这根骨朝哪」，两套骨架在同一个全局坐标系下可直接比。

## 已知前提
两套骨架的**全局朝向**未必一致（源 forward 是 −Y 还是 +Y 至今未敲定）。
所以本脚本额外打印 `pelvis` 的 E 作为「全局基准」参考：
若各骨 E 与 pelvis 的 E 高度一致 ⇒ 差的是全局朝向而不是姿势。
"""
import math
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

# ---------------------------------------------------------------- 四元数工具
IDQ = (0.0, 0.0, 0.0, 1.0)


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
    if n < 1e-12:
        return IDQ
    return (-x / n, -y / n, -z / n, w / n)


def qang(a, b):
    """a 与 b 的夹角（度），取最短路径。"""
    d = abs(a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3])
    d = max(-1.0, min(1.0, d))
    return math.degrees(2.0 * math.acos(d))


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def local_of(anim, bone, frame):
    t = AL.get_bone_pose_for_frame(anim, bone, frame, False)
    return ((t.translation.x, t.translation.y, t.translation.z),
            (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w))


def world_of(anim, bone, frame):
    """返回组件空间的 (位置, 旋转)。含缩放逐级复合。"""
    chain = [str(x) for x in AL.find_bone_path_to_root(anim, bone)][::-1]
    p, q, s = (0.0, 0.0, 0.0), IDQ, (1.0, 1.0, 1.0)
    for bn in chain:
        t, bq = local_of(anim, bn, frame)
        sc = (t[0] * s[0], t[1] * s[1], t[2] * s[2])
        off = mv(qmat(q), sc)
        p = (p[0] + off[0], p[1] + off[1], p[2] + off[2])
        q = qmul(q, bq)
    return p, q


# ---------------------------------------------------------------- 骨对应
PAIRS = [
    ("Hips",         "pelvis",     True),   # True = 全局基准参考
    ("Spine1",       "spine_01",   False),
    ("Spine2",       "spine_03",   False),
    ("Neck",         "neck_01",    False),
    ("Head",         "head",       True),   # 链尾
    ("L_Clavicle",   "clavicle_l", False),
    ("L_Shoulder",   "upperarm_l", False),
    ("L_Elbow",      "lowerarm_l", False),
    ("L_Hand",       "hand_l",     True),   # 链尾
    ("R_Clavicle",   "clavicle_r", False),
    ("R_Shoulder",   "upperarm_r", False),
    ("R_Elbow",      "lowerarm_r", False),
    ("R_Hand",       "hand_r",     True),   # 链尾
    ("L_Hip",        "thigh_l",    False),
    ("L_KneeLower",  "calf_l",     False),
    ("L_Foot",       "foot_l",     True),   # 链尾
    ("R_Hip",        "thigh_r",    False),
    ("R_KneeLower",  "calf_r",     False),
    ("R_Foot",       "foot_r",     True),   # 链尾
]

ANIMS = [
    ("idle1",
     "/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_idle1",
     "/Game/Character/Darius/Anims_TP/A_Darius_idle1"),
    ("run",
     "/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_run",
     "/Game/Character/Darius/Anims_TP/A_Darius_run"),
]


def analyse(tag, sa, ta):
    try:
        n = min(int(AL.get_num_frames(sa)), int(AL.get_num_frames(ta)))
    except Exception:
        n = 0
    if n <= 1:
        LW("  %s: 帧数不足（%d）" % (tag, n))
        return
    step = max(1, n // 12)
    frames = list(range(0, n, step))
    L("")
    L("################ %s（源 %d 帧 / 目标 %d 帧，抽样 %d 帧）"
      % (tag, int(AL.get_num_frames(sa)), int(AL.get_num_frames(ta)), len(frames)))
    L("   %-12s %9s %9s %9s   %s" % ("骨", "E均值", "E漂移", "与基准差", "E(首帧) 转成 rotator"))

    base = None
    for sb, tb, is_leaf in PAIRS:
        errs = []
        e0 = None
        for f in frames:
            try:
                _, qs = world_of(sa, sb, f)
                _, qt = world_of(ta, tb, f)
            except Exception as ex:
                LW("   %s 取样失败: %s" % (sb, str(ex)[:70]))
                errs = []
                break
            e = qmul(qs, qinv(qt))
            if e0 is None:
                e0 = e
            errs.append(qang(e, e0))
        if not errs:
            continue
        mean_drift = sum(errs) / len(errs)
        drift = max(errs)
        # E 的实际大小：用首帧的 E 作用到目标上，看与源差多少 —— 这里直接给 e0 的旋转角
        e0_angle = qang(e0, IDQ)
        if is_leaf and base is not None:
            rel = qang(e0, base)
        else:
            rel = float("nan")
        if sb == "Hips":
            base = e0
        try:
            q = unreal.Quat(e0[0], e0[1], e0[2], e0[3])
            r = q.rotator()
            rs = "(%.1f, %.1f, %.1f)" % (r.roll, r.pitch, r.yaw)
        except Exception:
            rs = str(e0)
        L("   %-12s %9.2f %9.2f %9s   %s  |E|=%.1f°%s"
          % (tb, e0_angle, drift, ("%.1f" % rel) if rel == rel else "-", rs, e0_angle,
             "  [链尾]" if is_leaf else ""))


L("=== 逐骨世界朝向误差（E = 目标→源 的世界旋转；逐帧恒定 ⇒ retarget pose 静态偏移）===")
L("    判读：E均值 大 + E漂移 ≈ 0  ⇒ 静态偏移，补 E 即可")
L("          E漂移 大               ⇒ 不是静态偏移，别往 retarget pose 上找")
for tag, sp, tp in ANIMS:
    sa = eal.load_asset(sp)
    ta = eal.load_asset(tp)
    if sa is None or ta is None:
        LW("  %s: 加载失败（源 %s / 目标 %s）" % (tag, sa is not None, ta is not None))
        continue
    analyse(tag, sa, ta)
L("=== DONE ===")
