# -*- coding: utf-8 -*-
"""决定性探针：最外层骨到底有没有「缩放轨道」？
若没有 ⇒ get_bone_pose_for_frame 返回 1.0 只是**测量假象**，
运行时该通道会回落 skeleton reference pose（scale 100），动画其实没问题。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

OUTER = "darius_godking_mesh_LOD0_Skeleton"
NEW = "/Game/Character/Darius/Anims_TP/A_Darius_idle1"
OLD = "/Game/Character/Darius/Anims/A_Darius_Idle1_TP"


def track_info(a, bone):
    """⚠️ data_model_interface.get_bone_track_names() 返回的是**小写名**
    （实测 `camera_cameraSocket` → `camera_camerasocket`），所以一律按小写匹配。"""
    try:
        dm = a.get_editor_property("data_model_interface")
    except Exception as ex:
        return "data_model_interface 取不到: %s" % str(ex)[:60]
    names = []
    try:
        names = [str(x) for x in dm.get_bone_track_names()]
    except Exception:
        pass
    low = {n.lower(): n for n in names}
    real = low.get(bone.lower())
    if real is None:
        return "**无此骨的轨道**（共 %d 条轨道）" % len(names)
    try:
        idx = dm.get_bone_track_index_by_name(real)
    except Exception as ex:
        return "找到轨道名 %s 但取索引失败: %s" % (real, str(ex)[:50])
    try:
        t = dm.get_bone_track_by_index(idx)
    except Exception as ex:
        return "索引 %s 取轨道失败: %s" % (idx, str(ex)[:60])
    out = ["轨道名=%s 索引=%s" % (real, idx)]
    try:
        it = t.get_editor_property("internal_track")
        for f in ("pos_keys", "rot_keys", "scale_keys"):
            try:
                arr = it.get_editor_property(f)
                n = len(arr) if hasattr(arr, "__len__") else "?"
                sample = ""
                if hasattr(arr, "__len__") and n:
                    sample = " 首=%s" % arr[0]
                out.append("%s=%s%s" % (f, n, sample))
            except Exception as ex:
                out.append("%s: %s" % (f, str(ex)[:50]))
    except Exception as ex:
        out.append("internal_track: %s" % str(ex)[:70])
    return " | ".join(out)


L("################ 最外层骨 %s" % OUTER)
for tag, p in (("旧动画", OLD), ("新产物", NEW)):
    a = eal.load_asset(p)
    L("")
    L("  --- %s (%s)" % (tag, p.split("/")[-1]))
    try:
        names = [str(x) for x in a.get_editor_property("data_model_interface").get_bone_track_names()]
        L("      轨道总数 = %d ；含最外层骨 = %s" % (len(names), OUTER in names))
    except Exception as ex:
        LW("      轨道名读取失败: %s" % str(ex)[:80])
    L("      最外层骨：%s" % track_info(a, OUTER))
    L("      pelvis   ：%s" % track_info(a, "pelvis"))
    L("      thigh_l  ：%s" % track_info(a, "thigh_l"))
    try:
        L("      get_bone_pose_for_frame(最外层).scale = %s"
          % AL.get_bone_pose_for_frame(a, OUTER, 0, False).scale3d)
    except Exception as ex:
        LW("      pose 读取失败: %s" % str(ex)[:70])
L("=== DONE ===")
