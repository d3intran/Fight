import unreal

ABP = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
PA = "/Game/Character/Darius/SK_Darius_GodKing_Physics"
SM = "/Game/Character/Darius/SK_Darius_GodKing"

CAND = ["use_default_as_simulated", "b_use_default_as_simulated", "physics_asset",
        "override_physics_asset", "default_to_skeletal_mesh_physics_asset",
        "simulation_space", "max_substep_delta_time", "max_substeps", "base_bone",
        "bone_space_base_bone", "world_space_base_bone", "b_enable_world_gravity",
        "b_override_world_gravity", "override_world_gravity", "external_force",
        "component_linear_acc_scale", "component_linear_vel_scale",
        "component_applied_linear_acc_clamp", "b_enable_world_geometry", "overlap_channel",
        "b_force_disable_collision_between_constraint_bodies", "b_use_external_cloth_collision",
        "b_clamp_linear_translation_limit_to_ref_pose", "b_freeze_incoming_pose_on_start",
        "b_transfer_bone_velocities", "b_simulate_anim_physics_after_reset",
        "b_allow_pose_scale_propagation", "evaluation_reset_time", "b_deferred_simulation",
        "simulation_timing", "cached_bounds_scale", "b_enabled", "b_simulation_started",
        "reset_simulated_teleport_type", "world_space_gravity", "anim_physics_min_delta_time",
        "b_check_for_body_transform_init", "damping_alpha", "max_linear_velocity"]

abp = unreal.load_object(None, ABP)
unreal.log("############ 1. RBAN 精确读")
for g in unreal.AnimationLibrary.get_animation_graphs(abp):
    for n in g.get_graph_nodes_of_class(unreal.AnimGraphNode_RigidBody):
        nd = n.get_editor_property("node")
        hit = 0
        for pr in CAND:
            try:
                unreal.log("   %-56s = %s" % (pr, nd.get_editor_property(pr)))
                hit += 1
            except Exception:
                pass
        unreal.log("   === 命中 %d/%d" % (hit, len(CAND)))
        # 整体导出文本（最可靠：能看到全部序列化字段）
        try:
            unreal.log("   --- export_text ---")
            for ln in str(nd.export_text()).split("\n"):
                unreal.log("   %s" % ln)
        except Exception as ex:
            unreal.log("   export_text ERR %s" % str(ex)[:60])
        try:
            unreal.log("   --- to_dict ---")
            d = nd.to_dict()
            for k in sorted(d.keys()):
                unreal.log("      %-50s = %s" % (k, str(d[k])[:90]))
        except Exception as ex:
            unreal.log("   to_dict ERR %s" % str(ex)[:60])

unreal.log("############ 2. 连线（谁喂给谁）")
AL = unreal.AnimationLibrary
for g in AL.get_animation_graphs(abp):
    if g.get_name() != "AnimGraph":
        continue
    nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_Base)
    label = {}
    for n in nodes:
        label[n.get_name()] = n.get_class().get_name().replace("AnimGraphNode_", "")
    for n in nodes:
        for p in n.list_input_pins():
            conns = []
            for x in p.list_connected_pins():
                try:
                    conns.append("%s(%s).%s" % (label.get(x.get_owning_node().get_name(), "?"),
                                                x.get_owning_node().get_name(), x.get_pin_name()))
                except Exception:
                    conns.append("?")
            if conns:
                unreal.log("   %-26s.%-14s <- %s" % (label.get(n.get_name(), "?"), str(p.get_pin_name()), conns))

unreal.log("############ 3. 网格布料接口")
sk = unreal.load_object(None, SM)
try:
    unreal.log("   mesh_clothing_assets = %s" % sk.get_editor_property("mesh_clothing_assets"))
except Exception as ex:
    unreal.log("   mesh_clothing_assets ERR %s" % str(ex)[:60])
try:
    unreal.log("   lod_settings = %s" % str(sk.get_editor_property("lod_settings"))[:200])
except Exception as ex:
    unreal.log("   lod_settings ERR %s" % str(ex)[:60])
try:
    n = sk.get_lod_num()
    unreal.log("   get_lod_num = %s" % n)
except Exception as ex:
    unreal.log("   get_lod_num ERR %s" % str(ex)[:50])
for b in ("cape_chain_01_l", "cape_chain_05_m", "pelvis"):
    try:
        unreal.log("   is_section_using_cloth(%s) ERR?" % b)
    except Exception:
        pass
unreal.log("   dir 蒙皮/权重相关 = %s" % [m for m in dir(sk) if any(k in m.lower() for k in ("cloth", "weight", "skin", "section", "vertex"))][:25])
unreal.log("############ DONE")
