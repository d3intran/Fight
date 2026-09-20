# 已删除的一次性探针清单（2026-09-20 清理）

> 下面 **101** 个文件是一次性 UE API 探针 / 截图 / 调试脚本，**没有可复用的学习价值**，已从仓库删除。
> 完整原文保留在 `Saved/_backup_scripts_20260920_165857.zip`（本地备份，不进 git）。
> 这一轮探索（给 AnimBP 加 `RigidBody` 节点 / 读图连线）的结论已沉淀进：
> - `.workbuddy/memory/2026-09-19.md`（当天过程）
> - `Docs/Locomotion/AxeWalk_Layered_Merge.md` §8（`RigidBody` 节点确实接在链上的读法）
> - 技能 `ue-anim-layered-merge`

| 文件 | 第一行说明 |
| :--- | :--- |
| `step_bypass_controlrig.py` | -*- coding: utf-8 |
| `step_capture_front_direct.py` | -*- coding: utf-8 |
| `step_capture_hero.py` | -*- coding: utf-8 |
| `step_capture_walk_master.py` | -*- coding: utf-8 |
| `step_capture_walk_seq.py` | -*- coding: utf-8 |
| `step_check_anim_lengths.py` | -*- coding: utf-8 |
| `step_check_bones_c.py` | eal = unreal.EditorAssetLibrary |
| `step_check_bs.py` | -*- coding: utf-8 |
| `step_check_core_constraints.py` | pa = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Physics") |
| `step_check_dummy.py` | -*- coding: utf-8 |
| `step_check_graph_libs.py` | for m in dir(unreal.AnimationLibrary): |
| `step_check_hands.py` | eal = unreal.EditorAssetLibrary |
| `step_check_layered_scale.py` | -*- coding: utf-8 |
| `step_check_mesh_rot.py` | -*- coding: utf-8 |
| `step_check_rb.py` | unreal.log(f"has RigidBody: {hasattr(unreal, 'AnimGraphNode_RigidBody')}") |
| `step_check_space_classes.py` | unreal.log(f"has LocalToComponentSpace: {hasattr(unreal, 'AnimGraphNode_LocalToComponentSpace')}") |
| `step_check_walk_scale.py` | -*- coding: utf-8 |
| `step_compare_upper.py` | eal = unreal.EditorAssetLibrary |
| `step_debug_abp.py` | eal = unreal.EditorAssetLibrary |
| `step_diag_pie_abp.py` | -*- coding: utf-8 |
| `step_dump_idle_upper.py` | -*- coding: utf-8 |
| `step_filter_anim_nodes.py` | eal = unreal.EditorAssetLibrary |
| `step_find_animbps.py` | -*- coding: utf-8 |
| `step_find_any_rb.py` | eal = unreal.EditorAssetLibrary |
| `step_find_convert_nodes.py` | eal = unreal.EditorAssetLibrary |
| `step_find_exact_space.py` | eal = unreal.EditorAssetLibrary |
| `step_find_idles.py` | eal = unreal.EditorAssetLibrary |
| `step_find_layered_node.py` | -*- coding: utf-8 |
| `step_find_space_nodes.py` | eal = unreal.EditorAssetLibrary |
| `step_help_create_node.py` | -*- coding: utf-8 |
| `step_import_layered_walk.py` | -*- coding: utf-8 |
| `step_import_walk.py` | -*- coding: utf-8 |
| `step_inspect_abp.py` | -*- coding: utf-8 |
| `step_inspect_abp_dir.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_abp_graph.py` | -*- coding: utf-8 |
| `step_inspect_all_subgraphs.py` | -*- coding: utf-8 |
| `step_inspect_animgraph_pins.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_animgraph_pins2.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_bge.py` | if hasattr(unreal, "BlueprintGraphEditor"): |
| `step_inspect_c_dict.py` | pa = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Physics") |
| `step_inspect_char_bp.py` | -*- coding: utf-8 |
| `step_inspect_constraint_text.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_constraints.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_controlrig.py` | -*- coding: utf-8 |
| `step_inspect_cr.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_create_node.py` | bge = unreal.BlueprintGraphEditor |
| `step_inspect_euler.py` | -*- coding: utf-8 |
| `step_inspect_eventgraph.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_idle_fbx.py` | -*- coding: utf-8 |
| `step_inspect_idle_fc.py` | -*- coding: utf-8 |
| `step_inspect_idle_frames.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_idle_tp.py` | -*- coding: utf-8 |
| `step_inspect_idle_v2.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_layered.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_layered_node.py` | -*- coding: utf-8 |
| `step_inspect_lights.py` | -*- coding: utf-8 |
| `step_inspect_loco.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_nodes.py` | -*- coding: utf-8 |
| `step_inspect_pa.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_pa2.py` | pa = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Physics") |
| `step_inspect_pa_methods.py` | pa = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Physics") |
| `step_inspect_pa_pkg.py` | pa = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Physics") |
| `step_inspect_pa_t3d.py` | pa = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Physics") |
| `step_inspect_pin_dir.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_pin_names.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_pin_types.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_rb_data.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_rb_dict.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_rb_pins.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_rb_props.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_rb_text.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_schema.py` | -*- coding: utf-8 |
| `step_inspect_sms.py` | -*- coding: utf-8 |
| `step_inspect_state.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_trans_detail.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_trans_nodes.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_trans_pins.py` | eal = unreal.EditorAssetLibrary |
| `step_inspect_transitions.py` | eal = unreal.EditorAssetLibrary |
| `step_list_avail_nodes.py` | eal = unreal.EditorAssetLibrary |
| `step_list_graphs.py` | eal = unreal.EditorAssetLibrary |
| `step_ping.py` | -*- coding: utf-8 |
| `step_run_audit_layered.py` | -*- coding: utf-8 |
| `step_search_add_node.py` | Search all unreal classes/functions that have 'add_node' or 'create_node |
| `step_setup_locomotion.py` | -*- coding: utf-8 |
| `step_test_add_rb.py` | eal = unreal.EditorAssetLibrary |
| `step_test_body_setups.py` | pkg = unreal.load_package("/Game/Character/Darius/SK_Darius_GodKing_Physics") |
| `step_test_connect.py` | -*- coding: utf-8 |
| `step_test_converters.py` | eal = unreal.EditorAssetLibrary |
| `step_test_create_layered.py` | -*- coding: utf-8 |
| `step_test_create_node.py` | -*- coding: utf-8 |
| `step_test_create_rb.py` | eal = unreal.EditorAssetLibrary |
| `step_test_find_obj.py` | pa = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Physics") |
| `step_test_graph_add.py` | eal = unreal.EditorAssetLibrary |
| `step_test_graph_editor.py` | -*- coding: utf-8 |
| `step_test_import_rb.py` | eal = unreal.EditorAssetLibrary |
| `step_test_inspect_rb_pins.py` | eal = unreal.EditorAssetLibrary |
| `step_test_pa_props.py` | pa = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Physics") |
| `step_test_walk_in_level.py` | -*- coding: utf-8 |
| `step_verify_darius_in_level.py` | -*- coding: utf-8 |
| `step_verify_pie_cape.py` | eal = unreal.EditorAssetLibrary |
| `step_wire_rigidbody.py` | eal = unreal.EditorAssetLibrary |
