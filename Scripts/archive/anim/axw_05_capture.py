import os
import unreal

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = ues.get_editor_world()

OUT = "E:/UE/Fight/Saved/Shots/AxwProbe"
DONE = os.path.join(OUT, "done.txt")
os.makedirs(OUT, exist_ok=True)
if os.path.exists(DONE):
    os.remove(DONE)

TAG = "AxwProbe"
CASES = [
    ("AxeWalk_Mixamo", "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo"),
    ("Walk_Layered", "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"),
    ("Walk_InPlace", "/Game/Character/Darius/Anims/A_Darius_Walk_InPlace"),
]

S = {"step": 0, "rt": None, "mesh": None, "cap": None, "mc": None, "handle": None, "log": []}


def log(m):
    S["log"].append(str(m))
    unreal.log(str(m))


def cleanup():
    for a in list(eas.get_all_level_actors()):
        n, l = a.get_name(), a.get_actor_label()
        if any(x.startswith(TAG) for x in (n, l)):
            eas.destroy_actor(a)


def on_tick(delta):
    try:
        step = S["step"]
        S["step"] = step + 1
        idx = step - 2
        case_i = idx // 4
        sub = idx % 4

        if step == 0:
            cleanup()
            S["rt"] = unreal.RenderingLibrary.create_render_target2d(
                world, 800, 620, unreal.TextureRenderTargetFormat.RTF_RGBA8)
            sm = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
            ma = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0),
                                            unreal.Rotator(pitch=0, yaw=180, roll=0))
            ma.set_actor_label("%s_Mesh" % TAG)
            S["mesh"] = ma
            mc = ma.skeletal_mesh_component
            mc.set_skinned_asset_and_update(sm)
            mc.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            S["mc"] = mc
            sc_class = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
            ca = eas.spawn_actor_from_class(sc_class, unreal.Vector(-700.0, 0.0, 105.0),
                                            unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
            ca.set_actor_label("%s_Cap" % TAG)
            S["cap"] = ca
            cap = ca.get_editor_property("capture_component2d")
            cap.set_editor_property("texture_target", S["rt"])
            cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
            cap.set_editor_property("fov_angle", 40.0)
            cap.set_editor_property("capture_every_frame", False)
            log("setup done")
            return

        if step == 1:
            log("game_time=%.3f  actors=%d" % (
                unreal.SystemLibrary.get_game_time_in_seconds(world), len(eas.get_all_level_actors())))
            return

        if case_i >= len(CASES):
            cleanup()
            unreal.unregister_slate_post_tick_callback(S["handle"])
            with open(DONE, "w", encoding="utf-8") as f:
                f.write("\n".join(S["log"]))
            unreal.log("ALL DONE, actors=%d" % len(eas.get_all_level_actors()))
            return

        name, path = CASES[case_i]
        if sub == 0:
            anim = eal.load_asset(path)
            S["mc"].set_animation(anim)
            S["mc"].play(True)
            log("---- %s : set_animation" % name)
        elif sub == 1:
            S["mc"].set_position(0.35, False)
            log("     set_position 0.35")
        elif sub == 2:
            for b in ("pelvis", "foot_l", "foot_r", "ball_l", "ball_r", "head", "weapon_jnt", "root"):
                try:
                    st = S["mc"].get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD)
                    log("     %-10s world z=%8.2f  %s" % (
                        b, st.translation.z,
                        [round(v, 2) for v in (st.translation.x, st.translation.y, st.translation.z)]))
                except Exception as ex:
                    log("     %-10s ERR %s" % (b, str(ex)[:70]))
            S["cap"].get_editor_property("capture_component2d").capture_scene()
            log("     capture_scene")
        else:
            unreal.RenderingLibrary.export_render_target(world, S["rt"], OUT, "probe_%s" % name)
            log("     export probe_%s" % name)
    except Exception as ex:
        log("TICK EXC %s" % ex)
        try:
            unreal.unregister_slate_post_tick_callback(S["handle"])
        except Exception:
            pass
        with open(DONE, "w", encoding="utf-8") as f:
            f.write("\n".join(S["log"]))


S["handle"] = unreal.register_slate_post_tick_callback(on_tick)
unreal.log("registered post-tick callback, waiting for %d cases" % len(CASES))
