import math
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
if not gw:
    unreal.log_error("不在 PIE 里")
    raise SystemExit(1)

TARGET = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if a.get_class().get_name().startswith("BP_DariusCharacter"):
        TARGET = a
        break
if not TARGET:
    unreal.log_error("PIE 里没找到角色")
    raise SystemExit(1)

arot = TARGET.get_actor_rotation()
aloc = TARGET.get_actor_location()
vel = TARGET.get_velocity()
mc = TARGET.get_components_by_class(unreal.SkeletalMeshComponent)[0]
mrot = mc.get_component_rotation() if hasattr(mc, "get_component_rotation") else None
mloc = mc.get_component_location() if hasattr(mc, "get_component_location") else None

unreal.log("### actor: loc=%s yaw=%.2f  speed=%.2f" % (
    [round(v, 1) for v in (aloc.x, aloc.y, aloc.z)], arot.yaw,
    math.sqrt(vel.x ** 2 + vel.y ** 2 + vel.z ** 2)))
unreal.log("### mesh : loc=%s rot=(p=%.2f y=%.2f r=%.2f)" % (
    [round(v, 1) for v in (mloc.x, mloc.y, mloc.z)] if mloc else None,
    mrot.pitch if mrot else 0, mrot.yaw if mrot else 0, mrot.roll if mrot else 0))


def sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def nrm(v):
    n = math.sqrt(dot(v, v))
    return tuple(x / n for x in v) if n > 1e-9 else (0.0, 0.0, 0.0)


def yaw_of(v):
    return math.degrees(math.atan2(v[1], v[0]))


BODY = ["pelvis", "spine_01", "spine_03", "neck_01", "head", "clavicle_l", "clavicle_r",
        "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r",
        "toe_l", "toe_r", "hand_l", "hand_r"]
CAPE = ["cape_chain_01_l", "cape_chain_01_m", "cape_chain_01_r",
        "cape_chain_05_l", "cape_chain_05_m", "cape_chain_05_r",
        "cape_chain_09_l", "cape_chain_09_m", "cape_chain_09_r",
        "godking_hair_chain_01", "godking_hair_chain_05"]

pos = {}
for b in BODY + CAPE:
    try:
        st = mc.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD)
        pos[b] = (st.translation.x, st.translation.y, st.translation.z)
    except Exception as ex:
        unreal.log("   %s ERR %s" % (b, str(ex)[:50]))

# 用「披风在身后」反推网格真实朝向：pelvis → cape_chain_01_m
if "cape_chain_01_m" in pos and "pelvis" in pos:
    back = nrm(sub(pos["cape_chain_01_m"], pos["pelvis"]))
    unreal.log("### 由披风推网格真实朝向")
    unreal.log("   pelvis->cape_01_m（应指向「背后」）= %s  yaw=%.2f°" % (
        [round(v, 3) for v in back], yaw_of(back)))
    unreal.log("   ⇒ 网格真实「正面」yaw ≈ %.2f°" % ((yaw_of(back) + 180.0 + 180.0) % 360.0 - 180.0))
    unreal.log("   actor yaw=%.2f   mesh world yaw=%.2f" % (
        arot.yaw, mrot.yaw if mrot else 0))

if all(k in pos for k in ("pelvis", "head", "thigh_l", "thigh_r")):
    up = nrm(sub(pos["head"], pos["pelvis"]))
    right = nrm(sub(pos["thigh_r"], pos["thigh_l"]))
    fwd = nrm(cross(right, up))          # 右手系：forward = right × up
    unreal.log("### 姿态轴（世界系）")
    unreal.log("   up    = %s   离世界 Z %.2f°" % ([round(v, 3) for v in up],
                                                  math.degrees(math.acos(max(-1, min(1, up[2]))))))
    unreal.log("   right = %s" % [round(v, 3) for v in right])
    unreal.log("   fwd   = %s   yaw=%.2f°" % ([round(v, 3) for v in fwd], yaw_of(fwd)))
    horiz = nrm((up[0], up[1], 0.0))
    fh = nrm((fwd[0], fwd[1], 0.0))
    rh = nrm((right[0], right[1], 0.0))
    lean_f = math.degrees(math.acos(max(-1, min(1, dot(horiz, fh)))))
    lean_r = math.degrees(math.acos(max(-1, min(1, dot(horiz, rh)))))
    tilt = math.degrees(math.acos(max(-1, min(1, up[2]))))
    unreal.log("   躯干离竖直 %.2f°  ⇒ 前/后倾分量 %.2f°（0=纯前后），左/右倾分量 %.2f°（0=纯左右）"
               % (tilt, lean_f, lean_r))
    unreal.log("   与动画前向夹角：动画 fwd yaw %.2f°  vs  actor yaw %.2f°  = %.2f°"
               % (yaw_of(fwd), arot.yaw, yaw_of(fwd) - arot.yaw))

unreal.log("### 关键骨世界坐标")
for b in ("pelvis", "spine_03", "neck_01", "head", "thigh_l", "thigh_r",
          "foot_l", "foot_r", "ball_l", "ball_r",
          "cape_chain_01_m", "cape_chain_05_m", "cape_chain_09_m",
          "cape_chain_01_l", "cape_chain_09_l", "cape_chain_01_r", "cape_chain_09_r",
          "godking_hair_chain_01", "godking_hair_chain_05"):
    if b in pos:
        unreal.log("   %-22s %s" % (b, [round(v, 1) for v in pos[b]]))

if "pelvis" in pos and "cape_chain_09_m" in pos:
    pel = pos["pelvis"]
    unreal.log("### 披风末端相对骨盆（水平距离 / 落差）")
    for b in ("cape_chain_01_m", "cape_chain_05_m", "cape_chain_09_m",
              "cape_chain_01_l", "cape_chain_05_l", "cape_chain_09_l",
              "cape_chain_01_r", "cape_chain_05_r", "cape_chain_09_r"):
        if b in pos:
            d = sub(pos[b], pel)
            unreal.log("   %-18s 水平 %.1f cm   垂直 %.1f cm" % (
                b, math.sqrt(d[0] ** 2 + d[1] ** 2), d[2]))
unreal.log("### DONE")
