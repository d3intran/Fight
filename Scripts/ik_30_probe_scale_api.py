# -*- coding: utf-8 -*-
"""探针：找出「给 AnimSequence 的某根骨写入缩放轨道」的可用接口。
在 /Game/Temp 下的副本上做实验，不碰正式资产。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

SRC = "/Game/Character/Darius/Anims_TP/A_Darius_idle1"
TMPDIR = "/Game/Temp/ScaleProbe"
OUTER = "darius_godking_mesh_LOD0_Skeleton"

L("################ 1. 相关类名")
for kw in ("AnimationData", "AnimData", "AnimSequence", "RawAnimation"):
    L("  %-16s : %s" % (kw, ", ".join(sorted([x for x in dir(unreal) if kw in x]))[:400]))

a = eal.load_asset(SRC)
L("")
L("################ 2. AnimSequence 上的数据相关成员")
L("  %s" % ", ".join(sorted([x for x in dir(a)
                            if any(k in x.lower() for k in ("data", "model", "track", "controller", "curve"))])))

L("")
L("################ 3. 各候选属性")
for prop in ("data_model", "raw_animation_data", "compressed_data", "compressed_curve_data"):
    try:
        v = a.get_editor_property(prop)
        L("  %-24s -> %s" % (prop, type(v)))
        if v is not None:
            L("      attrs: %s" % ", ".join(sorted([x for x in dir(v) if not x.startswith("_")]))[:500])
    except Exception as ex:
        L("  %-24s : %s" % (prop, str(ex)[:110]))

L("")
L("################ 4. 现有轨道里有没有最外层骨")
try:
    dm = a.get_editor_property("data_model")
    for fn in ("get_bone_track_names", "get_bone_tracks", "get_num_bone_tracks"):
        f = getattr(dm, fn, None)
        if f is None:
            continue
        try:
            r = f()
            L("  data_model.%s() -> %s" % (fn, (list(r)[:8] if hasattr(r, "__len__") else r)))
        except Exception as ex:
            L("  data_model.%s() : %s" % (fn, str(ex)[:90]))
except Exception as ex:
    LW("  data_model 不可用: %s" % str(ex)[:110])

L("")
L("################ 5. 复制一份做实验")
if not eal.does_directory_exist(TMPDIR):
    L("  make_directory -> %s" % eal.make_directory(TMPDIR))
dup = eal.duplicate_asset(SRC, TMPDIR + "/A_Darius_idle1_copy")
L("  duplicate -> %s" % (dup.get_name() if dup else "失败"))


def outer_scale(x):
    try:
        return AL.get_bone_pose_for_frame(x, OUTER, 0, False).scale3d.x
    except Exception as ex:
        return "ERR:%s" % str(ex)[:50]


if dup is not None:
    L("  复制件 outer scale = %s" % outer_scale(dup))

    L("")
    L("  --- 试 A：remove_bone_animation（删掉该骨轨道，看是否回落到 reference pose）")
    try:
        AL.remove_bone_animation(dup, OUTER)
        L("      remove_bone_animation OK -> outer scale = %s" % outer_scale(dup))
    except Exception as ex:
        LW("      remove 失败: %s" % str(ex)[:110])

    L("")
    L("  --- 试 B：AnimationLibrary 其它可写接口")
    L("      %s" % ", ".join(sorted([x for x in dir(AL) if not x.startswith("_")])))
L("=== DONE ===")
