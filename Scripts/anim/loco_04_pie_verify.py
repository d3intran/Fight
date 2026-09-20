import json
import os
import unreal

OUT_DIR = "E:/UE/Fight/Saved/Preview/Locomotion"
METRICS_PATH = "E:/UE/Fight/Saved/loco_pie_metrics.json"
RT_PATH = "/Game/Temp/RT_LocoShot"
LABEL = "LocoShotCapture"

os.makedirs(OUT_DIR, exist_ok=True)
if os.path.exists(METRICS_PATH):
    os.remove(METRICS_PATH)

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if les.is_in_play_in_editor():
    unreal.log_error("Already in PIE! Please end play session first.")
    raise SystemExit(1)

# Clean up any pre-existing capture actors in editor world
ew = ues.get_editor_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(ew, unreal.Actor):
    if a.get_actor_label() == LABEL:
        eas.destroy_actor(a)

# Create/Configure Render Target
rt = unreal.load_asset(RT_PATH)
if rt is None:
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RT_LocoShot", "/Game/Temp", unreal.TextureRenderTarget2D,
        unreal.TextureRenderTargetFactoryNew())
rt.set_editor_property("size_x", 1280)
rt.set_editor_property("size_y", 720)
rt.set_editor_property("render_target_format", unreal.TextureRenderTargetFormat.RTF_RGBA8)

# Spawn SceneCapture2D actor in editor world
sc_cls = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
cap_actor = eas.spawn_actor_from_class(sc_cls, unreal.Vector(0, 0, 300), unreal.Rotator(0, 0, 0))
cap_actor.set_actor_label(LABEL)
comp = cap_actor.capture_component2d
comp.set_editor_property("texture_target", rt)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
comp.set_editor_property("fov_angle", 70.0)
comp.set_editor_property("capture_every_frame", False)

S = {
    "ticks": 0,
    "handle": None,
    "started": False,
    "ch": None,
    "mc": None,
    "spring_arm": None,
    "camera": None,
    "cmc": None,
    "cap_actor": None,
    "t0": None,
    "records": [],
    "shots": [],
    "shot_idle_done": False,
    "shot_walk_done": False,
    "static_checks": {},
    "finished": False
}

def capture_shot(tag, cam_loc, cam_rot):
    w = ues.get_game_world()
    cap = S["cap_actor"]
    cap.set_actor_location(cam_loc, False, False)
    cap.set_actor_rotation(cam_rot, False)
    cap.capture_component2d.capture_scene()
    try:
        unreal.RenderingLibrary.export_render_target(w, rt, OUT_DIR, tag)
        fn = os.path.join(OUT_DIR, tag + ".png")
    except Exception as e:
        fn = f"ERR: {e}"
    S["shots"].append({"tag": tag, "file": fn})
    unreal.log(f"[PIE] Shot captured: {tag}")

