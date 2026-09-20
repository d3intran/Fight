import unreal

PA = "/Game/Character/Darius/SK_Darius_GodKing_Physics"
ABP = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"


def LO(p):
    try:
        return unreal.load_object(None, p)
    except Exception:
        return None


unreal.log("############ 1. PhysicsAsset 可用 API")
unreal.log("%s" % [m for m in dir(unreal.PhysicsAsset) if not m.startswith("_")])
unreal.log("############ 2. SkeletalBodySetup 可用 API")
try:
    unreal.log("%s" % [m for m in dir(unreal.SkeletalBodySetup) if not m.startswith("_")])
except Exception as ex:
    unreal.log("   ERR %s" % ex)
unreal.log("############ 3. PhysicsAssetEditor / 子系统")
for n in ("PhysicsAssetEditorLibrary", "PhysicsAssetEditorSubsystem", "SkeletalMeshEditorSubsystem",
          "PhysicsAssetEditor"):
    unreal.log("   %-34s exists=%s" % (n, hasattr(unreal, n)))

pa = LO(PA)
unreal.log("############ 4. 现有物理资产内容")
unreal.log("   pa = %s" % pa)
if pa:
    for prop in ("skeletal_body_setups", "constraint_setup", "collision_disabled_bodies",
                 "preview_scale", "skeletal_mesh", "bounds_bodies"):
        try:
            v = pa.get_editor_property(prop)
            unreal.log("   %-26s = %s" % (prop, v if not hasattr(v, "__len__") else "len=%d" % len(v)))
        except Exception as ex:
            unreal.log("   %-26s ERR %s" % (prop, str(ex)[:70]))
    for m in ("get_body_names", "find_body", "get_constraint_names", "find_constraint"):
        f = getattr(pa, m, None)
        if f:
            try:
                unreal.log("   %s() -> %s" % (m, f()))
            except Exception as ex:
                unreal.log("   %s() ERR %s" % (m, str(ex)[:70]))

unreal.log("############ 5. ABP 的 RigidBody 节点配置")
abp = LO(ABP)
if abp:
    for g in unreal.AnimationLibrary.get_animation_graphs(abp):
        try:
            nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_RigidBody)
        except Exception:
            nodes = []
        for n in nodes:
            unreal.log("   图 %s  RigidBody 节点" % g.get_name())
            try:
                nd = n.get_editor_property("node")
                unreal.log("      node = %s" % nd)
                for prop in ("physics_asset", "alpha", "physics_asset_override",
                             "simulation_space", "component_space_kinematic_reference",
                             "enable_clipping", "lods", "override_world_gravity",
                             "world_space_gravity", "max_substep_delta_time", "bend_ratio",
                             "override_physics_asset"):
                    try:
                        unreal.log("      %-38s = %s" % (prop, nd.get_editor_property(prop)))
                    except Exception as ex:
                        unreal.log("      %-38s ERR %s" % (prop, str(ex)[:50]))
            except Exception as ex:
                unreal.log("      ERR %s" % ex)

unreal.log("############ 6. ControlRig 节点")
if abp:
    for g in unreal.AnimationLibrary.get_animation_graphs(abp):
        try:
            nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_ControlRig)
        except Exception:
            nodes = []
        for n in nodes:
            try:
                nd = n.get_editor_property("node")
                cr = nd.get_editor_property("control_rig_asset")
                unreal.log("   图 %-14s ControlRig -> %s" % (g.get_name(), cr.get_path_name() if cr else None))
            except Exception as ex:
                unreal.log("   图 %-14s ControlRig ERR %s" % (g.get_name(), str(ex)[:60]))
unreal.log("############ DONE")
