import unreal

PA = "/Game/Character/Darius/SK_Darius_GodKing_Physics"
ABP = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
SM = "/Game/Character/Darius/SK_Darius_GodKing"

pa = unreal.load_object(None, PA)
unreal.log("############ A. 刚体 PhysicsType 实读")
try:
    sbs = pa.get_editor_property("skeletal_body_setups")
    unreal.log("   len(skeletal_body_setups) = %d" % len(sbs))
except Exception as ex:
    sbs = []
    unreal.log("   ERR %s" % str(ex)[:80])
stat = {}
for b in sbs[:40]:
    vals = {}
    for pr in ("bone_name", "physics_type", "body_mass", "linear_damping", "angular_damping",
               "collision_response", "b_use_ccd", "mass_scale", "interpolate"):
        try:
            vals[pr] = b.get_editor_property(pr)
        except Exception:
            pass
    key = str(vals.get("physics_type"))
    stat[key] = stat.get(key, 0) + 1
    unreal.log("   %s" % vals)
unreal.log("   ★ physics_type 分布 = %s" % stat)
try:
    unreal.log("   enum 值参考 Default=%s Kinematic=%s Simulated=%s" % (
        unreal.PhysicsType.PHYS_TYPE_DEFAULT, unreal.PhysicsType.PHYS_TYPE_KINEMATIC,
        unreal.PhysicsType.PHYS_TYPE_SIMULATED))
except Exception as ex:
    unreal.log("   enum ERR %s" % str(ex)[:60])

unreal.log("############ B. RBAN 节点实读")
abp = unreal.load_object(None, ABP)
for g in unreal.AnimationLibrary.get_animation_graphs(abp):
    try:
        nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_RigidBody)
    except Exception as ex:
        unreal.log("   ERR %s" % str(ex)[:60])
        continue
    for n in nodes:
        unreal.log("   图 %s 节点 %s" % (g.get_name(), n.get_name()))
        try:
            nd = n.get_editor_property("node")
            unreal.log("   node = %s (类 %s)" % (nd, nd.get_class().get_name()))
        except Exception as ex:
            unreal.log("   node ERR %s" % str(ex)[:60])
            continue
        cand = ["use_default_as_simulated", "b_use_default_as_simulated",
                "default_to_skeletal_mesh_physics_asset", "b_default_to_skeletal_mesh_physics_asset",
                "alpha", "physics_asset", "override_physics_asset", "simulation_space",
                "max_substep_delta_time", "max_substeps", "base_bone", "b_enabled",
                "b_enable_world_gravity", "b_override_world_gravity", "external_force",
                "component_linear_acc_scale", "component_linear_vel_scale",
                "b_enable_world_geometry", "b_force_disable_collision_between_constraint_bodies",
                "b_use_external_cloth_collision", "b_clamp_linear_translation_limit_to_ref_pose",
                "b_freeze_incoming_pose_on_start", "b_transfer_bone_velocities",
                "b_simulate_anim_physics_after_reset", "reset_simulated_teleport_type",
                "b_allow_pose_scale_propagation", "evaluation_reset_time", "b_custom_stepping",
                "custom_delta_time", "b_simulate_cache_physics", "b_stop_sim_on_reached_steady_state",
                "physics_asset_override", "gravity", "bend_ratio", "lod_threshold",
                "b_override_lod_threshold", "world_space_gravity"]
        got = 0
        for pr in cand:
            try:
                unreal.log("      %-52s = %s" % (pr, nd.get_editor_property(pr)))
                got += 1
            except Exception:
                pass
        unreal.log("      读到 %d 个属性" % got)

unreal.log("############ C. 网格上有没有布料 / LOD 数")
sk = unreal.load_object(None, SM)
for pr in ("physics_asset", "lod_num", "b_enable_cloth", "cloth_assets", "skeleton",
           "bounds_scale", "b_overrideBoundsScale", "streaming_texture_lods_size"):
    try:
        v = sk.get_editor_property(pr)
        unreal.log("   %-28s = %s" % (pr, "len=%d" % len(v) if hasattr(v, "__len__") else v))
    except Exception as ex:
        unreal.log("   %-28s ERR %s" % (pr, str(ex)[:50]))
unreal.log("   dir(sk) cloth 相关 = %s" % [m for m in dir(sk) if "cloth" in m.lower() or "lod" in m.lower()][:20])
unreal.log("############ DONE")