def finish(msg):
    if S["finished"]:
        return
    S["finished"] = True
    try:
        unreal.unregister_slate_post_tick_callback(S["handle"])
    except Exception:
        pass
    
    data = {
        "status": msg,
        "static_checks": S["static_checks"],
        "records": S["records"],
        "shots": S["shots"]
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    unreal.log(f"[PIE] Finished: {msg}, records: {len(S['records'])}, shots: {len(S['shots'])}")
    les.editor_request_end_play()

def on_tick(dt):
    S["ticks"] += 1
    try:
        if not S["started"]:
            if S["ticks"] == 2:
                unreal.log("[PIE] Requesting BeginPlay...")
                les.editor_request_begin_play()
            if S["ticks"] < 40:
                return
            S["started"] = True
            return

        w = ues.get_game_world()
        if w is None:
            if S["ticks"] > 200:
                finish("ERR: No game world")
            return

        # Find live Darius character and capture actor
        if S["ch"] is None:
            for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
                cls_name = a.get_class().get_name()
                if "BP_DariusCharacter" in cls_name:
                    S["ch"] = a
                elif a.get_actor_label() == LABEL:
                    S["cap_actor"] = a

            if S["ch"] is None or S["cap_actor"] is None:
                if S["ticks"] > 300:
                    finish("ERR: Character or capture actor not found")
                return

            ch = S["ch"]
            S["mc"] = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
            S["cmc"] = ch.get_components_by_class(unreal.CharacterMovementComponent)[0]
            arms = ch.get_components_by_class(unreal.SpringArmComponent)
            S["spring_arm"] = arms[0] if arms else None
            cams = ch.get_components_by_class(unreal.CameraComponent)
            S["camera"] = cams[0] if cams else None

            # Record static checks on live PIE instance
            arm = S["spring_arm"]
            cmc = S["cmc"]
            cam = S["camera"]
            S["static_checks"] = {
                "spring_arm_found": arm is not None,
                "arm_length": arm.get_editor_property("target_arm_length") if arm else None,
                "enable_camera_lag": arm.get_editor_property("enable_camera_lag") if arm else None,
                "camera_lag_speed": arm.get_editor_property("camera_lag_speed") if arm else None,
                "enable_camera_rotation_lag": arm.get_editor_property("enable_camera_rotation_lag") if arm else None,
                "camera_rotation_lag_speed": arm.get_editor_property("camera_rotation_lag_speed") if arm else None,
                "camera_found": cam is not None,
                "cmc_max_walk_speed": cmc.get_editor_property("max_walk_speed") if cmc else None,
                "cmc_max_acceleration": cmc.get_editor_property("max_acceleration") if cmc else None,
                "cmc_braking_deceleration_walking": cmc.get_editor_property("braking_deceleration_walking") if cmc else None,
                "cmc_ground_friction": cmc.get_editor_property("ground_friction") if cmc else None,
            }
            S["t0"] = unreal.SystemLibrary.get_game_time_in_seconds(w)
            unreal.log(f"[PIE] Setup complete at t0={S['t0']:.2f}")

        ch = S["ch"]
        cam = S["camera"]
        cmc = S["cmc"]
        t = unreal.SystemLibrary.get_game_time_in_seconds(w)
        rel_t = t - S["t0"]

        # Phase 1: Resting Idle (0.0s to 0.4s)
        if rel_t < 0.4:
            if not S["shot_idle_done"] and rel_t >= 0.2:
                # Capture Idle perspective from character camera
                c_loc = cam.get_world_location()
                c_rot = cam.get_world_rotation()
                capture_shot("idle_shoulder", c_loc, c_rot)
                S["shot_idle_done"] = True

        # Phase 2: Active Walking (0.4s to 2.0s) -> Apply Forward Movement Input
        elif rel_t < 2.0:
            ch.add_movement_input(unreal.Vector(1.0, 0.0, 0.0), 1.0)
            
            # Capture Walking perspective at steady state ~1.3s
            if not S["shot_walk_done"] and rel_t >= 1.3:
                c_loc = cam.get_world_location()
                c_rot = cam.get_world_rotation()
                capture_shot("walk_shoulder", c_loc, c_rot)
                
                # Also side view
                ch_loc = ch.get_actor_location()
                side_cam_loc = unreal.Vector(ch_loc.x, ch_loc.y + 350.0, ch_loc.z + 50.0)
                side_cam_rot = unreal.MathLibrary.find_look_at_rotation(side_cam_loc, unreal.Vector(ch_loc.x, ch_loc.y, ch_loc.z + 40.0))
                capture_shot("walk_side", side_cam_loc, side_cam_rot)
                S["shot_walk_done"] = True

        # Phase 3: Braking & Stop (2.0s to 3.0s) -> No movement input
        elif rel_t >= 2.0:
            pass

        # Sample kinematic metrics every 2 slate ticks
        if S["ticks"] % 2 == 0:
            vel = ch.get_velocity()
            speed = vel.length()
            ch_loc = ch.get_actor_location()
            cam_loc = cam.get_world_location() if cam else unreal.Vector(0,0,0)
            
            # Distance from camera to character
            dx = cam_loc.x - ch_loc.x
            dy = cam_loc.y - ch_loc.y
            dz = cam_loc.z - ch_loc.z
            cam_dist = (dx*dx + dy*dy + dz*dz)**0.5
            
            S["records"].append({
                "t": round(rel_t, 3),
                "speed": round(speed, 2),
                "ch_loc": (round(ch_loc.x, 2), round(ch_loc.y, 2), round(ch_loc.z, 2)),
                "cam_loc": (round(cam_loc.x, 2), round(cam_loc.y, 2), round(cam_loc.z, 2)),
                "cam_dist": round(cam_dist, 2)
            })

        # Finish after braking period
        if rel_t >= 2.8:
            finish("SUCCESS")

    except Exception as e:
        finish(f"EXCEPTION: {e}")

S["handle"] = unreal.register_slate_post_tick_callback(on_tick)
unreal.log("[PIE] Registered locomotion verification callback.")
