# -*- coding: utf-8 -*-
"""rtg_07_probe_root —— 只读：RTG 的 op 栈 / root 设置 / 两侧 root 骨位置，判定 +206cm root offset 是否合理"""

import unreal

L = unreal.log
LW = unreal.log_warning

RTG = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, RTG)
c = unreal.IKRetargeterController.get_controller(rtg)

# ---------------------------------------------------------------- op 栈（正确 API：按索引取名）
try:
    n = c.get_num_retarget_ops()
    L(f"[OPS] num = {n}")
    for i in range(n):
        nm = c.get_op_name(i)
        par = None
        try:
            par = c.get_parent_op_by_name(nm)
        except Exception:
            pass
        en = None
        try:
            en = c.get_retarget_op_enabled(nm)
        except Exception as ex:
            en = f"err {ex}"
        L(f"[OPS]   [{i}] {nm}   parent={par}  enabled={en}")
except Exception as ex:
    LW(f"[OPS] err {ex}")

for fn in ("get_root_settings", "get_global_settings"):
    f = getattr(c, fn, None)
    if f is None:
        continue
    for side, tag in ((unreal.RetargetSourceOrTarget.TARGET, "TARGET"), (unreal.RetargetSourceOrTarget.SOURCE, "SOURCE")):
        try:
            v = f(side)
            L(f"[OPS] {fn}({tag}) = {v}")
        except Exception as ex:
            try:
                v = f()
                L(f"[OPS] {fn}() = {v}   (no-side)")
                break
            except Exception as ex2:
                LW(f"[OPS] {fn} err {ex} / {ex2}")

# ---------------------------------------------------------------- 两侧 root 骨参考位置
TGT_RIG = unreal.load_object(None, "/Game/Character/Darius/IK/IK_Darius")
SRC_RIG = unreal.load_object(None, "/Game/Character/Darius/IK/IK_LOL_Darius")
ct = unreal.IKRigController.get_controller(TGT_RIG)
cs = unreal.IKRigController.get_controller(SRC_RIG)

L("[REF] --- TARGET ref pose (component space) ---")
for b in ("root", "pelvis", "spine_01", "foot_l", "ball_l", "foot_r", "hand_r", "weapon_jnt"):
    try:
        t = ct.get_ref_pose_transform_of_bone(unreal.Name(b))
        L(f"[REF]   TGT {b:<12} loc=({t.translation.x:8.2f},{t.translation.y:8.2f},{t.translation.z:8.2f})")
    except Exception as ex:
        LW(f"[REF]   TGT {b} err {ex}")

L("[REF] --- SOURCE ref pose (component space) ---")
for b in ("Root", "Pelvis", "Spine1", "L_Foot", "L_Toe", "R_Foot", "R_Hand", "Weapon"):
    try:
        t = cs.get_ref_pose_transform_of_bone(unreal.Name(b))
        L(f"[REF]   SRC {b:<12} loc=({t.translation.x:8.2f},{t.translation.y:8.2f},{t.translation.z:8.2f})")
    except Exception as ex:
        LW(f"[REF]   SRC {b} err {ex}")

# ---------------------------------------------------------------- 源 rig 全部链名（核对 39 条里的重复）
try:
    names = [str(ch.chain_name) for ch in cs.get_retarget_chains()]
    L(f"[CHAIN] SRC chains({len(names)}) = {names}")
except Exception as ex:
    LW(f"[CHAIN] src err {ex}")
try:
    names = [str(ch.chain_name) for ch in ct.get_retarget_chains()]
    dup = sorted({x for x in names if names.count(x) > 1})
    L(f"[CHAIN] TGT chains({len(names)}) dup={dup}")
    L(f"[CHAIN] TGT = {names}")
except Exception as ex:
    LW(f"[CHAIN] tgt err {ex}")

L("PROBE_ROOT_DONE")
