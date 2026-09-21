# -*- coding: utf-8 -*-
"""rtg_31_state_dump —— 只读：把 RTG 当前状态（root/姿态偏移/链映射/op）完整落成 JSON + 日志"""

import unreal
import json

L = unreal.log
LW = unreal.log_warning

RTG = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
IK_T = "/Game/Character/Darius/IK/IK_Darius"
IK_S = "/Game/Character/Darius/IK/IK_LOL_Darius"
OUT = "E:/UE/Fight/Saved/Attack/rtg_state_after_fix.json"

rtg = unreal.load_object(None, RTG)
c = unreal.IKRetargeterController.get_controller(rtg)
snap = {"asset": RTG}

try:
    rs = c.get_root_settings()
    ro = rs.get_editor_property("rotation_offset")
    to = rs.get_editor_property("translation_offset")
    snap["target_root_settings"] = {"rotation_offset": [ro.pitch, ro.yaw, ro.roll],
                                    "translation_offset": [to.x, to.y, to.z],
                                    "blend_to_source": rs.get_editor_property("blend_to_source"),
                                    "rotation_alpha": rs.get_editor_property("rotation_alpha"),
                                    "translation_alpha": rs.get_editor_property("translation_alpha")}
    L(f"[STATE] TargetRootSettings rot=({ro.pitch:.2f},{ro.yaw:.2f},{ro.roll:.2f}) trans=({to.x:.2f},{to.y:.2f},{to.z:.2f})")
except Exception as ex:
    LW(f"[STATE] root settings err {ex}")

for side, tag in ((unreal.RetargetSourceOrTarget.TARGET, "TARGET"), (unreal.RetargetSourceOrTarget.SOURCE, "SOURCE")):
    try:
        v = c.get_root_offset_in_retarget_pose(side)
        snap[f"{tag}_root_offset"] = [v.x, v.y, v.z]
        L(f"[STATE] {tag} retarget-pose root offset = ({v.x:.3f}, {v.y:.3f}, {v.z:.3f})")
    except Exception as ex:
        LW(f"[STATE] {tag} root offset err {ex}")

# op 栈
ops = []
for i in range(c.get_num_retarget_ops()):
    nm = str(c.get_op_name(i))
    entry = {"index": i, "name": nm}
    try:
        oc = c.get_op_controller(i)
        st = oc.get_settings()
        entry["enabled"] = st.get_editor_property("enabled")
        if nm == "Pelvis Motion":
            rg = st.get_editor_property("rotation_offset_global")
            entry["rotation_offset_global"] = [rg.pitch, rg.yaw, rg.roll]
        if nm == "FK Chains":
            arr = st.get_editor_property("chains_to_retarget")
            entry["chain_count"] = len(arr)
            entry["rotation_mode_sample"] = str(arr[0].get_editor_property("rotation_mode")) if arr else None
        if nm == "Run IK Rig":
            entry["ik_chains"] = [str(x.get_editor_property("target_chain_name")) for x in st.get_editor_property("chains")]
    except Exception as ex:
        entry["err"] = str(ex)
    ops.append(entry)
snap["ops"] = ops
for o in ops:
    L(f"[STATE] op[{o.get('index')}] {o.get('name'):<14} enabled={o.get('enabled')} {({k: v for k, v in o.items() if k not in ('index', 'name', 'enabled')})}")

# 链映射（以目标 rig 的链名枚举）
try:
    tgt_rig = unreal.load_object(None, IK_T)
    tgt_chains = [str(ch.chain_name) for ch in unreal.IKRigController.get_controller(tgt_rig).get_retarget_chains()]
    mapping = {}
    for ch in tgt_chains:
        mapping[ch] = str(c.get_source_chain(unreal.Name(ch)))
    snap["chain_map"] = mapping
    L(f"[STATE] 链映射 {len(mapping)} 条：")
    for k, v in mapping.items():
        L(f"[STATE]   {k:<22} <- {v}")
except Exception as ex:
    LW(f"[STATE] chain map err {ex}")

# 两侧姿态旋转偏移（只记非单位阵）
for path, tag in ((IK_T, "TARGET"), (IK_S, "SOURCE")):
    rig = unreal.load_object(None, path)
    rc = unreal.IKRigController.get_controller(rig)
    bones = set()
    for ch in rc.get_retarget_chains():
        bones.add(str(ch.start_bone))
        bones.add(str(ch.end_bone))
    bones |= {"root", "Root", "pelvis", "Pelvis"}
    offs = {}
    for b in sorted(bones):
        try:
            r = c.get_rotation_offset_for_retarget_pose_bone(unreal.Name(b), unreal.RetargetSourceOrTarget.TARGET if tag == "TARGET" else unreal.RetargetSourceOrTarget.SOURCE).rotator()
            if abs(r.pitch) > 0.01 or abs(r.yaw) > 0.01 or abs(r.roll) > 0.01:
                offs[b] = [round(r.pitch, 3), round(r.yaw, 3), round(r.roll, 3)]
        except Exception:
            pass
    snap[f"{tag}_pose_offsets_nonidentity"] = offs
    L(f"[STATE] {tag} 非单位姿态偏移 {len(offs)} 个：")
    for k, v in offs.items():
        L(f"[STATE]   {tag} {k:<22} {v}")

try:
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, ensure_ascii=False)
    L(f"[STATE] 已写入 {OUT}")
except Exception as ex:
    LW(f"[STATE] write err {ex}")

L("STATE_DUMP_DONE")
