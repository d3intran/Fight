# -*- coding: utf-8 -*-
"""rtg_41_fix_outer_scale —— 重定向产物后处理：删掉最外层骨那条 `scale = 1` 的假轨道。

原理与踩坑完全沿用工程既有方案（脚本库里的 ik_31）：重定向产物有 310 轨，最外层骨
`darius_godking_mesh_LOD0_Skeleton` 被写了 scale = 1 ⇒ 角色被渲染成 1.85cm、披风被撑爆。
正常动画只有 309 轨、该骨回落 reference pose（scale = 100）。修法 = 整条轨道删掉，不写任何魔数。

三条铁律（已实测）：
1. 必须 `anim.get_editor_property("controller").remove_bone_track(骨名)`，参数是**骨名**；
   索引从 `data_model_interface.get_bone_track_names()` 的**位置**取。
2. 严禁 legacy 的 `AnimationLibrary.remove_bone_animation`（会把整段动画清成静止）。
3. 改完必须**同时**验 scale 与「动画是否还在动」；先在 /Game/Temp 副本上验方法。

目标目录读 `Saved/Attack/rtg_scale_fix_dir.txt`（缺省用测试目录）。
"""

import os
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

DIR_FILE = "E:/UE/Fight/Saved/Attack/rtg_scale_fix_dir.txt"
OUT_DIR = "/Game/Character/Darius/Animations/LOL_Retarget_Test"
TMP = "/Game/Temp/ScaleFixProbe"
NAME_HINT = "lod0_skeleton"

if os.path.isfile(DIR_FILE):
    try:
        with open(DIR_FILE, encoding="utf-8") as fh:
            v = fh.read().strip()
            if v:
                OUT_DIR = v
    except Exception as ex:
        LW(f"读 {DIR_FILE} 失败: {ex}")
L(f"[SCALE] 目标目录 = {OUT_DIR}")


def track_names(a):
    try:
        return [str(x) for x in a.get_editor_property("data_model_interface").get_bone_track_names()]
    except Exception as ex:
        LW(f"  读轨道名失败: {str(ex)[:90]}")
        return []


_RESOLVED_OUTER = None


def outer_index(a):
    global _RESOLVED_OUTER
    names = track_names(a)
    for i, n in enumerate(names):
        if NAME_HINT in n.lower():
            _RESOLVED_OUTER = n
            return i, names
    return -1, names


def outer_scale(a, name=None):
    """删轨前后都能量：删完用骨名直接取，应回落 reference pose（100）"""
    try:
        n = name or _RESOLVED_OUTER
        if n is None:
            i, names = outer_index(a)
            if i < 0:
                return "NO_TRACK"
            n = names[i]
        return round(AL.get_bone_pose_for_frame(a, unreal.Name(n), 0, False).scale3d.x, 3)
    except Exception as ex:
        return f"ERR:{str(ex)[:30]}"


def animating(a, bone="thigh_l", frames=(0, 8, 17, 26, 34)):
    s = set()
    for f in frames:
        try:
            q = AL.get_bone_pose_for_frame(a, bone, f, False).rotation
            s.add((round(q.x, 6), round(q.y, 6), round(q.z, 6), round(q.w, 6)))
        except Exception:
            pass
    return len(s)


anims = sorted(str(x).split(".")[0] for x in eal.list_assets(OUT_DIR, recursive=False, include_folder=False))
if not anims:
    LW(f"!! {OUT_DIR} 下没有资产")
    raise SystemExit(1)
L(f"[SCALE] 待处理 {len(anims)} 个资产：{[p.split('/')[-1] for p in anims]}")

first = eal.load_asset(anims[0])
idx, names = outer_index(first)
L(f"[SCALE] 轨道总数 = {len(names)}；最外层骨索引 = {idx}；该骨 scale = {outer_scale(first)}")
if idx < 0:
    L("[SCALE] 找不到最外层骨轨道 ⇒ 已修过（或不是重定向产物），无需处理。")
    L("SCALE_FIX_DONE")
    raise SystemExit(0)

# ---------------------------------------------------------------- 1. 副本验方法
eal.make_directory(TMP)
dup = eal.duplicate_asset(anims[0], TMP + "/probe")
if dup is None:
    LW("!! 副本创建失败，为安全起见不动正式资产。")
    raise SystemExit(1)
before = (outer_scale(dup), animating(dup))
try:
    dup.get_editor_property("controller").remove_bone_track(track_names(dup)[idx])
except Exception as ex:
    LW(f"!! remove_bone_track 失败: {str(ex)[:130]}")
    raise SystemExit(1)
after = (outer_scale(dup), animating(dup))
L(f"[SCALE] 副本验证：scale {before[0]} -> {after[0]}；不同姿态 {before[1]} -> {after[1]}")
for x in eal.list_assets(TMP, recursive=True, include_folder=False):
    eal.delete_asset(str(x).split(".")[0])
eal.delete_directory(TMP)
if not (after[0] == 100.0 and after[1] > 1):
    LW("!! 方法未通过（需 scale=100 且 不同姿态>1），不动正式资产。")
    raise SystemExit(1)
L("[SCALE] 副本验证通过。")

# ---------------------------------------------------------------- 2. 施加
allok = True
for p in anims:
    a = eal.load_asset(p)
    nm = p.split("/")[-1]
    i, _ = outer_index(a)
    b = (outer_scale(a), animating(a))
    if i < 0:
        L(f"[SCALE]   {nm:<34} 没有该轨道，跳过（scale={b[0]}）")
        continue
    try:
        a.get_editor_property("controller").remove_bone_track(track_names(a)[i])
    except Exception as ex:
        LW(f"[SCALE]   {nm:<34} remove 失败: {str(ex)[:90]}")
        allok = False
        continue
    f = (outer_scale(a), animating(a))
    good = f[0] == 100.0 and f[1] > 1
    allok = allok and good
    L(f"[SCALE]   {nm:<34} scale {b[0]} -> {f[0]} | 不同姿态 {b[1]} -> {f[1]}   {'OK' if good else '!! 异常'}")

# ---------------------------------------------------------------- 3. 存盘 + 复核
n = 0
for p in anims:
    try:
        if eal.save_asset(p):
            n += 1
    except Exception as ex:
        LW(f"[SCALE]   save {p.split('/')[-1]} 失败: {str(ex)[:70]}")
L(f"[SCALE] 存盘 {n}/{len(anims)}")
for p in anims:
    a = eal.load_asset(p)
    sc = outer_scale(a)
    am = animating(a)
    L(f"[SCALE] 复核 {p.split('/')[-1]:<34} scale={sc:<8} 不同姿态={am}  {'OK' if (sc == 100.0 and am > 1) else '!! 失败'}")
if not allok:
    LW("!! 有动画未通过。")
    raise SystemExit(1)
L("SCALE_FIX_DONE")
