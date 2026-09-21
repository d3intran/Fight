# -*- coding: utf-8 -*-
"""rtg_05_diag_state —— 只读诊断：RTG 两侧 rig / 预览网格 / 重定向姿态偏移 / 关卡 Actor"""

import unreal

L = unreal.log
LW = unreal.log_warning

RTG = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
IK_T = "/Game/Character/Darius/IK/IK_Darius"
IK_S = "/Game/Character/Darius/IK/IK_LOL_Darius"
TGT_MESH = "/Game/Character/Darius/SK_Darius_GodKing"

def in_pie():
    for mod, cls, fn in ((unreal, unreal.LevelEditorSubsystem, "is_in_play_in_editor"),
                         (unreal, unreal.LevelEditorSubsystem, "is_play_in_editor"),
                         (unreal, unreal.EditorLevelLibrary, "is_in_play_in_editor")):
        f = getattr(cls, fn, None)
        if f is None:
            continue
        try:
            return f() if cls is unreal.EditorLevelLibrary else unreal.get_editor_subsystem(cls).__getattribute__(fn)()
        except Exception:
            pass
    try:
        return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None
    except Exception as ex:
        return f"unknown ({ex})"


L(f"[DIAG] PIE running = {in_pie()}")
L(f"[DIAG] LevelEditorSubsystem api = {[m for m in dir(unreal.LevelEditorSubsystem) if 'play' in m.lower()]}")

# ---------------------------------------------------------------- 关卡 Actor 盘点
try:
    subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subs.get_all_level_actors()
    L(f"[DIAG] level actors = {len(actors)}")
    for a in actors:
        L(f"[DIAG]    - {a.get_name()}  [{a.get_class().get_name()}]")
except Exception as ex:
    LW(f"[DIAG] actor list err {ex}")

# ---------------------------------------------------------------- RTG 两侧 rig 指针
rtg = unreal.load_object(None, RTG)
c = unreal.IKRetargeterController.get_controller(rtg)

for side, tag in ((unreal.RetargetSourceOrTarget.TARGET, "TARGET"), (unreal.RetargetSourceOrTarget.SOURCE, "SOURCE")):
    fn = getattr(c, "get_ik_rig", None)
    if fn is None:
        L(f"[DIAG] {tag} get_ik_rig 不存在")
        continue
    try:
        rig = fn(side)
        L(f"[DIAG] {tag} rig = {rig.get_path_name() if rig else None}")
    except Exception as ex:
        LW(f"[DIAG] {tag} get_ik_rig err {ex}")

for side, tag in ((unreal.RetargetSourceOrTarget.TARGET, "TARGET"), (unreal.RetargetSourceOrTarget.SOURCE, "SOURCE")):
    try:
        L(f"[DIAG] {tag} current retarget pose = {c.get_current_retarget_pose_name(side)}")
    except Exception as ex:
        LW(f"[DIAG] {tag} pose name err {ex}")
    try:
        poses = c.get_retarget_poses(side)
        L(f"[DIAG] {tag} poses = {[str(p) for p in poses]}")
    except Exception as ex:
        LW(f"[DIAG] {tag} poses err {ex}")
    try:
        off = c.get_root_offset_in_retarget_pose(side)
        L(f"[DIAG] {tag} root offset = ({off.x:.3f}, {off.y:.3f}, {off.z:.3f})")
    except Exception as ex:
        LW(f"[DIAG] {tag} root offset err {ex}")

# ---------------------------------------------------------------- 两侧 rig 的网格绑定
for path in (IK_T, IK_S):
    rig = unreal.load_object(None, path)
    if not rig:
        LW(f"[DIAG] {path} 不存在")
        continue
    rc = unreal.IKRigController.get_controller(rig)
    gm = None
    used = None
    for fname in ("get_skeletal_mesh", "get_preview_mesh", "get_skeletal_mesh_asset"):
        fn = getattr(rc, fname, None)
        if fn is None:
            continue
        try:
            gm = fn()
            used = fname
            break
        except Exception as ex:
            LW(f"[DIAG] {fname} err {ex}")
    L(f"[DIAG] {path}")
    L(f"[DIAG]    mesh={gm.get_path_name() if gm else None}   (via {used})")
    try:
        L(f"[DIAG]    retarget_root = {rc.get_retarget_root()}")
    except Exception as ex:
        LW(f"[DIAG]    root err {ex}")
    try:
        L(f"[DIAG]    chains = {len(rc.get_retarget_chains())}")
    except Exception as ex:
        LW(f"[DIAG]    chains err {ex}")
    L(f"[DIAG]    mesh-ish api = {[m for m in dir(rc) if 'mesh' in m.lower() or 'preview' in m.lower()]}")

# ---------------------------------------------------------------- 重定向姿态逐骨偏移
TGT_BONES = ("pelvis", "thigh_l", "thigh_r", "foot_l", "foot_r", "upperarm_l", "upperarm_r", "spine_01", "weapon_jnt")
SRC_BONES = ("Pelvis", "L_Hip", "R_Hip", "L_Foot", "R_Foot", "L_Shoulder", "R_Shoulder", "Spine1", "Weapon")

for bones, side, tag in ((TGT_BONES, unreal.RetargetSourceOrTarget.TARGET, "TGT"),
                         (SRC_BONES, unreal.RetargetSourceOrTarget.SOURCE, "SRC")):
    L(f"[DIAG] --- {tag} retarget pose rotation offsets ---")
    for b in bones:
        try:
            q = c.get_rotation_offset_for_retarget_pose_bone(unreal.Name(b), side)
            r = q.rotator()
            L(f"[DIAG]   {tag} {b:<12} off=(p {r.pitch:8.2f}, y {r.yaw:8.2f}, r {r.roll:8.2f})")
        except Exception as ex:
            LW(f"[DIAG]   {tag} {b} err {ex}")

# ---------------------------------------------------------------- 目标网格包围盒
mesh = unreal.load_object(None, TGT_MESH)
if mesh:
    b = mesh.get_bounds()
    L(f"[DIAG] TGT mesh extent = ({b.box_extent.x:.1f}, {b.box_extent.y:.1f}, {b.box_extent.z:.1f})  r={b.sphere_radius:.1f}")
    try:
        L(f"[DIAG] TGT mesh import_scale-ish: {[m for m in dir(mesh) if 'scale' in m.lower()][:12]}")
    except Exception:
        pass

# ---------------------------------------------------------------- RTG 可用的 预览/显示 相关 API
L(f"[DIAG] rtg props(mesh/preview/show/display) = {[n for n in dir(rtg) if any(k in n.lower() for k in ('mesh', 'preview', 'show', 'display', 'view'))]}")
L(f"[DIAG] ctrl props(mesh/preview/show/display) = {[n for n in dir(c) if any(k in n.lower() for k in ('mesh', 'preview', 'show', 'display', 'view'))]}")
L("RTG_DIAG_DONE")
