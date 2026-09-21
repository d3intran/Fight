# rtg_63_evidence - 只读：补齐 100 的证据链（rest 真值 / socket / 布料 / 物理资产）
import unreal, json

def L(s): print(f"[EV] {s}")

mesh = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
skel = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")

# 1) Skeleton reference pose（global = 全部都在 mesh 空间）
try:
    ref = skel.get_reference_pose()
    L(f"reference_pose 类型 = {type(ref).__name__} 长度={len(ref) if hasattr(ref,'__len__') else '?'}")
except Exception as ex:
    L(f"get_reference_pose err {ex}")

# 2) 用 AnimationLibrary 读一条动画的最外层骨 + root + pelvis
AL = unreal.AnimationLibrary
anim = unreal.load_asset("/Game/Character/Darius/Animations/LOL_Retarget_Test/A_Darius_run")
if not anim:
    anim = unreal.load_asset("/Game/Character/Darius/Animations/LOL_Retarget/A_Darius_idle1")
L(f"采样动画 = {anim.get_name() if anim else None}")
if anim:
    for b in ("darius_godking_mesh_LOD0_Skeleton", "root", "pelvis", "hand_r", "weapon_jnt"):
        for local in (True, False):
            try:
                t = AL.get_bone_pose_for_frame(anim, unreal.Name(b), 0, local)
                tag = "LOCAL " if local else "COMP  "
                L(f"ANIM {b:<36} {tag} loc=({t.translation.x:10.4f},{t.translation.y:10.4f},{t.translation.z:10.4f}) "
                  f"sc=({t.scale3d.x:.4f},{t.scale3d.y:.4f},{t.scale3d.z:.4f})")
            except Exception as ex:
                L(f"ANIM {b} {'LOCAL' if local else 'COMP'} err {str(ex)[:50]}")

# 3) socket 当前值
try:
    sub = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
    L(f"subsystem = {sub}")
    for m in dir(sub):
        if "socket" in m.lower():
            L(f"  SkeletalMeshEditorSubsystem.{m}")
except Exception as ex:
    L(f"sub err {ex}")

# 4) 布料资产
cape = unreal.load_asset("/Game/Character/Darius/CA_Darius_Cape")
L(f"CA_Darius_Cape -> {cape.get_class().get_name() if cape else 'NOT FOUND'}")
if cape:
    try:
        props = [p for p in dir(cape) if not p.startswith("_")]
        L(f"cloth 资产成员数 = {len(props)}")
        for p in props:
            if any(k in p.lower() for k in ("sim", "param", "solver", "config", "mesh", "space", "scale")):
                L(f"  cloth.{p}")
    except Exception as ex:
        L(f"cloth 属性 err {ex}")

# 5) 物理资产
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for cls in ("PhysicsAsset", "Skeleton", "ChaosClothAsset"):
    f = unreal.ARFilter(package_paths=["/Game/Character/Darius"], recursive_paths=True,
                        class_paths=[unreal.TopLevelAssetPath("/Script/Engine", cls)])
    try:
        L(f"{cls} = {[str(a.asset_name) for a in ar.get_assets(f)]}")
    except Exception as ex:
        L(f"{cls} err {ex}")
L("DONE")
