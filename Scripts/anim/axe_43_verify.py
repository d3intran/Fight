import math
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not les.is_in_play_in_editor():
    les.editor_request_begin_play()
    unreal.log("已请求开始 PIE（再跑一次本脚本读结果）")
    raise SystemExit(0)

gw = ues.get_game_world()
ch = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if a.get_class().get_name().startswith("BP_DariusCharacter"):
        ch = a
        break
if not ch:
    unreal.log("还没角色")
    raise SystemExit(0)

mc = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
st = mc.get_socket_transform("hand_rSocket", unreal.RelativeTransformSpace.RTS_WORLD)
hl = mc.get_socket_transform("hand_r", unreal.RelativeTransformSpace.RTS_WORLD).translation
q = st.rotation


def qrot(qq, v):
    x, y, z, w = qq.x, qq.y, qq.z, qq.w
    m = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


S = (st.translation.x, st.translation.y, st.translation.z)
Y = qrot(q, (0.0, 1.0, 0.0))          # 斧头 +Y（大刃端）
unreal.log("hand_r(wrist) = %s" % [round(v, 1) for v in (hl.x, hl.y, hl.z)])
unreal.log("socket/斧头原点 = %s" % [round(v, 1) for v in S])
unreal.log("斧头 +Y 世界方向 = %s  ⇒ 与朝下夹角 %.1f°" % (
    [round(v, 3) for v in Y], math.degrees(math.acos(max(-1, min(1, -Y[2]))))))
head = tuple(S[i] + 86.0 * Y[i] for i in range(3))
pommel = tuple(S[i] - 86.0 * Y[i] for i in range(3))
unreal.log("斧头端(z=原点-握距) z=%.1f  尾端 z=%.1f" % (head[2], pommel[2]))
d = (hl.x - S[0], hl.y - S[1], hl.z - S[2])
proj = sum(d[i] * Y[i] for i in range(3))
perp = math.sqrt(max(0.0, sum(x * x for x in d) - proj * proj))
unreal.log("手腕到斧柄轴线距离 = %.1f cm（越大越像「没握住」；斧柄半径约 3cm）" % perp)
unreal.log("手腕在斧柄上的投影点离斧头 %.1f cm" % (40.0 + proj))
unreal.log("### DONE")
