# -*- coding: utf-8 -*-
"""重定向产物后处理：删掉最外层骨那条 `scale = 1` 的假轨道。
**必须重启编辑器之后再跑**（原因见下）。

## 它修的是什么
重定向出来的 AnimSequence 比正常动画**多一条轨道**：最外层骨
`darius_godking_mesh_LOD0_Skeleton`，值是 **scale = 1**。

| | 轨道数 | 最外层骨轨道 | `get_bone_pose_for_frame(最外层).scale` |
|---|---|---|---|
| 正常动画（旧一套） | 309 | **没有** ⇒ 回落 reference pose | **100** ✅ |
| 重定向产物 | **310** | **有**，值为 1 | **1** ❌ ⇒ 角色被渲染成 **1.85 cm** |

⇒ Persona 预览和内容浏览器缩略图都看不见角色。

修法：把那条轨道**整条删掉**，让它像正常动画一样回落到 skeleton 的 reference pose。
不写任何数值，所以没有魔数。

## 🔴 三条踩过的坑（都实测过）

1. **必须用 `AnimationDataController.remove_bone_track(bone_name)`**，
   参数是**骨名**（传索引会报 `Failed to convert parameter 'bone_name'`）。
   索引从 `data_model_interface.get_bone_track_names()` 的**位置**取
   （`get_bone_track_index_by_name` 实测恒返回 -1，不可用）。
   ⚠️ 该函数返回的轨道名是**小写**的（`camera_cameraSocket` → `camera_camerasocket`）。

2. **不要用 legacy 的 `AnimationLibrary.remove_bone_animation`** ——
   它会把**整段动画清成静止姿态**（所有骨逐帧四元数相同）。
   我因此作废过两批产物。同样地 `finalize_bone_animation` 也会清空动画。

3. **改完必须同时验两项：scale 与「动画是否还在动」。**
   只量 scale 会漏掉「动画被清空」这种失败 —— 这正是上面那个坑没被当场发现的原因。
   本脚本的做法：**先在 `/Game/Temp` 的副本上验证方法，通过了才动正式资产。**

## 流程
`ik_11` 产出并存盘 → （编辑器可继续用）→ 本脚本。
本脚本自身幂等：副本验证不过就完全不碰正式资产。
"""
import json
import os
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

# 🔁 目标目录可被 Saved/retarget_cycle.json 覆盖（实验回路每轮写新目录）
CFG = "E:/UE/Fight/Saved/retarget_cycle.json"
OUT_DIR = "/Game/Character/Darius/Anims_TP"
if os.path.isfile(CFG):
    try:
        with open(CFG, encoding="utf-8") as fh:
            OUT_DIR = json.load(fh).get("out_dir") or OUT_DIR
    except Exception as ex:
        LW("读 %s 失败: %s" % (CFG, ex))
OUTER = "darius_godking_mesh_LOD0_Skeleton"
TMP = "/Game/Temp/ProbeFix"
L("目标目录 = %s" % OUT_DIR)


def track_names(a):
    try:
        return [str(x) for x in a.get_editor_property("data_model_interface").get_bone_track_names()]
    except Exception as ex:
        LW("  读轨道名失败: %s" % str(ex)[:90])
        return []


def outer_index(a):
    names = track_names(a)
    for i, n in enumerate(names):
        if n.lower() == OUTER.lower():
            return i, names
    return -1, names


def outer_scale(a):
    try:
        return round(AL.get_bone_pose_for_frame(a, OUTER, 0, False).scale3d.x, 3)
    except Exception as ex:
        return "ERR:%s" % str(ex)[:30]


def animating(a, bone="thigh_l", frames=(0, 8, 17, 26, 34)):
    s = set()
    for f in frames:
        try:
            q = AL.get_bone_pose_for_frame(a, bone, f, False).rotation
            s.add((round(q.x, 6), round(q.y, 6), round(q.z, 6), round(q.w, 6)))
        except Exception:
            pass
    return len(s)


