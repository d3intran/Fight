"""布料数值验收（PIE 内）：
  - sim_time 是否随帧递增        → 证明布料模拟在跑（不是冻结姿势）
  - kinematic / dynamic 粒子数   → 验证肩部钉住是否生效
  - 瞬移 3m 后拍两张图           → 真布料会滞后拖尾（图里能看出来）
结果写 Saved/cape_cloth_probe.json + Saved/Preview/CapeCloth/SW*.png
"""
import json
import os
import unreal

OUT = "E:/UE/Fight/Saved/Preview/CapeCloth"
INFO = "E:/UE/Fight/Saved/cape_cloth_probe.json"
RT_PATH = "/Game/Temp/RT_CapeShot"
LABEL = "CapeShotCapture"
os.makedirs(OUT, exist_ok=True)
if os.path.exists(INFO):
    os.remove(INFO)

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
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
rt.set_editor_property("render_target_format", unreal.TextureRenderTargetFormat.RTF_RGBA8)

ew = ues.get_editor_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(ew, unreal.Actor):
    if a.get_actor_label() == LABEL:
        eas.destroy_actor(a)
sc_cls = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
cap_actor = eas.spawn_actor_from_class(sc_cls, unreal.Vector(0, 0, 300), unreal.Rotator(0, 0, 0))
cap_actor.set_actor_label(LABEL)
comp = cap_actor.capture_component2d
comp.set_editor_property("texture_target", rt)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
comp.set_editor_property("fov_angle", 42.0)
comp.set_editor_property("capture_every_frame", False)

S = {"ticks": 0, "handle": None, "started": False, "actor": None, "cap": None, "t0": None,
     "series": [], "shots": [], "n": 0, "teleported": False}
SAMPLE_OFFSETS = (0.3, 0.6, 1.0, 1.5, 2.0, 2.5, 3.0)


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
        json.dump({"msg": msg, "series": S["series"], "shots": S["shots"]}, f)
    unreal.log("PROBE_DONE %s series=%d shots=%d" % (msg, len(S["series"]), len(S["shots"])))


def cloth_stats(mc):
    out = {}
    try:
        it = mc.get_clothing_simulation_interactor()
        out["interactor_class"] = it.get_class().get_name() if it else None
        if it:
            for nm in ("get_num_cloths", "get_num_dynamic_particles",
                       "get_num_kinematic_particles", "get_simulation_time", "get_num_substeps"):
                try:
                    out[nm] = getattr(it, nm)()
                except Exception as ex:
                    out[nm] = "ERR %s" % str(ex)[:40]
    except Exception as ex:
        out["interactor"] = "ERR %s" % str(ex)[:60]
    return out


def shoot(tag, mc, ch):
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
    w = ues.get_game_world()
    try:
        unreal.RenderingLibrary.export_render_target(w, rt, OUT, tag)
        fn = os.path.join(OUT, tag)
    except Exception as ex:
        fn = "ERR %s" % str(ex)[:50]
    S["shots"].append({"tag": tag, "file": fn, "cam": [round(v, 1) for v in cam]})
    unreal.log("SHOT %s" % tag)


def on_tick(dt):
    S["ticks"] += 1
    try:
        if not S["started"]:
            if S["ticks"] == 2:
                les.editor_request_begin_play()
            if S["ticks"] < 45:
                return
            S["started"] = True
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
                return
            S["t0"] = unreal.SystemLibrary.get_game_time_in_seconds(w)
            unreal.log("READY t0=%.2f" % S["t0"])
        ch, mc = S["actor"], S["actor"].get_components_by_class(unreal.SkeletalMeshComponent)[0]
        t = unreal.SystemLibrary.get_game_time_in_seconds(w)
        rel = t - S["t0"]

        for want in SAMPLE_OFFSETS:
            if S["n"] < len(SAMPLE_OFFSETS) and rel >= want:
                st = cloth_stats(mc)
                st["t"] = round(rel, 2)
                S["series"].append(st)
                S["n"] += 1
                unreal.log("STATS t=%.2f %s" % (rel, json.dumps(st, ensure_ascii=False)[:200]))

        # 采样完 +2.0s 后：拍一张、瞬移 3m、再拍两张
        if S["n"] >= len(SAMPLE_OFFSETS) and not S["teleported"]:
            shoot("SW_before", mc, ch)

            def bp(bone):
                t3 = mc.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_WORLD).translation
                return (t3.x, t3.y, t3.z)

            side_b = vn(vsub(bp("clavicle_r"), bp("clavicle_l")))
            loc = ch.get_actor_location()
            ch.set_actor_location(unreal.Vector(loc.x + side_b[0] * 300, loc.y + side_b[1] * 300, loc.z),
                                  False, False)
            S["teleported"] = True
            S["tmove"] = t
            unreal.log("TELEPORT 300cm along side axis")
            return
        if S["teleported"]:
            dtm = t - S["tmove"]
            if "SW_after" not in [s["tag"] for s in S["shots"]] and dtm >= 0.25:
                shoot("SW_after", mc, ch)
            if dtm >= 1.5:
                shoot("SW_late", mc, ch)
                finish("ok")
    except Exception as ex:
        finish("EXC %s" % str(ex)[:160])


S["handle"] = unreal.register_slate_post_tick_callback(on_tick)
unreal.log("REGISTERED cloth probe")
