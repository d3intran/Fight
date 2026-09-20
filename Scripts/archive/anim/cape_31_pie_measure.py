"""PIE 实机验收：把 ABP 的 RigidBody 节点指向 /Game/Temp/PA_capeA_test，抬升 RBAN 子步
让模拟在低帧率下仍按真实时间推进，然后逐帧量：下垂量 / 离脊柱轴的后距 / 受动摆动。
结果写 Saved/cape_pie_temp.json。
"""
import json
import os
import unreal

def tv(v):
    return (v.x, v.y, v.z)


ABP = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
NEW_PA = "/Game/Temp/PA_capeA_test"
OUT = "E:/UE/Fight/Saved/cape_pie_temp.json"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

if os.path.exists(OUT):
    os.remove(OUT)
if les.is_in_play_in_editor():
    unreal.log_error("ALREADY_IN_PIE")
    raise SystemExit(1)

# ---------------------------------------------------------------- 1 换物理资产
abp = unreal.load_object(None, ABP)
pa_new = unreal.load_object(None, NEW_PA)
changed = []
for g in unreal.AnimationLibrary.get_animation_graphs(abp):
    for n in g.get_graph_nodes_of_class(unreal.AnimGraphNode_RigidBody):
        nd = n.get_editor_property("node")
        before = nd.get_editor_property("override_physics_asset")
        nd.set_editor_property("override_physics_asset", pa_new)
        n.set_editor_property("node", nd)
        nd2 = n.get_editor_property("node")
        changed.append((g.get_name(), str(before.get_path_name() if before else None),
                        str(nd2.get_editor_property("override_physics_asset").get_path_name())))
unreal.log("RBAN_OVERRIDE %s" % changed)
try:
    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
    unreal.log("COMPILE ok")
except Exception as ex:
    unreal.log_warning("COMPILE_ERR %s" % str(ex)[:80])

# ---------------------------------------------------------------- 2 抬升子步 + 降画质
w0 = ues.get_editor_world()
CMDS = [
    "p.RigidBodyNode.MaxSubSteps 40",       # 0.0157*40 = 0.63s >= 低帧率帧长 => 真实时间步进
    "p.RigidBodyNode.EnableTimeBasedReset 0",
    "t.MaxFPS 0",
    "r.DynamicGlobalIlluminationMethod 0",
    "r.ReflectionMethod 0",
    "r.ScreenPercentage 45",
    "sg.ShadowQuality 0",
    "sg.GlobalIlluminationQuality 0",
    "sg.ReflectionQuality 0",
    "sg.AntiAliasingQuality 1",
    "sg.ViewDistanceQuality 1",
]
for c in CMDS:
    try:
        unreal.SystemLibrary.execute_console_command(w0, c)
    except Exception as ex:
        unreal.log_warning("CVAR_ERR %s %s" % (c, str(ex)[:40]))
unreal.log("CVARS set")

# ---------------------------------------------------------------- 3 采样
S = {"ticks": 0, "samples": [], "handle": None, "started": False, "pieticks": 0,
     "phase": "boot"}
BONES = ["pelvis", "spine_03", "clavicle_l", "clavicle_r"] + [
    "cape_chain_%02d_%s" % (i, s) for s in ("l", "m", "r") for i in (1, 3, 5, 7, 9)]


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
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"msg": msg, "samples": S["samples"]}, f)
    unreal.log("SAMPLE_DONE %s n=%d" % (msg, len(S["samples"])))


def on_tick(dt):
    S["ticks"] += 1
    try:
        if not S["started"]:
            if S["ticks"] == 2:
                les.editor_request_begin_play()
            if S["ticks"] < 60:
                return
            S["started"] = True
            unreal.log("PIE_BEGIN in=%s" % les.is_in_play_in_editor())
            return
        w = ues.get_game_world()
        if w is None:
            if S["ticks"] > 200:
                finish("no game world")
            return
        ch = None
        for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
            if a.get_class().get_name().startswith("BP_DariusCharacter"):
                ch = a
                break
        if ch is None:
            if S["ticks"] > 400:
                finish("no character")
            return
        if S["pieticks"] % 3 != 0:
            S["pieticks"] += 1
            return
        mc = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        P = {}
        for b in BONES:
            try:
                t = mc.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD).translation
                P[b] = (t.x, t.y, t.z)
            except Exception:
                P[b] = None
        if P.get("pelvis") is None or P.get("spine_03") is None or P.get("cape_chain_01_m") is None:
            S["pieticks"] += 1
            if S["pieticks"] > 700:
                finish("bones missing")
            return
        up = vn(vsub(P["spine_03"], P["pelvis"]))
        side = vn(vsub(P["clavicle_r"], P["clavicle_l"]))
        back = vn(vcross(up, side))
        if vdot(back, vsub(P["cape_chain_01_m"], P["spine_03"])) < 0:
            back = (-back[0], -back[1], -back[2])
        # 脊柱轴线（ pelvis 方向沿 up）用作「离体轴的水平后距」参考点
        ax0 = P["pelvis"]
        s = {"tick": S["pieticks"], "t": round(unreal.SystemLibrary.get_game_time_in_seconds(w), 3),
             "dt": round(dt, 4), "fps": round(1.0 / dt, 2) if dt > 1e-6 else 0.0,
             "actor": [round(v, 1) for v in ch.get_actor_location()], "droop": {}, "post": {}}
        for b in BONES:
            if P[b] is None:
                continue
            d = vsub(P[b], ax0)
            s["droop"][b] = round(vdot(up, d) * 1.0, 2)          # 沿躯干轴高度(相对骨盆, cm)
            s["post"][b] = round(vdot(back, d), 2)               # 身后距离(cm)
        # 每 60 个 pietick 把角色沿面朝方向推 2 m，制造速度激励看披风是否滞后
        if S["pieticks"] % 60 == 30:
            loc = ch.get_actor_location()
            fwd = (side[1], -side[0], 0.0)   # 与 side、up 垂直
            f2 = vn(fwd)
            if vdot(f2, vsub(ax0, P["cape_chain_01_m"])) < 0:
                f2 = (-f2[0], -f2[1], -f2[2])
            ch.set_actor_location(unreal.Vector(loc.x + f2[0] * 200, loc.y + f2[1] * 200, loc.z),
                                  False, False)
            s["teleport"] = 1
        S["samples"].append(s)
        S["pieticks"] += 1
        if len(S["samples"]) >= 90:
            finish("ok")
    except Exception as ex:
        finish("EXC %s" % str(ex)[:160])


S["handle"] = unreal.register_slate_post_tick_callback(on_tick)
unreal.log("REGISTERED, sampling to file")
