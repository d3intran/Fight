import math
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

if not les.is_in_play_in_editor():
    les.editor_request_begin_play()
    unreal.log("已请求开始 PIE（下一次运行本脚本再读）")
    raise SystemExit(0)

gw = ues.get_game_world()
ch = None
if gw:
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        if a.get_class().get_name().startswith("BP_DariusCharacter"):
            ch = a
            break
if not ch:
    unreal.log("PIE 里还没角色")
    raise SystemExit(0)

mc = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
st = mc.get_socket_transform("hand_rSocket", unreal.RelativeTransformSpace.RTS_WORLD)
q = st.rotation


def qrot(qq, v):
    x, y, z, w = qq.x, qq.y, qq.z, qq.w
    m = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


# 斧头组件 relative_rotation = 0 ⇒ 斧头世界旋转 = socket 世界旋转
for tag, v in (("+Y（大刃，项目笔记）", (0.0, 1.0, 0.0)),
               ("-Y（另一端）", (0.0, -1.0, 0.0))):
    d = qrot(q, v)
    unreal.log("   %-22s 世界方向 = %s   与朝下夹角 %.1f°   与朝上夹角 %.1f°" % (
        tag, [round(x, 3) for x in d],
        math.degrees(math.acos(max(-1, min(1, -d[2])))),
        math.degrees(math.acos(max(-1, min(1, d[2]))))))
ax = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if a.get_class().get_name().startswith("BP_DariusCharacter"):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.get_name() == "WeaponAxe":
                ax = c
if ax:
    r = ax.get_component_rotation()
    unreal.log("   WeaponAxe 组件世界 rot = pitch=%.2f yaw=%.2f roll=%.2f" % (r.pitch, r.yaw, r.roll))
    try:
        unreal.log("   相对旋转 = %s" % ax.get_editor_property("relative_rotation"))
    except Exception:
        pass
unreal.log("### DONE")