def ok_state(a):
    return outer_scale(a) == 100.0 and animating(a) > 1


anims = sorted([str(x).split(".")[0]
                for x in eal.list_assets(OUT_DIR, recursive=False, include_folder=False)])
if not anims:
    LW("!! %s 下没有资产" % OUT_DIR)
    raise SystemExit(1)

# ---------------------------------------------------------------- 1. 副本验方法
L("################ 1. 副本上验证方法")
idx, names = outer_index(eal.load_asset(anims[0]))
L("  轨道总数 = %d ；最外层骨索引 = %s" % (len(names), idx))
if idx < 0 and outer_scale(eal.load_asset(anims[0])) == 100.0:
    L("  副本与正式资产都没有这条轨道 ⇒ 已经修过了，无需处理。")
    L("=== DONE ===")
    raise SystemExit(0)
if idx < 0:
    LW("!! 找不到最外层骨轨道，但 scale 也不是 100，情况未见过，先不动。")
    raise SystemExit(1)

eal.make_directory(TMP)
dup = eal.duplicate_asset(anims[0], TMP + "/probe")
if dup is None:
    LW("!! 副本创建失败，为安全起见不动正式资产。")
    raise SystemExit(1)
before = (outer_scale(dup), animating(dup))
try:
    dup.get_editor_property("controller").remove_bone_track(names[idx])
except Exception as ex:
    LW("!! remove_bone_track 失败: %s" % str(ex)[:130])
    raise SystemExit(1)
after = (outer_scale(dup), animating(dup))
L("  副本：scale %s -> %s ；不同姿态 %d -> %d" % (before[0], after[0], before[1], after[1]))
for x in eal.list_assets(TMP, recursive=True, include_folder=False):
    eal.delete_asset(str(x).split(".")[0])
eal.delete_directory(TMP)
if not (after[0] == 100.0 and after[1] > 1):
    LW("!! 方法未通过（需 scale=100 且 不同姿态>1），不动正式资产。")
    raise SystemExit(1)
L("  副本验证通过。")

# ---------------------------------------------------------------- 2. 施加
L("")
L("################ 2. 施加到正式资产")
allok = True
for p in anims:
    a = eal.load_asset(p)
    nm = p.split("/")[-1]
    i, _ = outer_index(a)
    b = (outer_scale(a), animating(a))
    if i < 0:
        L("  %-34s 本来就没有这条轨道，跳过" % nm)
        continue
    try:
        a.get_editor_property("controller").remove_bone_track(track_names(a)[i])
    except Exception as ex:
        LW("  %-34s remove 失败: %s" % (nm, str(ex)[:90]))
        allok = False
        continue
    f = (outer_scale(a), animating(a))
    good = f[0] == 100.0 and f[1] > 1
    allok = allok and good
    L("  %-34s scale %-7s -> %-7s | 不同姿态 %d -> %d   %s"
      % (nm, b[0], f[0], b[1], f[1], "OK" if good else "!! 异常"))

# ---------------------------------------------------------------- 3. 存盘 + 复核
L("")
L("################ 3. 存盘")
n_saved = 0
for p in anims:
    try:
        if eal.save_asset(p):
            n_saved += 1
    except Exception as ex:
        LW("  save %s 失败: %s" % (p.split("/")[-1], str(ex)[:70]))
L("  存盘 %d / %d" % (n_saved, len(anims)))

L("")
L("################ 4. 复核（scale 与「是否还在动」两项都要过）")
for p in anims:
    a = eal.load_asset(p)
    L("  %-34s scale=%-7s 不同姿态=%d  %s"
      % (p.split("/")[-1], outer_scale(a), animating(a), "OK" if ok_state(a) else "!! 失败"))
if not allok:
    LW("!! 有动画未通过。")
    raise SystemExit(1)
L("=== DONE ===")
