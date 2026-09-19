# -*- coding: utf-8 -*-
"""诊断 v2：逐个动作真采多帧 + 与旧一套动画做对照，判断「数据空」还是「预览空」。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary


def sample(pkg, bone):
    a = eal.load_asset(pkg)
    name = pkg.split("/")[-1]
    if a is None:
        LW("  %-40s NOT FOUND" % name)
        return
    try:
        n = int(AL.get_num_frames(a))
    except Exception as ex:
        LW("  %-40s get_num_frames 失败: %s" % (name, str(ex)[:80]))
        return
    L("  %-40s 帧数=%d  len=%.4f" % (name, n, a.get_editor_property("sequence_length")))
    prev = None
    moved = 0
    for f in sorted(set([0, max(0, n // 2), max(0, n - 1)])):
        try:
            t = AL.get_bone_pose_for_frame(a, bone, f, False)
        except Exception as ex:
            LW("      f=%-4d 采样失败: %s" % (f, str(ex)[:80]))
            continue
        tr = t.translation
        ro = t.rotation
        key = (round(tr.x, 3), round(tr.y, 3), round(tr.z, 3),
               round(ro.x, 4), round(ro.y, 4), round(ro.z, 4), round(ro.w, 4))
        L("      f=%-4d T=(%8.3f,%8.3f,%8.3f)  Q=(%.4f,%.4f,%.4f,%.4f)"
          % (f, tr.x, tr.y, tr.z, ro.x, ro.y, ro.z, ro.w))
        if prev is not None and key != prev:
            moved += 1
        prev = key
    L("      ⇒ 采样帧之间姿态%s变化" % ("有" if moved else "**无**"))


L("################ A. 本轮重定向前 6 个产物（骨骼 pelvis）")
for p in sorted(eal.list_assets("/Game/Character/Darius/Anims_TP",
                                recursive=False, include_folder=False)):
    sample(str(p).split(".")[0], "pelvis")

L("")
L("################ B. 对照组：上一套 Blender 管线产出的旧动画（骨骼 pelvis）")
for p in sorted(eal.list_assets("/Game/Character/Darius/Anims",
                                recursive=False, include_folder=False)):
    n = str(p).split(".")[0].split("/")[-1]
    if n in ("A_Darius_Run_TP", "A_Darius_Idle1_TP", "A_Darius_RunFast_TP", "BS_Darius_Locomotion"):
        sample(str(p).split(".")[0], "pelvis")

L("")
L("################ C. 源的 run / idle1（骨骼 Pelvis）")
for n in ("run", "idle1"):
    sample("/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_" + n, "Pelvis")

L("")
L("################ D. 骨架的预览网格属性探测")
sk = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
if sk:
    cands = [x for x in dir(sk) if "preview" in x.lower() or "mesh" in x.lower()]
    L("  SK_Darius_GodKing_Skeleton 上可能的属性: %s" % ", ".join(sorted(cands)))
    for prop in cands:
        if "preview" in prop.lower():
            try:
                L("    %s = %s" % (prop, sk.get_editor_property(prop)))
            except Exception as ex:
                L("    %s : %s" % (prop, str(ex)[:90]))
else:
    LW("  骨架没加载到")
L("=== DONE ===")
