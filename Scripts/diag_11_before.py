import unreal, os, time

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()

# 清理
for a in actor_sub.get_all_level_actors():
    if "BP_DariusCharacter" in a.get_name() or "ShotCam" in a.get_name():
        actor_sub.destroy_actor(a)

bp_class = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp_class, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 180))
actor.set_actor_label("DariusDiag")
print("Spawned:", actor.get_name())

mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)
nb = mesh.get_num_bones()
out = []
for i in range(nb):
    bn = mesh.get_bone_name(i)
    ps = mesh.get_socket_transform(bn, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE)
    try:
        pn = str(mesh.get_parent_bone(bn))
    except Exception as e:
        pn = "?"
    out.append(f"{i}\t{bn}\tparent\t{pn}\tlocalScale\t{ps.scale3d.x:.4f},{ps.scale3d.y:.4f},{ps.scale3d.z:.4f}")
with open("E:/UE/Fight/Saved/Shots/bones.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("bones written:", nb)

weapon = None
for c in actor.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name() or "Axe" in c.get_name():
        weapon = c
print("Weapon comp:", weapon.get_name() if weapon else None)
if weapon:
    print("  worldScale:", weapon.get_world_scale())
    print("  worldLoc:", weapon.get_world_location())

actor_sub.set_selected_level_actors([])
out_dir = r"E:/UE/Fight/Saved/Shots"
os.makedirs(out_dir, exist_ok=True)
for cmd in ["ShowFlag.Selection 0", "t.IdleWhenNotForeground 0"]:
    unreal.SystemLibrary.execute_console_command(ew, cmd)

def shoot(name, cam_loc, cam_rot):
    for k in les.get_viewport_config_keys():
        les.set_level_viewport_camera_info(unreal.Vector(*cam_loc), unreal.Rotator(*cam_rot), k)
        try:
            les.editor_set_game_view(True, k)
            les.editor_set_viewport_realtime(True, k)
        except Exception:
            pass
    les.editor_invalidate_viewports()
    time.sleep(0.7)
    p = f"{out_dir}/{name}.png"
    if os.path.exists(p):
        os.remove(p)
    unreal.SystemLibrary.execute_console_command(ew, f'HighResShot 1600x900 filename="{p}"')
    time.sleep(1.6)
    print("shot ->", p)

shoot("BEFORE_front", (-430.0, -300.0, 175.0), (-8.0, 35.0, 0.0))
shoot("BEFORE_wide",  (-700.0, -520.0, 300.0), (-14.0, 36.0, 0.0))
print("DONE")
