# -*- coding: utf-8 -*-
"""inspect_rtg_offset —— 检查 RTG_LOL_To_Darius 的视口预览偏移与网格位置"""
import unreal

rtg_path = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, rtg_path)
if not rtg:
    unreal.log_error(f"Cannot load {rtg_path}")
    raise SystemExit(1)

unreal.log(f"=== 检查 {rtg.get_name()} ===")
c = unreal.IKRetargeterController.get_controller(rtg)

src_ik = c.get_ik_rig(unreal.RetargetSourceOrTarget.SOURCE)
tgt_ik = c.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET)
unreal.log(f"Source IK: {src_ik.get_path_name() if src_ik else 'None'}")
unreal.log(f"Target IK: {tgt_ik.get_path_name() if tgt_ik else 'None'}")

src_mesh = c.get_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE)
tgt_mesh = c.get_preview_mesh(unreal.RetargetSourceOrTarget.TARGET)
unreal.log(f"Source Preview Mesh: {src_mesh.get_name() if src_mesh else 'None'}")
unreal.log(f"Target Preview Mesh: {tgt_mesh.get_name() if tgt_mesh else 'None'}")

# 检查 Target Mesh Offset
for attr in dir(c):
    if "offset" in attr.lower() or "target" in attr.lower() or "location" in attr.lower():
        unreal.log(f"controller.{attr}")

for attr in dir(rtg):
    if "offset" in attr.lower() or "target" in attr.lower():
        unreal.log(f"rtg.{attr}")

# 检查属性
try:
    off = rtg.get_editor_property("target_mesh_offset")
    unreal.log(f"target_mesh_offset = {off}")
except Exception as ex:
    unreal.log(f"get target_mesh_offset error: {ex}")
