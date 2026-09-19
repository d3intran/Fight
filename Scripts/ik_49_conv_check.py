# -*- coding: utf-8 -*-
"""判定「偏移 → retarget pose 世界朝向」的映射约定 —— **不需要导出，秒出结果**。

## 判据（构造上与全局朝向无关）
`W = W_parent · L_ret`，两种候选约定：
  A：`L_ret = O · L_rest`      （偏移在父空间前乘）
  B：`L_ret = L_rest · O`      （偏移在骨自身空间后乘）

同一链内两根骨的**相对世界朝向** `W(子)·W(父)⁻¹` **不含全局朝向 G**，可直接跨骨架比较。
取**腿链**做样本：`thigh_l` 的偏移是 `ik_37` 实测 **0.01°** 完美的已知良好值
（`calf_l` 5.77°），判别力极强 —— 约定若错，预测会偏 ~2×47° ≈ 95°。

比较对象：
  源（retarget pose = 其自身 rest pose，偏移全 0）：`W_src(L_KneeLower)·W_src(L_Hip)⁻¹`
  目标（用 ref pose 局部旋转 + 当前偏移，按约定 FK）：
       `W_tgt(calf_l)·W_tgt(thigh_l)⁻¹`

差 ≈ 0 的那种约定就是 UE 的真实约定。
"""
import math
import os
import json
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
MESH_SRC = "/Game/Character/Darius/LOL_Source/SK_LOL_Darius"
MESH_TGT = "/Game/Character/Darius/SK_Darius_GodKing"
E = unreal.RetargetSourceOrTarget
IDQ = (0.0, 0.0, 0.0, 1.0)


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


def read_skel(mesh_path):
    sm = eal.load_asset(mesh_path)
    a = actor_sub.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
    a.set_actor_label("Probe_Conv")
    comp = a.get_editor_property("skeletal_mesh_component")
    try:
        comp.set_skinned_asset_and_update(sm)
    except Exception:
        comp.set_skeletal_mesh(sm)
    n = int(comp.get_num_bones())
    names = [str(comp.get_bone_name(i)) for i in range(n)]
    par, loc = {}, {}
    for i, bn in enumerate(names):
        pn = None
        for arg in (i, bn):
            try:
                p = comp.get_parent_bone(arg)
                pn = str(p) if isinstance(p, str) else names[int(p)]
                break
            except Exception:
                pn = None
        par[bn] = pn
        try:
            t = comp.get_ref_pose_transform(i)
            r = t.rotation
            loc[bn] = (r.x, r.y, r.z, r.w)
        except Exception:
            loc[bn] = IDQ
    actor_sub.destroy_actor(a)
    return names, par, loc


def fk_world(bone, par, loc_of):
    chain, b, g = [], bone, 0
    while b and g < 600:
        chain.append(b)
        b = par.get(b)
        g += 1
    q = IDQ
    for bn in chain[::-1]:
        q = qmul(q, loc_of(bn))
    return q


rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)
src_names, src_par, src_loc = read_skel(MESH_SRC)
tgt_names, tgt_par, tgt_loc = read_skel(MESH_TGT)

off = {}
n_off = 0
for bn in tgt_names:
    q = None
    for args in ((bn, E.TARGET), (E.TARGET, bn)):
        try:
            o = ctrl.get_rotation_offset_for_retarget_pose_bone(*args)
            q = (o.x, o.y, o.z, o.w)
            break
        except Exception:
            q = None
    off[bn] = q if q is not None else IDQ
    if qang(off[bn], IDQ) > 0.05:
        n_off += 1
L("源骨 %d / 目标骨 %d ；目标非单位偏移 %d 根" % (len(src_names), len(tgt_names), n_off))

# 相对朝向样本：子骨, 父骨（源名, 目标名）
SAMPLES = [
    ("大腿-小腿", ("L_KneeLower", "L_Hip"), ("calf_l", "thigh_l")),
    ("大腿-小腿 R", ("R_KneeLower", "R_Hip"), ("calf_r", "thigh_r")),
    ("小腿-脚", ("L_Foot", "L_KneeLower"), ("foot_l", "calf_l")),
    ("脊柱1-2", ("Spine2", "Spine1"), ("spine_03", "spine_01")),
    ("肘-腕", ("L_Hand", "L_Elbow"), ("hand_l", "lowerarm_l")),
]

L("")
L("################ 相对朝向对照（源 vs 目标，两种约定）")
L("   %-14s %10s %10s   %s" % ("样本", "A 差(度)", "B 差(度)", "结论"))
tot = {"A": [], "B": []}
for tag, (s_child, s_par), (t_child, t_par) in SAMPLES:
    rel_src = qmul(fk_world(s_child, src_par, lambda b: src_loc[b]),
                   qinv(fk_world(s_par, src_par, lambda b: src_loc[b])))
    line = []
    for case in ("A", "B"):
        def loc_of(b, _c=case):
            return qmul(off[b], tgt_loc[b]) if _c == "A" else qmul(tgt_loc[b], off[b])
        rel_tgt = qmul(fk_world(t_child, tgt_par, loc_of), qinv(fk_world(t_par, tgt_par, loc_of)))
        d = qang(rel_src, rel_tgt)
        tot[case].append(d)
        line.append(d)
    L("   %-14s %10.2f %10.2f   %s"
      % (tag, line[0], line[1],
         ("A 更对" if line[0] < line[1] - 2 else ("B 更对" if line[1] < line[0] - 2 else "两者相近"))))

L("")
for case in ("A", "B"):
    v = tot[case]
    L("   约定 %s：平均 %.2f°  最大 %.2f°" % (case, sum(v) / len(v), max(v)))
L("")
LW("判读：差小（<10°）的那个约定才是 UE 的真实约定。两者都大 ⇒ 模型本身不对，别继续在这条路上花时间。")
L("=== DONE ===")
