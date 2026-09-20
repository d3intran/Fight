# -*- coding: utf-8 -*-
"""
战斧握持修正 —— 落盘 + 数值验收
  hand_rSocket.relative_rotation = (-106.334, -70.982, 9.342)
  hand_rSocket.relative_location = (0.18965, 0.10080, 0.00982)   [bone 空间]
"""
import unreal, os, time, math

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()

if les.is_in_play_in_editor():
    les.editor_request_end_play(); L("!! PIE"); raise SystemExit

def R(p, y, r):
    return unreal.Rotator(pitch=p, yaw=y, roll=r)

# ---- 清场 ----
killed = []
for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith(("BP_DariusCharacter", "FIX_", "SceneCapture2D_", "AXE_", "XYZ_", "ABTest_",
                     "StaticMeshActor_0", "StaticMeshActor_5", "StaticMeshActor_6",
                     "CameraActor_", "AxeProxy", "AxeCap_")):
        killed.append(n); actor_sub.destroy_actor(a)
L("清场: %s" % killed)

# ---- 写入 socket ----
sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
sock = sk.find_socket(unreal.Name("hand_rSocket"))
NEW_ROT = R(-106.3340, -70.9820, 9.3420)
NEW_LOC = unreal.Vector(0.18965, 0.10080, 0.00982)
sock.set_editor_property("relative_rotation", NEW_ROT)
sock.set_editor_property("relative_location", NEW_LOC)
sock.set_editor_property("relative_scale", unreal.Vector(0.01, 0.01, 0.01))
saved = unreal.EditorAssetLibrary.save_loaded_asset(sk)
L("保存 SK: %s" % saved)

# 复核（重新载入）
try:
    unreal.EditorAssetLibrary.unload_asset("/Game/Character/Darius/SK_Darius_GodKing")
except Exception as e:
    L("unload 不可用(%s)，改用资产对象复核" % e)
sk2 = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
s2 = sk2.find_socket(unreal.Name("hand_rSocket"))
r2 = s2.get_editor_property("relative_rotation")
l2 = s2.get_editor_property("relative_location")
L("复核 relRot=(%.3f,%.3f,%.3f) relLoc=(%.5f,%.5f,%.5f) relScale=%s" % (
    r2.pitch, r2.yaw, r2.roll, l2.x, l2.y, l2.z, s2.get_editor_property("relative_scale")))

# ---- 验收测量 ----
bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
act = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), R(0.0, 180.0, 0.0))
act.set_actor_label("AXE_Final")
mesh = act.get_component_by_class(unreal.SkeletalMeshComponent)
weapon = None
for c in act.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name():
        weapon = c

sm = unreal.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
L("")
L("=== 验收指标 ===")
L("[1] 几何完整性: UE LOD0 顶点 = %s  (源 FBX = 5661)" % unreal.EditorStaticMeshLibrary.get_number_verts(sm, 0))
L("    SM 局部包围盒 extent = (%.1f, %.1f, %.1f)" % tuple(
    [sm.get_bounds().box_extent.x, sm.get_bounds().box_extent.y, sm.get_bounds().box_extent.z]))

t = weapon.get_world_transform()
o0 = t.transform_location(unreal.Vector(0, 0, 0))
axis_dirs = {}
for nm, v in (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))):
    d = t.transform_location(unreal.Vector(*v)) - o0
    axis_dirs[nm] = d
    L("[2] 斧头局部 %s 世界方向 = (%.3f, %.3f, %.3f)  与世界上向夹角 %.1f°" % (
        nm, d.x, d.y, d.z, math.degrees(math.acos(max(-1.0, min(1.0, d.z))))))

b = sm.get_bounds(); lo = b.origin - b.box_extent; hi = b.origin + b.box_extent
cs = [t.transform_location(unreal.Vector(lo.x if i == 0 else hi.x,
                                         lo.y if j == 0 else hi.y,
                                         lo.z if k == 0 else hi.z))
      for i in (0, 1) for j in (0, 1) for k in (0, 1)]
ax_min = (min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))
ax_max = (max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs))
L("[3] 斧头世界 AABB  X %.1f~%.1f  Y %.1f~%.1f  Z %.1f~%.1f" % (
    ax_min[0], ax_max[0], ax_min[1], ax_max[1], ax_min[2], ax_max[2]))
