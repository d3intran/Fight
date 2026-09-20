import math
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not les.is_in_play_in_editor():
    unreal.log("不在 PIE")
    raise SystemExit(0)
gw = ues.get_game_world()
ch = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if a.get_class().get_name().startswith("BP_DariusCharacter"):
        ch = a
        break
if not ch:
    unreal.log("没角色")
    raise SystemExit(0)

rot = ch.get_actor_rotation()
mc = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
yaw = math.radians(rot.yaw)
right = (math.cos(yaw), math.sin(yaw), 0.0)      # actor yaw 0 ⇒ 前 = +X、右 = +Y
fwd = (-math.sin(yaw), math.cos(yaw), 0.0)
unreal.log("actor yaw=%.2f" % rot.yaw)

BONES = ["pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r",
         "ball_l", "ball_r", "toe_l", "toe_r", "hand_r", "hand_l", "head"]
P = {}
for b in BONES:
    try:
        st = mc.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD)
        P[b] = (st.translation.x, st.translation.y, st.translation.z)
    except Exception:
        pass
ref = P["pelvis"]


def lat(p):
    return (p[0] - ref[0]) * right[0] + (p[1] - ref[1]) * right[1]


def fw(p):
    return (p[0] - ref[0]) * fwd[0] + (p[1] - ref[1]) * fwd[1]


unreal.log("左右次序（左腿应<0、右腿应>0）：")
for lvl, a, b in (("髋", "thigh_l", "thigh_r"), ("膝", "calf_l", "calf_r"),
                  ("踝", "foot_l", "foot_r"), ("掌", "ball_l", "ball_r"), ("趾", "toe_l", "toe_r")):
    if a in P and b in P:
        la, lb = lat(P[a]), lat(P[b])
        unreal.log("   %-3s %-9s %+7.1f  %-9s %+7.1f  次序差 %+7.1f  %s" % (
            lvl, a, la, b, lb, lb - la, "交叉!" if lb - la < 0 else "正常"))
unreal.log("前后 / 高度：")
for b in ("foot_l", "foot_r", "ball_l", "ball_r", "toe_l", "toe_r"):
    if b in P:
        unreal.log("   %-9s 前向 %+7.1f  高 %6.1f" % (b, fw(P[b]), P[b][2]))
unreal.log("脚间距 %.1f cm" % math.dist(P["ball_l"], P["ball_r"]))
unreal.log("### DONE")
