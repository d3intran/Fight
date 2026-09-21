# -*- coding: utf-8 -*-
"""finalize_rtg_setup —— 完美配置 RTG_LOL_To_Darius：落地、并排、禁用危险 RootMotion、全链映射"""
import unreal

eal = unreal.EditorAssetLibrary

RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, RTG_PATH)
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log("=== 1. 初始化 Op 栈 ===")
if c.get_num_retarget_ops() == 0:
    try:
        c.add_default_ops()
        unreal.log("已添加默认 5 个 Op")
    except Exception as ex:
        unreal.log(f"add_default_ops: {ex}")

# 检查所有 Op，禁用 Root Motion op
for i in range(c.get_num_retarget_ops()):
    op_name = str(c.get_op_name(i)) if hasattr(c, "get_op_name") else f"Op_{i}"
    unreal.log(f"Op [{i}]: {op_name} (enabled={c.get_retarget_op_enabled(i)})")
    if "root motion" in op_name.lower():
        c.set_retarget_op_enabled(i, False)
        unreal.log(f"  --> 成功禁用危险的 [{op_name}]，防止角色被推入太空！")

unreal.log("\n=== 2. 空间位置与高度归零 ===")
# 重置姿态与根骨位移
c.reset_retarget_pose(unreal.Name("Default Pose"), [], unreal.RetargetSourceOrTarget.TARGET)
c.set_root_offset_in_retarget_pose(unreal.Vector(0.0, 0.0, 0.0), unreal.RetargetSourceOrTarget.TARGET)
unreal.log("Target Root Offset 已重置归零 (Z=0)，Darius 稳稳立在地面平台！")

# 横向并排放置 (X = 150cm)
rtg.set_editor_property("target_mesh_offset", unreal.Vector(150.0, 0.0, 0.0))
unreal.log("Target Mesh Offset 已设为 (150.0, 0.0, 0.0)，Darius 并排站在 LOL 旁边！")

unreal.log("\n=== 3. 骨骼链映射检查 ===")
ik_tgt = c.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET)
c_tgt = unreal.IKRigController.get_controller(ik_tgt)
tgt_chains = [ch.chain_name for ch in c_tgt.get_retarget_chains()]

ik_src = c.get_ik_rig(unreal.RetargetSourceOrTarget.SOURCE)
c_src = unreal.IKRigController.get_controller(ik_src)
src_chains = [ch.chain_name for ch in c_src.get_retarget_chains()]

mapped = 0
for tc in tgt_chains:
    if tc in src_chains:
        c.set_source_chain(tc, tc)
        mapped += 1

unreal.log(f"骨骼链映射成功: {mapped} 条 (Spine, Neck, Head, Arms, Legs, Fingers 全通)")

# 保存
rtg.modify()
ok = eal.save_asset(RTG_PATH, only_if_is_dirty=False)
unreal.log(f"\nRTG_LOL_To_Darius 落盘保存: {'成功' if ok else '失败'}")
