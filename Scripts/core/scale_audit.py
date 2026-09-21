# -*- coding: utf-8 -*-
"""scale 契约门禁 —— 只读扫描，不改动任何资产。

背景见 Scripts/core/fight_scale（骨架最外层骨承载唯一的 100x 缩放）。
本门禁检查三件事：

  1. 每条目标骨架动画的最外层骨缩放是否合规
     - 没有该骨轨道  -> 回落到 reference pose(100)，合规
     - 有该骨轨道且值 = 100  -> 合规（保留了显式轨道，但值对）
     - 有该骨轨道且值 != 100 -> 违规（重定向写的假轨道，会让角色缩成 1.85cm）
  2. 网格 socket 的相对缩放是否 = 0.01
  3. 角色蓝图里战斧组件的相对缩放

附带「动画活性」检查：多骨 x 按真实帧长采样，看跨帧最大旋转差（度）。
低于 0.5 度判定为「疑似被清成静止」并计为违规；0.5-3 度是低动态（idle 属正常）。

输出以 `VERDICT: PASS` / `VERDICT: FAIL` 结尾，便于流水线判定。
常量一律取自 Scripts/core/fight_scale，禁止在此重复魔数。
"""

import math
import sys
import unreal

_CORE = "E:/UE/Fight/Scripts/core"
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)
import fight_scale as FS

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

CHAR_DIR = "/Game/Character/Darius"
TGT_SKEL = "SK_Darius_GodKing_Skeleton"
MESH_PATH = "/Game/Character/Darius/SK_Darius_GodKing"
BP_PATH = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
KNOWN_SOCKETS = ("hand_rSocket",)
MOTION_BONES = ("pelvis", "spine_01", "thigh_l", "hand_r")
MOTION_DEAD_DEG = 0.5
MOTION_LOW_DEG = 3.0

L("[SA] ===== scale 契约门禁 =====")
L(f"[SA] 期望：最外层骨 {FS.OUTER_BONE} 无轨道或 = {FS.OUTER_SCALE}；"
  f"socket 相对缩放 = {FS.SOCKET_SCALE}")


def track_names(a):
    try:
        return [str(x) for x in a.get_editor_property("data_model_interface").get_bone_track_names()]
    except Exception as ex:
        LW(f"[SA]   读轨道名失败 {str(ex)[:80]}")
        return []


def find_outer_track(a):
    for n in track_names(a):
        if FS.OUTER_BONE.lower() in n.lower():
            return n
    return None


def read_scale(a, bone):
    try:
        return round(AL.get_bone_pose_for_frame(a, unreal.Name(bone), 0, False).scale3d.x, 4)
    except Exception as ex:
        return f"ERR:{str(ex)[:26]}"


def motion_deg(a, n=7):
    """跨帧最大旋转差（度）——多骨取最大，帧号按动画真实长度铺开。"""
    try:
        keys = int(a.get_editor_property("number_of_sampled_keys"))
    except Exception:
        keys = 1
    if keys < 2:
        return 0.0
    frames = sorted(set(int(round(i * (keys - 1) / (n - 1))) for i in range(n)))
    worst = 0.0
    for b in MOTION_BONES:
        qs = []
        for f in frames:
            try:
                qs.append(AL.get_bone_pose_for_frame(a, unreal.Name(b), f, False).rotation)
            except Exception:
                pass
        if len(qs) < 2:
            continue
        b = qs[0]
        for q in qs[1:]:
            d = b.x * q.x + b.y * q.y + b.z * q.z + b.w * q.w
            d = min(1.0, max(-1.0, abs(d)))
            worst = max(worst, math.degrees(2.0 * math.acos(d)))
    return round(worst, 2)


ar = unreal.AssetRegistryHelpers.get_asset_registry()
filt = unreal.ARFilter(package_paths=[CHAR_DIR], recursive_paths=True,
                       class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence")])
paths = sorted(str(a.package_name) for a in ar.get_assets(filt))

violations = []
checked = 0
skipped_src = 0
low_motion = []

L(f"[SA] --- 动画扫描（{len(paths)} 条候选） ---")
for p in paths:
    a = eal.load_asset(p)
    if a is None:
        LW(f"[SA]   载入失败 {p}")
        continue
    nm = p.split("/")[-1]
    try:
        sk = a.get_editor_property("skeleton")
        skn = sk.get_name() if sk else ""
    except Exception:
        skn = ""
    if skn != TGT_SKEL:
        skipped_src += 1
        continue

    checked += 1
    tr = find_outer_track(a)
    if tr is None:
        sc = read_scale(a, FS.OUTER_BONE)
        ok = FS.outer_scale_ok(sc) if isinstance(sc, float) else False
        note = f"无轨道，回落 {sc}"
    else:
        sc = read_scale(a, tr)
        ok = FS.outer_scale_ok(sc) if isinstance(sc, float) else False
        note = f"轨道值 {sc}"
    mo = motion_deg(a)
    flag = "OK" if ok else "!! FAIL"
    if not ok:
        violations.append((nm, f"最外层骨 {note}"))
    if mo < MOTION_DEAD_DEG:
        L(f"[SA]   {nm:<36} {note:<22} 动态 {mo:>6.2f}度  {flag}  !! 疑似静止")
        violations.append((nm, f"疑似被清成静止（{mo}度）"))
    elif mo < MOTION_LOW_DEG:
        L(f"[SA]   {nm:<36} {note:<22} 动态 {mo:>6.2f}度  {flag}  (低动态，idle 正常)")
        low_motion.append(nm)
    else:
        L(f"[SA]   {nm:<36} {note:<22} 动态 {mo:>6.2f}度  {flag}")

L(f"[SA] 目标骨架动画 {checked} 条；跳过源骨架 {skipped_src} 条；低动态 {len(low_motion)} 条")

L("[SA] --- socket 扫描 ---")
mesh = eal.load_asset(MESH_PATH)
if mesh is None:
    LW(f"[SA] !! 网格载入失败 {MESH_PATH}")
else:
    for sn in KNOWN_SOCKETS:
        try:
            s = mesh.find_socket(unreal.Name(sn))
        except Exception as ex:
            LW(f"[SA]   find_socket({sn}) 失败 {str(ex)[:60]}")
            continue
        if s is None:
            L(f"[SA]   {sn:<24} 不存在")
            continue
        sc = s.get_editor_property("relative_scale")
        ok = FS.socket_scale_ok(sc.x) and FS.socket_scale_ok(sc.y) and FS.socket_scale_ok(sc.z)
        L(f"[SA]   {sn:<24} relative_scale=({sc.x:.4f},{sc.y:.4f},{sc.z:.4f})  "
          f"{'OK' if ok else '!! FAIL'}")
        if not ok:
            violations.append((f"socket {sn}", f"scale=({sc.x:.4f},{sc.y:.4f},{sc.z:.4f})"))

L("[SA] --- 蓝图组件扫描 ---")
L("[SA]   未覆盖：Blueprint 的 SCS 节点不从 Python 暴露。")
L("[SA]   战斧的实际载体是 socket（见上）；组件相对变换的手工记录在 AGENTS.md 2.2。")

L("[SA] --- 汇总 ---")
if violations:
    L(f"[SA] 违规 {len(violations)} 项：")
    for nm, why in violations:
        L(f"[SA]     {nm:<36} {why}")
    L(f"[SA] VERDICT: FAIL  （检查动画 {checked} 条，违规 {len(violations)} 项）")
else:
    L(f"[SA] VERDICT: PASS  （全部合规，检查动画 {checked} 条）")
L("[SA] DONE")
