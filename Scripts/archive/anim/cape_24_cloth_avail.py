import unreal

SM = "/Game/Character/Darius/SK_Darius_GodKing"
sk = unreal.load_object(None, SM)
AL = unreal.AnimationLibrary

unreal.log("############ 1. 布料相关类型/插件是否可用")
for cls in ("ClothAsset", "SkeletalMeshClothBuildParams", "ClothingSimulationConfig",
            "ClothConfig", "ChaosClothAsset", "ClothSelectionAndDensityModule",
            "ClothAssetEditorSubsystem", "ClothAssetInteropSubsystem", "MeshToMeshBinding",
            "ClothCollisionLandmark", "SkeletalMeshSocket"):
    unreal.log("   unreal.%-32s exists=%s" % (cls, hasattr(unreal, cls)))
sub_names = [m for m in dir(unreal.SkeletalMeshEditorSubsystem) if not m.startswith("_")]
unreal.log("   SkeletalMeshEditorSubsystem: %s" % sub_names)
try:
    ps = unreal.get_editor_subsystem(unreal.EditorSubsystem)
except Exception:
    pass
try:
    plug = unreal.PluginService()
    for pid in ("ChaosCloth", "ChaosClothEditor", "ChaosClothAsset", "ChaosClothAssetEditor",
                "AnimationWarpingRuntime", "ControlRig", "DeformerGraph", "AnimationResourceManager"):
        unreal.log("   plugin %-28s enabled=%s" % (pid, plug.is_plugin_enabled(pid)))
except Exception as ex:
    unreal.log("   PluginService ERR %s" % str(ex)[:60])

unreal.log("############ 2. 网格材质槽 / LOD")
try:
    slots = sk.get_editor_property("skeletal_material_slots")
    for i, s in enumerate(slots):
        unreal.log("   slot %d  name=%s" % (i, s.get_editor_property("material_slot_name")))
except Exception as ex:
    unreal.log("   slots ERR %s" % str(ex)[:60])
for pr in ("lod_num", "materials", "render_data", "bounds_preview"):
    try:
        unreal.log("   %-14s = %s" % (pr, str(sk.get_editor_property(pr))[:120]))
    except Exception:
        pass

unreal.log("############ 3. 现役动画里披风骨轨道 + 是否逐帧变化")
ANIMS = ["/Game/Character/Darius/Anims/A_Darius_Walk_Layered",
         "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"]
for ap in ANIMS:
    a = unreal.load_object(None, ap)
    if not a:
        unreal.log("   %s 载入失败" % ap.split("/")[-1])
        continue
    try:
        names = [str(x) for x in a.controller.get_model_interface().get_bone_track_names()]
    except Exception as ex:
        unreal.log("   track ERR %s" % str(ex)[:60])
        continue
    cape = [x for x in names if "cape" in x.lower()]
    nf = int(AL.get_num_frames(a))
    unreal.log("   %-28s 轨道=%d 披风轨道=%d 帧=%d" % (ap.split("/")[-1], len(names), len(cape), nf))
    if cape:
        objs = [unreal.Name(x) for x in cape]
        p0 = AL.get_bone_poses_for_frame(a, objs, 0, False)
        pm = AL.get_bone_poses_for_frame(a, objs, max(1, nf // 2), False)
        for i, bn in enumerate(cape[:5]):
            d = sum((p0[i].translation[j] - pm[i].translation[j]) ** 2 for j in range(3)) ** 0.5
            rq0 = p0[i].rotation
            rqm = pm[i].rotation
            dot = abs(rq0.x * rqm.x + rq0.y * rqm.y + rq0.z * rqm.z + rq0.w * rqm.w)
            ang = unreal.MathLibrary.radians_to_degrees(2 * (1 - dot) ** 0.5) if dot < 1 else 0.0
            unreal.log("      %-20s f0→mid 位移 %.4f  旋转差约 %.2f 度  loc0=%s" % (
                bn, d, ang, [round(v, 2) for v in (p0[i].translation.x, p0[i].translation.y, p0[i].translation.z)]))
unreal.log("############ 4. 披风链挂点")
skel = sk.get_editor_property("skeleton")
for b in ("cape_chain_01_l", "cape_chain_01_m", "cape_chain_01_r"):
    try:
        unreal.log("   %-16s <- %s" % (b, unreal.SkeletonLibrary.find_bone_path_to_root(skel, b)))
    except Exception as ex:
        unreal.log("   %-16s ERR %s" % (b, str(ex)[:50]))
unreal.log("############ DONE")
