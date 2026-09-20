import math
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.log("PIE = %s" % les.is_in_play_in_editor())

unreal.log("############ 1. 图连线 API")
unreal.log("EdGraphNode: %s" % [m for m in dir(unreal.EdGraphNode) if not m.startswith("_")])
unreal.log("AnimGraphNode_Base: %s" % [m for m in dir(unreal.AnimGraphNode_Base) if not m.startswith("_")])

abp = unreal.load_object(None, "/Game/Character/Darius/Blueprints/ABP_Darius_Test")
if abp:
    for g in unreal.AnimationLibrary.get_animation_graphs(abp):
        if g.get_name() != "AnimGraph":
            continue
        nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_Base)
        for n in nodes:
            cn = n.get_class().get_name()
            info = []
            for m in ("get_pins", "get_all_pins"):
                f = getattr(n, m, None)
                if f:
                    try:
                        ps = f()
                        info.append("%s -> %s" % (m, [str(p.get_name()) for p in ps]))
                    except Exception as ex:
                        info.append("%s ERR %s" % (m, str(ex)[:40]))
            if info:
                unreal.log("   %-42s %s" % (cn, " | ".join(info)))
            else:
                unreal.log("   %-42s (无 pin API)" % cn)

unreal.log("############ 2. PIE 内一次性测量")
gw = ues.get_game_world()
if not gw:
    unreal.log("   不在 PIE")
    raise SystemExit(0)

ch = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if a.get_class().get_name().startswith("BP_DariusCharacter"):
        ch = a
        break
if not ch:
    unreal.log("   找不到角色")
    raise SystemExit(0)

rot = ch.get_actor_rotation()
unreal.log("   actor yaw=%.2f  loc=%s" % (rot.yaw, [round(v, 1) for v in
                                                  (ch.get_actor_location().x, ch.get_actor_location().y,
                                                   ch.get_actor_location().z)]))
unreal.log("   角色上的组件：")
for c in ch.get_components_by_class(unreal.SceneComponent):
    try:
        unreal.log("      %-24s %s" % (c.get_name(), c.get_class().get_name()))
    except Exception:
        pass

mc = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
yaw = math.radians(rot.yaw)
right = (math.cos(yaw), math.sin(yaw), 0.0)      # UE: actor 前向 = +X（yaw 0），右 = +Y
fwd = (-math.sin(yaw), math.cos(yaw), 0.0)

BONES = ["pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r",
         "ball_l", "ball_r", "toe_l", "toe_r", "head"]
P = {}
for b in BONES:
    try:
        st = mc.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD)
        P[b] = (st.translation.x, st.translation.y, st.translation.z)
    except Exception:
        pass


def lat(p, ref):
    return (p[0] - ref[0]) * right[0] + (p[1] - ref[1]) * right[1]


def fw(p, ref):
    return (p[0] - ref[0]) * fwd[0] + (p[1] - ref[1]) * fwd[1]


if "pelvis" in P:
    ref = P["pelvis"]
    unreal.log("   左右次序（正=在角色右侧；左腿应<0、右腿应>0）：")
    for lvl, a, b in (("髋", "thigh_l", "thigh_r"), ("膝", "calf_l", "calf_r"),
                      ("踝", "foot_l", "foot_r"), ("掌", "ball_l", "ball_r"),
                      ("趾", "toe_l", "toe_r")):
        if a in P and b in P:
            la, lb = lat(P[a], ref), lat(P[b], ref)
            unreal.log("      %-3s  %-9s %+7.1f   %-9s %+7.1f   次序差 %+7.1f  %s" % (
                lvl, a, la, b, lb, lb - la, "交叉!" if lb - la < 0 else "正常"))
    unreal.log("   前后：")
    for b in ("foot_l", "foot_r", "ball_l", "ball_r"):
        if b in P:
            unreal.log("      %-9s 前向 %+7.1f  高度 z %7.1f" % (b, fw(P[b], ref), P[b][2]))
    for b in ("thigh_l", "thigh_r", "calf_l", "calf_r"):
        if b in P:
            unreal.log("      %-9s 左右 %+7.1f  高度 z %7.1f" % (b, lat(P[b], ref), P[b][2]))

unreal.log("############ 3. 斧头在哪")
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    n, cn = a.get_name(), a.get_class().get_name()
    if "Axe" in n or "Axe" in cn or "Weapon" in n or "Darius" in n:
        unreal.log("   actor %-34s %s" % (n, cn))
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            try:
                sm = c.get_editor_property("static_mesh")
                unreal.log("      StaticMeshComp %-22s mesh=%s" % (c.get_name(), sm.get_name() if sm else None))
            except Exception:
                pass
unreal.log("############ DONE")
