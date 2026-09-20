import math
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
gw = ues.get_game_world()
if not gw:
    unreal.log("不在 PIE")
    raise SystemExit(0)
ch = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if a.get_class().get_name().startswith("BP_DariusCharacter"):
        ch = a
        break
if not ch:
    unreal.log("没角色")
    raise SystemExit(0)

mc = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
B = ["pelvis", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "hand_l", "hand_r",
     "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r",
     "toe_l", "toe_r", "head"]
P = {}
for b in B:
    try:
        st = mc.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD)
        P[b] = (st.translation.x, st.translation.y, st.translation.z)
    except Exception:
        pass

# ★ 自校准：用「锁骨线」定角色的右轴（锁骨 L/R 的左右是骨架保证的，不依赖任何约定）
sv = tuple(P["clavicle_r"][i] - P["clavicle_l"][i] for i in range(3))
sv = (sv[0], sv[1], 0.0)
n = math.sqrt(sv[0] ** 2 + sv[1] ** 2)
right = (sv[0] / n, sv[1] / n)
fwd = (-right[1], right[0])
unreal.log("由锁骨线定出的角色右轴 = %s（yaw %.1f°）" % ([round(v, 3) for v in right],
                                                        math.degrees(math.atan2(right[1], right[0]))))
ref = P["pelvis"]


def lat(p):
    return (p[0] - ref[0]) * right[0] + (p[1] - ref[1]) * right[1]


def fw(p):
    return (p[0] - ref[0]) * fwd[0] + (p[1] - ref[1]) * fwd[1]


unreal.log("自检（锁骨/手，应该左<0、右>0）：")
for a, b in (("clavicle_l", "clavicle_r"), ("hand_l", "hand_r"), ("upperarm_l", "upperarm_r")):
    unreal.log("   %-11s %+7.1f   %-11s %+7.1f   次序差 %+7.1f %s"
               % (a, lat(P[a]), b, lat(P[b]), lat(P[b]) - lat(P[a]),
                  "← 反了!" if lat(P[b]) - lat(P[a]) < 0 else "ok"))
unreal.log("腿（左应<0、右应>0）：")
for lvl, a, b in (("髋", "thigh_l", "thigh_r"), ("膝", "calf_l", "calf_r"),
                  ("踝", "foot_l", "foot_r"), ("掌", "ball_l", "ball_r"), ("趾", "toe_l", "toe_r")):
    la, lb = lat(P[a]), lat(P[b])
    unreal.log("   %-3s %-9s %+7.1f  %-9s %+7.1f  次序差 %+7.1f  %s"
               % (lvl, a, la, b, lb, lb - la, "交叉!" if lb - la < 0 else "正常"))
unreal.log("前后/高度：")
for b in ("foot_l", "foot_r", "ball_l", "ball_r"):
    unreal.log("   %-8s 前后 %+7.1f  高 %6.1f" % (b, fw(P[b]), P[b][2]))
unreal.log("脚间距 = %.1f cm" % math.dist(P["ball_l"], P["ball_r"]))
unreal.log("### DONE")
