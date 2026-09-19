# -*- coding: utf-8 -*-
"""直接量最外层骨/root/pelvis 的局部变换（含 scale），对比 rest / 旧动画 / 新动画。
用来判断组件空间那个 100 倍差异是真问题还是测量假象。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

OUTER = {"target": "darius_godking_mesh_LOD0_Skeleton", "source": "skinned_mesh"}


def show(tag, t):
    tr, ro, sc = t.translation, t.rotation, t.scale3d
    L("    %-34s T=(%9.4f,%9.4f,%9.4f)  S=(%8.3f,%8.3f,%8.3f)"
      % (tag, tr.x, tr.y, tr.z, sc.x, sc.y, sc.z))


L("################ A. 骨架 rest pose（真值）")
sk = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
rp = sk.get_reference_pose()
for b in (OUTER["target"], "root", "pelvis"):
    try:
        show("rest " + b, rp.get_bone_pose(b, unreal.AnimPoseSpaces.LOCAL))
    except Exception as ex:
        LW("    rest %s 失败: %s" % (b, str(ex)[:70]))

L("")
L("################ B. 旧动画 A_Darius_Idle1_TP（在 Persona 里能正常显示的那套）")
a = eal.load_asset("/Game/Character/Darius/Anims/A_Darius_Idle1_TP")
for b in (OUTER["target"], "root", "pelvis"):
    try:
        show("old  " + b, AL.get_bone_pose_for_frame(a, b, 0, False))
    except Exception as ex:
        LW("    old %s 失败: %s" % (b, str(ex)[:70]))

L("")
L("################ C. 新产物 A_Darius_idle1")
a2 = eal.load_asset("/Game/Character/Darius/Anims_TP/A_Darius_idle1")
for b in (OUTER["target"], "root", "pelvis"):
    try:
        show("new  " + b, AL.get_bone_pose_for_frame(a2, b, 0, False))
    except Exception as ex:
        LW("    new %s 失败: %s" % (b, str(ex)[:70]))

L("")
L("################ D. 源骨架 rest + 源动画（对照源侧是否也这样）")
ssk = eal.load_asset("/Game/Character/Darius/LOL_Source/SK_LOL_Darius_Skeleton")
srp = ssk.get_reference_pose()
for b in (OUTER["source"], "Root", "Pelvis"):
    try:
        show("src rest " + b, srp.get_bone_pose(b, unreal.AnimPoseSpaces.LOCAL))
    except Exception as ex:
        LW("    src rest %s 失败: %s" % (b, str(ex)[:70]))
sa = eal.load_asset("/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_run")
for b in (OUTER["source"], "Root", "Pelvis"):
    try:
        show("src anim " + b, AL.get_bone_pose_for_frame(sa, b, 0, False))
    except Exception as ex:
        LW("    src anim %s 失败: %s" % (b, str(ex)[:70]))
L("=== DONE ===")
