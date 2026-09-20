import math
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()

unreal.log("############ 1. PIE 期间能不能拿到资产对象")
PATHS = [
    "/Game/Character/Darius/Anims_TP_v2/A_Darius_idle1",
    "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered",
    "/Game/Character/Darius/SK_Darius_GodKing_Physics",
    "/Game/Character/Darius/SK_Darius_GodKing",
    "/Game/Character/Darius/Blueprints/ABP_Darius_Test",
]
for p in PATHS:
    got = {}
    try:
        got["find_object"] = unreal.find_object(None, p + "." + p.rsplit("/", 1)[-1])
    except Exception as ex:
        got["find_object"] = "ERR %s" % str(ex)[:40]
    try:
        got["load_object"] = unreal.load_object(None, p)
    except Exception as ex:
        got["load_object"] = "ERR %s" % str(ex)[:40]
    unreal.log("   %s" % p)
    for k, v in got.items():
        unreal.log("      %-12s -> %s" % (k, v))

unreal.log("############ 2. PIE 内实时姿态（idle 时采样）")
TARGET = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if a.get_class().get_name().startswith("BP_DariusCharacter"):
        TARGET = a
        break
if TARGET:
    mc = TARGET.get_components_by_class(unreal.SkeletalMeshComponent)[0]
    ai = mc.get_anim_instance()
    unreal.log("   anim_instance = %s" % (ai.get_class().get_name() if ai else None))
    try:
        unreal.log("   anim 方法含 state 的: %s" % [m for m in dir(ai) if "state" in m.lower()])
    except Exception:
        pass

    def sub(a, b):
        return tuple(a[i] - b[i] for i in range(3))

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))

    def nrm(v):
        n = math.sqrt(dot(v, v))
        return tuple(x / n for x in v) if n > 1e-9 else (0.0, 0.0, 0.0)

    def yaw(v):
        return math.degrees(math.atan2(v[1], v[0]))

    B = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
         "thigh_l", "thigh_r", "foot_l", "foot_r", "ball_l", "ball_r",
         "clavicle_l", "clavicle_r", "hand_l", "hand_r",
         "cape_chain_01_m", "cape_chain_09_m", "cape_chain_01_l", "cape_chain_09_l"]
    P = {}
    for b in B:
        try:
            t = mc.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD)
            P[b] = (t.translation.x, t.translation.y, t.translation.z)
        except Exception:
            pass

    # 用双脚脚尖方向定「前向」（两只脚平均），避免被躯干姿态污染
    toedirs = []
    for lr in ("l", "r"):
        if "ball_%s" % lr in P and "foot_%s" % lr in P:
            d = sub(P["ball_%s" % lr], P["foot_%s" % lr])
            toedirs.append(nrm((d[0], d[1], 0.0)))
    if toedirs:
        avg = nrm(tuple(sum(d[i] for d in toedirs) for i in range(3)))
        unreal.log("   脚尖平均方向 yaw = %.2f°   （actor yaw = %.2f°）" % (yaw(avg), TARGET.get_actor_rotation().yaw))
        fwd = avg
    else:
        fwd = (1.0, 0.0, 0.0)

    unreal.log("   分段倾斜（相对世界 Z）：")
    for a, b in (("pelvis", "spine_01"), ("spine_01", "spine_02"), ("spine_02", "spine_03"),
                 ("spine_03", "neck_01"), ("neck_01", "head")):
        if a in P and b in P:
            v = sub(P[b], P[a])
            h = math.sqrt(v[0] ** 2 + v[1] ** 2)
            tilt = math.degrees(math.atan2(h, v[2])) if abs(v[2]) > 1e-6 else 90.0
            dirh = nrm((v[0], v[1], 0.0)) if h > 1e-6 else (0, 0, 0)
            fdot = dot(dirh, fwd)
            rdot = dot(dirh, cross((0, 0, 1), fwd))
            unreal.log("      %-18s 段长 %6.1f cm  离竖直 %6.2f°  前向分量 %+6.2f  右侧分量 %+6.2f"
                       % ("%s->%s" % (a, b), math.sqrt(dot(v, v)), tilt, fdot, rdot))
    if "pelvis" in P and "head" in P:
        v = sub(P["head"], P["pelvis"])
        h = math.sqrt(v[0] ** 2 + v[1] ** 2)
        unreal.log("   骨盆->头：离竖直 %.2f°   前向分量 %+.2f  右侧分量 %+.2f" % (
            math.degrees(math.atan2(h, v[2])), dot(nrm((v[0], v[1], 0.0)), fwd),
            dot(nrm((v[0], v[1], 0.0)), cross((0, 0, 1), fwd))))
    if "pelvis" in P and "cape_chain_09_m" in P:
        v = sub(P["cape_chain_09_m"], P["pelvis"])
        d = nrm((v[0], v[1], 0.0))
        unreal.log("   披风末端相对骨盆：水平 %.1f cm  前向分量 %+.2f（负=在身后）  右侧分量 %+.2f"
                   % (math.sqrt(v[0] ** 2 + v[1] ** 2), dot(d, fwd), dot(d, cross((0, 0, 1), fwd))))
unreal.log("############ DONE")