L("[4] 斧头最低点 z = %.1f  (要求 >= 0，不得插地)  -> %s" % (
    ax_min[2], "PASS" if ax_min[2] >= 0 else "FAIL"))

skb = mesh.get_editor_property("skeletal_mesh_asset").get_bounds()
mt = mesh.get_world_transform()
mlo = skb.origin - skb.box_extent; mhi = skb.origin + skb.box_extent
mcs = [mt.transform_location(unreal.Vector(mlo.x if i == 0 else mhi.x,
                                           mlo.y if j == 0 else mhi.y,
                                           mlo.z if k == 0 else mhi.z))
       for i in (0, 1) for j in (0, 1) for k in (0, 1)]
c_min = (min(c.x for c in mcs), min(c.y for c in mcs), min(c.z for c in mcs))
c_max = (max(c.x for c in mcs), max(c.y for c in mcs), max(c.z for c in mcs))
L("[5] 角色世界 AABB  X %.1f~%.1f  Y %.1f~%.1f  Z %.1f~%.1f" % (
    c_min[0], c_max[0], c_min[1], c_max[1], c_min[2], c_max[2]))

def ov(a_min, a_max, b_min, b_max):
    d = [max(0.0, min(a_max[i], b_max[i]) - max(a_min[i], b_min[i])) for i in range(3)]
    return d[0] * d[1] * d[2]

vol_axe = (ax_max[0]-ax_min[0])*(ax_max[1]-ax_min[1])*(ax_max[2]-ax_min[2])
inter = ov(ax_min, ax_max, c_min, c_max)
L("[6] 斧头 AABB 与角色 AABB 重叠体积 = %.0f cm³  占斧头包围盒 %.1f%% (修复前为 ~22%%)" % (
    inter, 100.0 * inter / max(vol_axe, 1.0)))

L("[7] socket: relRot=(%.3f,%.3f,%.3f) relLoc=(%.5f,%.5f,%.5f)" % (
    r2.pitch, r2.yaw, r2.roll, l2.x, l2.y, l2.z))
L("[8] WeaponAxe 组件: static_mesh=%s  relRot=%s  relLoc=%s  worldScale=%s" % (
    weapon.get_editor_property("static_mesh").get_name(),
    weapon.get_editor_property("relative_rotation"),
    weapon.get_editor_property("relative_location"), weapon.get_world_scale()))
L("    材质 Slot[0] = %s" % (weapon.get_material(0).get_path_name() if weapon.get_material(0) else None))

# ---- 终图 ----
if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Temp"):
    unreal.EditorAssetLibrary.make_directory("/Game/Temp")
rt = unreal.load_asset("/Game/Temp/RT_AxeCap")
if rt is None:
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RT_AxeCap", "/Game/Temp", unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
rt.set_editor_property("size_x", 1200); rt.set_editor_property("size_y", 900)
out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)
sc_class = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
ca = actor_sub.spawn_actor_from_class(sc_class, unreal.Vector(-560.0, -110.0, 150.0), R(0.0, 0.0, 0.0))
ca.set_actor_label("SceneCapture2D_v")
cap = ca.capture_component2d
cap.set_editor_property("texture_target", rt)
cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("fov_angle", 52.0)
cap.set_editor_property("capture_every_frame", False)
for nm, loc, pitch, yaw in [("side", (-560.0, -110.0, 150.0), 0.0, 0.0),
                            ("front", (0.0, -620.0, 160.0), -3.0, 90.0),
                            ("q34", (-430.0, -420.0, 200.0), -8.0, 46.0)]:
    ca.set_actor_location(unreal.Vector(*loc), False, False)
    ca.set_actor_rotation(R(pitch, yaw, 0.0), False)
    time.sleep(0.4)
    cap.capture_scene(); time.sleep(0.8)
    unreal.RenderingLibrary.export_render_target(ew, rt, out, "OK_%s" % nm)
    L("拍 OK_%s" % nm)

# ---- 清场（保留唯一展示角色） ----
for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith(("FIX_", "SceneCapture2D_", "AXE_", "XYZ_", "ABTest_")):
        actor_sub.destroy_actor(a)
L("")
L("关卡剩余 actor: %s" % [a.get_name() for a in actor_sub.get_all_level_actors()])
L("=== DONE ===")
