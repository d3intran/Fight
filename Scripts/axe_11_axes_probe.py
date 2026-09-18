# -*- coding: utf-8 -*-
"""① 结束 PIE ② 清场 ③ 打印战斧世界轴向与关键点 ④ 从斧刃正对机位拍摄"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if les.is_in_play_in_editor():
    les.editor_request_end_play()
    L("!! 已请求结束 PIE —— 请稍后重跑本脚本")
    raise SystemExit

# ---- 彻底清场：所有 Darius / 相机 ----
killed = []
for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith(("BP_DariusCharacter", "TempAudit_", "DariusShowcase", "CameraActor_", "AxeProxy", "AxeCap_", "ShotCam", "TestCamera")):
        killed.append(n)
        actor_sub.destroy_actor(a)
L("清理 actor: %s" % killed)
L("剩余 actor: %s" % [a.get_name() for a in actor_sub.get_all_level_actors()])

# ---- 生成唯一角色 ----
bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 180))
actor.set_actor_label("AXE_Showcase")
actor_sub.set_selected_level_actors([])
L("spawned %s" % actor.get_name())

weapon = None
for c in actor.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name():
        weapon = c
L("weapon comp: %s" % weapon.get_name())

t = weapon.get_world_transform()
L("")
L("=== 战斧世界变换 ===")
L("origin  = %s" % t.translation)
L("scale   = %s" % t.scale3d)
o0 = t.transform_location(unreal.Vector(0.0, 0.0, 0.0))
for nm, v in (("local X", (1, 0, 0)), ("local Y", (0, 1, 0)), ("local Z", (0, 0, 1))):
    d = t.transform_location(unreal.Vector(*v)) - o0
    L("  %s -> world dir (%.4f, %.4f, %.4f)" % (nm, d.x, d.y, d.z))

L("")
L("=== 关键点世界坐标（局部点 → 世界）===")
pts = [("握柄中点  (0,0,11)", (0.0, 0.0, 11.5)),
       ("刃端      (0,-86,11)", (0.0, -85.9, 11.5)),
       ("刃心      (0,-57,11)", (0.0, -57.0, 11.5)),
       ("刃上缘    (0,-57,50)", (0.0, -57.0, 50.0)),
       ("刃下缘    (0,-57,-27)", (0.0, -57.0, -26.9)),
       ("尾钩端    (0,+86,11)", (0.0, 85.9, 11.5))]
for nm, p in pts:
    w = t.transform_location(unreal.Vector(*p))
    L("  %-22s -> (%.1f, %.1f, %.1f)" % (nm, w.x, w.y, w.z))

mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)
for bn in ("root", "head", "hand_r", "hand_l", "foot_r"):
    try:
        w = mesh.get_socket_transform(unreal.Name(bn), unreal.RelativeTransformSpace.RTS_WORLD)
        L("  bone %-8s world (%.1f, %.1f, %.1f)" % (bn, w.translation.x, w.translation.y, w.translation.z))
    except Exception as e:
        L("  bone %s err %s" % (bn, e))

# ---- 机位：绕斧头 AABB 中心一圈 ----
b = weapon.get_editor_property("static_mesh").get_bounds()
lo = b.origin - b.box_extent
hi = b.origin + b.box_extent
cs = [t.transform_location(unreal.Vector(lo.x if i == 0 else hi.x,
                                        lo.y if j == 0 else hi.y,
                                        lo.z if k == 0 else hi.z))
      for i in (0, 1) for j in (0, 1) for k in (0, 1)]
ctr = unreal.Vector(sum(c.x for c in cs) / 8.0, sum(c.y for c in cs) / 8.0, sum(c.z for c in cs) / 8.0)
L("")
L("战斧世界 AABB 中心 = (%.1f, %.1f, %.1f)" % (ctr.x, ctr.y, ctr.z))

cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")
out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)
cam_specs = [
    ("V1_axeside", unreal.Vector(ctr.x, ctr.y, ctr.z + 30), unreal.Rotator(-6.0, -90.0, 0.0)),
    ("V2_axefront", unreal.Vector(ctr.x + 320, ctr.y - 320, ctr.z + 90), unreal.Rotator(-12.0, 45.0, 0.0)),
    ("V3_high", unreal.Vector(ctr.x - 260, ctr.y - 260, ctr.z + 320), unreal.Rotator(-35.0, 45.0, 0.0)),
]
LOC = {}
for nm, loc, rot in cam_specs:
    if nm == "V1_axeside":
        loc = unreal.Vector(ctr.x - 620, ctr.y, ctr.z + 20)
    LOC[nm] = (loc, rot)

for nm, (loc, rot) in LOC.items():
    cam = actor_sub.spawn_actor_from_class(cam_class, loc, rot)
    cam.set_actor_label("CameraActor_" + nm)
    try:
        cam.camera_component.set_editor_property("field_of_view", 45.0)
    except Exception:
        pass
    L("[%s] cam at (%.1f,%.1f,%.1f) rot %s" % (nm, loc.x, loc.y, loc.z, rot))

L("=== DONE ===")
