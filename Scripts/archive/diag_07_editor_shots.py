import unreal, os, time

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
# 1. 结束 PIE
while les.is_in_play_in_editor():
    les.editor_request_end_play()
    time.sleep(0.5)
print("PIE ended:", les.is_in_play_in_editor())

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()
print("EditorWorld:", ew.get_name())

# 2. 检查 SK 资产上 socket 的实际存盘值
sk = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
print("SK loaded:", sk)
if sk:
    s = sk.find_socket(unreal.Name("hand_rSocket"))
    print("hand_rSocket found:", s)
    if s:
        print("  relScale:", s.get_editor_property("relative_scale"))
        print("  relLoc:", s.get_editor_property("relative_location"))
        print("  relRot:", s.get_editor_property("relative_rotation"))
        print("  parent:", s.get_editor_property("parent_socket_name"))

# 3. 清理 + 重生一个干净的测试角色
for a in actor_sub.get_all_level_actors():
    if "BP_DariusCharacter" in a.get_name() or "ShotCam" in a.get_name() or "TestCamera" in a.get_name():
        actor_sub.destroy_actor(a)

bp_class = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp_class, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 180))
actor.set_actor_label("DariusDiag")
print("Spawned:", actor.get_name())

for c in actor.get_components_by_class(unreal.ActorComponent):
    print("  comp:", c.get_name(), c.get_class().get_name())
    if isinstance(c, unreal.StaticMeshComponent):
        print("     mesh:", c.get_editor_property("static_mesh"))
        print("     worldScale:", c.get_world_scale())
        print("     worldLoc:", c.get_world_location())
        try:
            print("     socket:", c.get_attach_socket_name())
        except Exception:
            pass

actor_sub.set_selected_level_actors([])
out_dir = r"E:/UE/Fight/Saved/Shots"
os.makedirs(out_dir, exist_ok=True)
for cmd in ["showflag.Billboard 0", "showflag.Selection 0", "t.IdleWhenNotForeground 0"]:
    unreal.SystemLibrary.execute_console_command(ew, cmd)

def shoot(name, cam_loc, cam_rot, res="1600x900"):
    for k in les.get_viewport_config_keys():
        les.set_level_viewport_camera_info(unreal.Vector(*cam_loc), unreal.Rotator(*cam_rot), k)
        try:
            les.editor_set_game_view(True, k)
            les.editor_set_viewport_realtime(True, k)
        except Exception:
            pass
    les.editor_invalidate_viewports()
    time.sleep(0.8)
    p = f"{out_dir}/{name}.png"
    if os.path.exists(p):
        os.remove(p)
    unreal.SystemLibrary.execute_console_command(ew, f'HighResShot {res} filename="{p}"')
    time.sleep(1.8)
    print("shot ->", p)

# 角色面朝 -X (rot 180)。右手在 +Y 侧
shoot("S1_front_full",   (-420.0, -260.0, 165.0), (-6.0, 32.0, 0.0))
shoot("S2_hand_close",   (-150.0, -120.0, 140.0), (-8.0, 50.0, 0.0))
shoot("S3_feet",         (-260.0, -150.0, 45.0),  (0.0, 35.0, 0.0))
shoot("S4_back_full",    (420.0, 40.0, 165.0),    (-6.0, -95.0, 0.0))
print("DONE")
