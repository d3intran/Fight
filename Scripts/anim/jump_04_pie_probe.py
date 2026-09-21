import json
import os
import unreal

OUT_DIR = "E:/UE/Fight/Saved/Preview/Jump"
METRICS_PATH = "E:/UE/Fight/Saved/jump_pie_metrics.json"
RT_PATH = "/Game/Temp/RT_JumpShot"
LABEL = "JumpShotCapture"

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
        "RT_JumpShot", "/Game/Temp", unreal.TextureRenderTarget2D,
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
    "jump_triggered": False,
    "records": [],
    "shots": [],
    "shot_apex_done": False,
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
    unreal.log(f"[PIE Jump] Shot captured: {tag}")

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
        "records": S["records"],
        "shots": S["shots"]
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    unreal.log(f"[PIE Jump] Finished: {msg}, records: {len(S['records'])}")
    les.editor_request_end_play()

def on_tick(dt):
    S["ticks"] += 1
    try:
        if not S["started"]:
            if S["ticks"] == 2:
                unreal.log("[PIE Jump] Requesting BeginPlay...")
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
            S["t0"] = unreal.SystemLibrary.get_game_time_in_seconds(w)
            unreal.log(f"[PIE Jump] Setup complete at t0={S['t0']:.2f}")

        ch = S["ch"]
        mc = S["mc"]
        cmc = S["cmc"]
        cam = S["camera"]
        t = unreal.SystemLibrary.get_game_time_in_seconds(w)
        rel_t = t - S["t0"]

        # Trigger jump at t = 0.5s
        if rel_t >= 0.5 and not S["jump_triggered"]:
            ch.jump()
            S["jump_triggered"] = True
            unreal.log(f"[PIE Jump] Triggered Jump at rel_t={rel_t:.2f}s")

        # Record metrics during jump
        vel = ch.get_velocity()
        ch_loc = ch.get_actor_location()
        cam_loc = cam.get_world_location() if cam else unreal.Vector(0,0,0)
        
        # Check bone scales or locations on mc
        head_t = mc.get_socket_transform("head", unreal.RelativeTransformSpace.RTS_WORLD)
        pelvis_t = mc.get_socket_transform("pelvis", unreal.RelativeTransformSpace.RTS_WORLD)
        root_t = mc.get_socket_transform("root", unreal.RelativeTransformSpace.RTS_WORLD)
        
        origin, box_extent = ch.get_actor_bounds(False)
        mc_scale = mc.get_editor_property("relative_scale3d")
        
        dx = cam_loc.x - ch_loc.x
        dy = cam_loc.y - ch_loc.y
        dz = cam_loc.z - ch_loc.z
        cam_dist = (dx*dx + dy*dy + dz*dz)**0.5

        rec = {
            "t": round(rel_t, 3),
            "z": round(ch_loc.z, 2),
            "vel_z": round(vel.z, 2),
            "movement_mode": str(cmc.movement_mode),
            "cam_dist": round(cam_dist, 2),
            "actor_extent": (round(box_extent.x, 1), round(box_extent.y, 1), round(box_extent.z, 1)),
            "mc_scale": (round(mc_scale.x, 3), round(mc_scale.y, 3), round(mc_scale.z, 3)),
            "root_scale": (round(root_t.scale3d.x, 3), round(root_t.scale3d.y, 3), round(root_t.scale3d.z, 3)),
            "pelvis_z": round(pelvis_t.translation.z, 2),
            "head_z": round(head_t.translation.z, 2),
            "head_pelvis_dist": round(head_t.translation.z - pelvis_t.translation.z, 2)
        }
        S["records"].append(rec)

        # Capture apex shot around apex of jump (when vel.z changes from positive to negative)
        if S["jump_triggered"] and not S["shot_apex_done"] and vel.z < 0.0 and rel_t > 0.6:
            # Capture from side to see character scale and jump height
            side_loc = unreal.Vector(ch_loc.x, ch_loc.y + 450.0, ch_loc.z + 50.0)
            side_rot = unreal.MathLibrary.find_look_at_rotation(side_loc, ch_loc)
            capture_shot("jump_apex_side", side_loc, side_rot)
            
            # Capture from follow camera
            c_loc = cam.get_world_location()
            c_rot = cam.get_world_rotation()
            capture_shot("jump_apex_shoulder", c_loc, c_rot)
            S["shot_apex_done"] = True

        # Finish after landing (at t ~ 2.5s)
        if rel_t >= 2.5:
            finish("SUCCESS")

    except Exception as e:
        finish(f"EXCEPTION: {e}")

S["handle"] = unreal.register_slate_post_tick_callback(on_tick)
unreal.log("[PIE Jump] Registered jump probe callback.")
