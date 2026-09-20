"""PIE 内从背后拍披风：python 里先在编辑器世界放一个 SceneCapture2D，
PIE 会把它复制进游戏世界，然后在 tick 里驱动它拍 0.4s / 2s / 6s 三张。

图写 Saved/Preview/CapeCloth/，信息写 Saved/cape_pie_shots.json。
"""
import json
import os
import unreal

OUT = "E:/UE/Fight/Saved/Preview/CapeCloth"
os.makedirs(OUT, exist_ok=True)
INFO = "E:/UE/Fight/Saved/cape_pie_shots.json"
RT_PATH = "/Game/Temp/RT_CapeShot"
LABEL = "CapeShotCapture"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if os.path.exists(INFO):
    os.remove(INFO)
if les.is_in_play_in_editor():
    unreal.log_error("ALREADY_IN_PIE")
    raise SystemExit(1)

rt = unreal.load_asset(RT_PATH)
if rt is None:
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RT_CapeShot", "/Game/Temp", unreal.TextureRenderTarget2D,
        unreal.TextureRenderTargetFactoryNew())
rt.set_editor_property("size_x", 900)
rt.set_editor_property("size_y", 1200)
try:
    rt.set_editor_property("render_target_format", unreal.TextureRenderTargetFormat.RTF_RGBA8)
    unreal.log("RT format -> RGBA8")
except Exception as ex:
    unreal.log_warning("RT format set failed: %s" % str(ex)[:60])

# ---- 编辑器世界放一个采相机（PIE 复制进游戏世界）----
ew = ues.get_editor_world()
existing = [a for a in unreal.GameplayStatics.get_all_actors_of_class(ew, unreal.Actor)
            if a.get_actor_label() == LABEL]
if existing:
    eas.destroy_actor(existing[0])
sc_cls = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
cap_actor = eas.spawn_actor_from_class(sc_cls, unreal.Vector(0, 0, 300), unreal.Rotator(0, 0, 0))
cap_actor.set_actor_label(LABEL)
comp = cap_actor.capture_component2d
comp.set_editor_property("texture_target", rt)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
comp.set_editor_property("fov_angle", 42.0)
comp.set_editor_property("capture_every_frame", False)
unreal.log("editor-world capture placed: %s" % cap_actor.get_name())

S = {"ticks": 0, "handle": None, "started": False, "actor": None, "cap": None,
     "done": {}, "shots": [], "t0": None}
SHOT_OFFSETS = (0.5, 2.0, 5.0, 5.2)   # 相对找到角色的时刻；最后两张间隔 0.2s 用于判抖动


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vn(a):
    d = vdot(a, a) ** 0.5
    return (a[0] / d, a[1] / d, a[2] / d) if d > 1e-9 else a


def finish(msg):
    try:
        unreal.unregister_slate_post_tick_callback(S["handle"])
    except Exception:
        pass
    with open(INFO, "w", encoding="utf-8") as f:
        json.dump({"msg": msg, "shots": S["shots"], "ticks": S["ticks"]}, f)
    unreal.log("SHOTS_DONE %s n=%d" % (msg, len(S["shots"])))


def on_tick(dt):
    S["ticks"] += 1
    try:
        if not S["started"]:
            if S["ticks"] == 2:
                les.editor_request_begin_play()
            if S["ticks"] < 45:
                return
            S["started"] = True
            unreal.log("PIE_BEGIN=%s" % les.is_in_play_in_editor())
            return
        w = ues.get_game_world()
        if w is None:
            return
        if S["cap"] is None:
            for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
                if a.get_class().get_name().startswith("BP_DariusCharacter"):
                    S["actor"] = a
                elif a.get_actor_label() == LABEL:
                    S["cap"] = a
            if S["actor"] is None or S["cap"] is None:
                if S["ticks"] > 900:
                    finish("no actor/cap actor=%s cap=%s" % (S["actor"], S["cap"]))
                return
            S["t0"] = unreal.SystemLibrary.get_game_time_in_seconds(w)
            unreal.log("found actor+cap in PIE: %s / %s  t0=%.2f" % (
                S["actor"].get_name(), S["cap"].get_name(), S["t0"]))
        ch = S["actor"]
        mc = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        t = unreal.SystemLibrary.get_game_time_in_seconds(w)
        for want in SHOT_OFFSETS:
            if want in S["done"] or (t - S["t0"]) < want:
                continue
            P = {}
            for b in ("pelvis", "spine_03", "clavicle_l", "clavicle_r", "cape_chain_01_m"):
                st = mc.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD).translation
                P[b] = (st.x, st.y, st.z)
            up = vn(vsub(P["spine_03"], P["pelvis"]))
            side = vn(vsub(P["clavicle_r"], P["clavicle_l"]))
            back = vn(vcross(up, side))
            if vdot(back, vsub(P["cape_chain_01_m"], P["spine_03"])) < 0:
                back = (-back[0], -back[1], -back[2])
            target = tuple(P["pelvis"][k] + up[k] * 60 for k in range(3))
            cam = tuple(target[k] + back[k] * 330 + (40 if k == 2 else 0) for k in range(3))
            cap = S["cap"]
            cap.set_actor_location(unreal.Vector(*cam), False, False)
            cap.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
                unreal.Vector(*cam), unreal.Vector(*target)), False)
            cap.capture_component2d.capture_scene()
            name = "T%04d" % int(want * 100)
            try:
                unreal.RenderingLibrary.export_render_target(w, rt, OUT, name)
                fn = os.path.join(OUT, name + ".png")
            except Exception as ex:
                fn = "EXPORT_ERR %s" % str(ex)[:60]
            S["done"][want] = True
            S["shots"].append({"want": want, "t": round(t, 2),
                               "fps": round(1.0 / dt, 1) if dt > 1e-6 else 0,
                               "file": fn, "cam": [round(v, 1) for v in cam]})
            unreal.log("SHOT %s at t=%.2f fps=%.1f" % (name, t, 1.0 / dt if dt > 1e-6 else 0))
            if len(S["shots"]) >= len(SHOT_OFFSETS):
                finish("ok")
                return
    except Exception as ex:
        finish("EXC %s" % str(ex)[:160])


S["handle"] = unreal.register_slate_post_tick_callback(on_tick)
unreal.log("REGISTERED shots v2")
