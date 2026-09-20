import json
import os
import unreal

INFO = "E:/UE/Fight/Saved/cape_cloth_pie_check.json"
if os.path.exists(INFO):
    try:
        os.remove(INFO)
    except Exception:
        pass

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

if les.is_in_play_in_editor():
    unreal.log_error("ALREADY_IN_PIE")
    raise SystemExit(1)

S = {"ticks": 0, "handle": None, "started": False, "samples": [], "t0": None}

def finish(msg):
    try:
        unreal.unregister_slate_post_tick_callback(S["handle"])
    except Exception:
        pass
    with open(INFO, "w", encoding="utf-8") as f:
        json.dump({"msg": msg, "samples": S["samples"]}, f, indent=2, ensure_ascii=False)
    unreal.log("PIE_CHECK_DONE: %s (samples=%d)" % (msg, len(S["samples"])))

def on_tick(dt):
    S["ticks"] += 1
    try:
        if not S["started"]:
            if S["ticks"] == 2:
                les.editor_request_begin_play()
            if S["ticks"] < 30:
                return
            S["started"] = True
            return
            
        w = ues.get_game_world()
        if w is None:
            return
            
        # Find character
        chars = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character)
        if not chars:
            return
            
        ch = chars[0]
        mc = ch.get_component_by_class(unreal.SkeletalMeshComponent)
        if not mc:
            return
            
        t = unreal.SystemLibrary.get_game_time_in_seconds(w)
        if S["t0"] is None:
            S["t0"] = t
            
        rel = t - S["t0"]
        it = mc.get_clothing_simulation_interactor()
        stats = {
            "rel_time": round(rel, 3),
            "interactor_class": it.get_class().get_name() if it else "None"
        }
        if it:
            for nm in ("get_num_cloths", "get_num_dynamic_particles",
                       "get_num_kinematic_particles", "get_simulation_time", "get_num_substeps"):
                try:
                    stats[nm] = getattr(it, nm)()
                except Exception as ex:
                    stats[nm] = str(ex)
                    
        S["samples"].append(stats)
        unreal.log("SAMPLE [%d]: %s" % (len(S["samples"]), stats))
        
        # Collect 8 samples over time
        if len(S["samples"]) >= 8:
            finish("OK")
            # Stop PIE
            les.editor_request_end_play()
    except Exception as ex:
        finish("EXC %s" % ex)

S["handle"] = unreal.register_slate_post_tick_callback(on_tick)
unreal.log("REGISTERED pie cloth check")
