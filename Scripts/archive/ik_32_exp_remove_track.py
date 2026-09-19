# -*- coding: utf-8 -*-
"""带对照组的实验：查清 (1) 我的「动画是否在动」检查本身可不可靠
(2) 最外层骨到底有没有动画轨道 (3) remove_bone_animation 是否会连带毁掉动画。
全部在 /Game/Temp/ScaleProbe 的副本上做，不碰正式资产。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

TMP = "/Game/Temp/ScaleProbe"
OLD = "/Game/Character/Darius/Anims/A_Darius_Idle1_TP"
NEW = "/Game/Character/Darius/Anims_TP/A_Darius_idle1"
OUTER = "darius_godking_mesh_LOD0_Skeleton"


def quats(a, bone, frames=(0, 8, 17, 26, 34)):
    out = []
    for f in frames:
        try:
            q = AL.get_bone_pose_for_frame(a, bone, f, False).rotation
            out.append((round(q.x, 6), round(q.y, 6), round(q.z, 6), round(q.w, 6)))
        except Exception:
            out.append(None)
    return out


def uniq(a, bone):
    return len(set(quats(a, bone)))


def outer_scale(a):
    try:
        return round(AL.get_bone_pose_for_frame(a, OUTER, 0, False).scale3d.x, 3)
    except Exception as ex:
        return "ERR:%s" % str(ex)[:30]


def report(tag, a):
    L("  %-26s thigh_l 不同姿态=%d   calf_l=%d   最外层 scale=%s"
      % (tag, uniq(a, "thigh_l"), uniq(a, "calf_l"), outer_scale(a)))


L("################ 1. 先验一下我的检查本身靠不靠谱")
old = eal.load_asset(OLD)
new = eal.load_asset(NEW)
report("旧动画 A_Darius_Idle1_TP", old)
report("新产物 A_Darius_idle1", new)
L("  ⇒ 若旧动画也是 1，说明检查方式本身失效；若旧动画 >1，说明新产物真的静止。")

L("")
L("################ 2. 轨道清单（新产物 vs 旧动画）")
for tag, a in (("新产物", new), ("旧动画", old)):
    L("  --- %s" % tag)
    for prop in ("controller", "data_model", "data_model_interface"):
        try:
            v = getattr(a, prop, None)
            L("      %-20s -> %s" % (prop, type(v)))
            if v is not None:
                fns = [x for x in dir(v) if "bone" in x.lower() or "track" in x.lower()]
                L("      接口: %s" % ", ".join(sorted(fns))[:400])
                for fn in ("get_bone_track_names", "get_bone_tracks", "get_num_bone_tracks"):
                    f = getattr(v, fn, None)
                    if f is None:
                        continue
                    try:
                        r = f()
                        names = [str(x) for x in r] if hasattr(r, "__len__") else [r]
                        L("      %s() -> %d 条；含最外层骨 = %s"
                          % (fn, len(names), OUTER in names))
                        if fn.endswith("names") and len(names) > 40:
                            L("         前 5 条: %s" % names[:5])
                    except Exception as ex:
                        L("      %s() : %s" % (fn, str(ex)[:80]))
        except Exception as ex:
            L("      %-20s : %s" % (prop, str(ex)[:90]))

L("")
L("################ 3. 对照组实验：在副本上删最外层骨轨道")
if not eal.does_directory_exist(TMP):
    L("  make_directory -> %s" % eal.make_directory(TMP))
base = eal.duplicate_asset(OLD, TMP + "/ctl_base")
ctl = eal.duplicate_asset(OLD, TMP + "/ctl_untouched")
rm = eal.duplicate_asset(OLD, TMP + "/ctl_remove")
L("  三个副本：ctl_untouched（对照）/ ctl_remove（删最外层骨轨道）/ base（对照原样）")
report("ctl_untouched（对照）", ctl)
try:
    AL.remove_bone_animation(rm, OUTER)
    L("  remove_bone_animation 已执行")
except Exception as ex:
    LW("  remove 失败: %s" % str(ex)[:100])
report("ctl_remove（删轨道后）", rm)
L("")
L("  判定：若 ctl_remove 的 thigh_l 变成 1 而 ctl_untouched >1 ⇒ remove 会连带毁掉动画。")
L("=== DONE ===")
