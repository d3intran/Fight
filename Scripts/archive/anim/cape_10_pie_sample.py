import json
import math
import os
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

OUT = "E:/UE/Fight/Saved/Preview/AxwExport"
DONE = os.path.join(OUT, "pie_sample.json")
os.makedirs(OUT, exist_ok=True)
if os.path.exists(DONE):
    os.remove(DONE)

S = {"ticks": 0, "samples": [], "handle": None, "started": False}


def get_world():
    return ues.get_game_world()


def find_char(w):
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        if a.get_class().get_name().startswith("BP_DariusCharacter"):
            return a
    return None


def find_axe(w):
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        n = a.get_name()
        cn = a.get_class().get_name()
        if "Axe" in n or "Axe" in cn or "Weapon" in n:
            return a
    return None


def finish(msg):
    try:
        unreal.unregister_slate_post_tick_callback(S["handle"])
    except Exception:
        pass
    with open(DONE, "w", encoding="utf-8") as f:
        json.dump({"msg": msg, "samples": S["samples"]}, f)
    unreal.log("SAMPLE DONE: %s (%d samples)" % (msg, len(S["samples"])))


def on_tick(delta):
    S["ticks"] += 1
    try:
        if not S["started"]:
            if S["ticks"] == 2:
                les.editor_request_begin_play()
            if S["ticks"] < 40:
                return
            S["started"] = True
            unreal.log("PIE 应已启动: %s" % les.is_in_play_in_editor())
            return

        w = get_world()
        ch = find_char(w) if w else None
        if ch is None:
            if S["ticks"] > 400:
                finish("no character")
            return

        if S["ticks"] % 15 != 0:
            return

        mc = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        s = {"t": round(unreal.SystemLibrary.get_game_time_in_seconds(w), 3)}
        for b in ("pelvis", "ball_l", "ball_r", "toe_l", "toe_r", "head",
                  "cape_chain_01_l", "cape_chain_05_l", "cape_chain_09_l",
                  "cape_chain_01_m", "cape_chain_05_m", "cape_chain_09_m",
                  "cape_chain_01_r", "cape_chain_05_r", "cape_chain_09_r"):
            try:
                st = mc.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD)
                s[b] = [round(v, 2) for v in (st.translation.x, st.translation.y, st.translation.z)]
            except Exception:
                s[b] = None
        try:
            st = mc.get_socket_transform("hand_rSocket", unreal.RelativeTransformSpace.RTS_WORLD)
            q = st.rotation
            s["hand_rSocket_rot"] = [round(v, 4) for v in (q.x, q.y, q.z, q.w)]
            s["hand_rSocket_loc"] = [round(v, 2) for v in (st.translation.x, st.translation.y, st.translation.z)]
        except Exception as ex:
            s["hand_rSocket_err"] = str(ex)[:60]
        ax = find_axe(w)
        if ax:
            s["axe_actor"] = "%s(%s)" % (ax.get_name(), ax.get_class().get_name())
            try:
                r = ax.get_actor_rotation()
                s["axe_rot"] = [round(r.pitch, 2), round(r.yaw, 2), round(r.roll, 2)]
                loc = ax.get_actor_location()
                s["axe_loc"] = [round(v, 2) for v in (loc.x, loc.y, loc.z)]
            except Exception:
                pass
            for sock in ("Blade_Tip", "Blade_Edge", "Pommel"):
                try:
                    p = ax.get_socket_location(sock) if hasattr(ax, "get_socket_location") else None
                    if p:
                        s["axe_" + sock] = [round(v, 2) for v in (p.x, p.y, p.z)]
                except Exception:
                    pass
        S["samples"].append(s)
        if len(S["samples"]) >= 10:
            finish("ok")
    except Exception as ex:
        finish("EXC %s" % str(ex)[:150])


S["handle"] = unreal.register_slate_post_tick_callback(on_tick)
unreal.log("registered; will begin PIE and sample")
