# -*- coding: utf-8 -*-
"""诊断：6 个重定向产物到底有没有动画数据，还是只是预览网格没设。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

TGT = "/Game/Character/Darius/Anims_TP"
SRC = "/Game/Character/Darius/LOL_Source"


def head(tag):
    L("")
    L("################ %s" % tag)


def dump(pkg, bone):
    a = eal.load_asset(pkg)
    name = pkg.split("/")[-1]
    if a is None:
        LW("  %-38s NOT FOUND" % name)
        return
    n = -1
    for prop in ("number_of_frames", "sequence_length", "skeleton",
                 "preview_mesh", "preview_animation", "enable_root_motion"):
        try:
            v = a.get_editor_property(prop)
            if prop == "number_of_frames":
                n = int(v)
            L("  %-38s %-18s = %s" % (name, prop, v))
        except Exception:
            pass
    # 采样同一根骨的不同帧：若三帧完全一样 ⇒ 无动画数据
    for f in (0, max(0, n // 2), max(0, n - 1)):
        for fn in ("get_bone_pose_for_frame", "get_bone_pose_for_frame_no_retarget"):
            fobj = getattr(unreal.AnimationLibrary, fn, None)
            if fobj is None:
                continue
            try:
                t = fobj(a, bone, f, False)
                L("  %-38s f=%-4d [%s] %s" % (name, f, fn, t))
                break
            except Exception as ex:
                L("  %-38s f=%-4d [%s] ERR %s" % (name, f, fn, str(ex)[:90]))
                break


head("目标侧产物（骨骼用 pelvis / head）")
for p in sorted(eal.list_assets(TGT, recursive=False, include_folder=False)):
    dump(str(p).split(".")[0], "pelvis")

L("")
L("目标骨架的预览网格：")
for p in ("/Game/Character/Darius/SK_Darius_GodKing_Skeleton",
          "/Game/Character/Darius/LOL_Source/SK_LOL_Darius_Skeleton"):
    s = eal.load_asset(p)
    if s is None:
        LW("  %s NOT FOUND" % p)
        continue
    for prop in ("preview_skeletal_mesh", "preview_mesh"):
        try:
            L("  %-46s %s = %s" % (p.split("/")[-1], prop, s.get_editor_property(prop)))
        except Exception:
            pass

head("源侧对照（骨骼用 Pelvis）")
dump(SRC + "/SK_LOL_Dariusskinned_mesh_darius_skin15_run", "Pelvis")
dump(SRC + "/SK_LOL_Dariusskinned_mesh_darius_skin15_idle1", "Pelvis")

head("AnimationLibrary 可用函数")
fns = [x for x in dir(unreal.AnimationLibrary) if "bone" in x.lower() or "frame" in x.lower()]
L("  %s" % ", ".join(sorted(fns)))
L("=== DONE ===")
