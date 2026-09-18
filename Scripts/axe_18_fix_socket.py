# -*- coding: utf-8 -*-
"""握持修正 v3：只改 hand_rSocket 的 relative_rotation / relative_location，两朝向对比渲染"""
import unreal, os, time, math

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()
ML = unreal.MathLibrary

if les.is_in_play_in_editor():
    les.editor_request_end_play(); L("!! PIE"); raise SystemExit

def R(p, y, r):
    return unreal.Rotator(pitch=p, yaw=y, roll=r)

def basis(rot):
    return (ML.get_forward_vector(rot), ML.get_right_vector(rot), ML.get_up_vector(rot))

def basis_err(a, b):
    e = 0.0
    for v1, v2 in zip(a, b):
        e += (v1.x - v2.x) ** 2 + (v1.y - v2.y) ** 2 + (v1.z - v2.z) ** 2
    return e

def solve_left(target_basis, right_rot):
    best = [0.0, 0.0, 0.0]; best_e = 1e18
    for step in (60.0, 20.0, 6.0, 2.0, 0.6, 0.2, 0.06, 0.02):
        improved = True; guard = 0
        while improved and guard < 40:
            improved = False; guard += 1
            for axis in range(3):
                for sgn in (1.0, -1.0):
                    cand = list(best); cand[axis] += sgn * step
                    e = basis_err(basis(ML.compose_rotators(R(*cand), right_rot)), target_basis)
                    if e < best_e - 1e-12:
                        best_e = e; best = cand; improved = True
    return R(*best), best_e

def solve_right(target_basis, left_rot):
    best = [0.0, 0.0, 0.0]; best_e = 1e18
    for step in (60.0, 20.0, 6.0, 2.0, 0.6, 0.2, 0.06, 0.02):
        improved = True; guard = 0
        while improved and guard < 40:
            improved = False; guard += 1
            for axis in range(3):
                for sgn in (1.0, -1.0):
                    cand = list(best); cand[axis] += sgn * step
                    e = basis_err(basis(ML.compose_rotators(left_rot, R(*cand))), target_basis)
                    if e < best_e - 1e-12:
                        best_e = e; best = cand; improved = True
    return R(*best), best_e

for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith(("BP_DariusCharacter", "FIX_", "SceneCapture2D_",
                     "StaticMeshActor_0", "StaticMeshActor_5", "StaticMeshActor_6")):
        actor_sub.destroy_actor(a)

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
probe = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), R(0.0, 180.0, 0.0))
probe.set_actor_label("FIX_probe")
mesh = probe.get_component_by_class(unreal.SkeletalMeshComponent)
weapon = None
for c in probe.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name():
        weapon = c
W0 = weapon.get_world_rotation()
sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
sock = sk.find_socket(unreal.Name("hand_rSocket"))
R0 = sock.get_editor_property("relative_rotation")
Pw, e_pw = solve_left(basis(W0), R0)
L("Pw=(%.4f,%.4f,%.4f) 残差=%.3e  自洽=%.3e" % (
    Pw.pitch, Pw.yaw, Pw.roll, e_pw, basis_err(basis(ML.compose_rotators(Pw, R0)), basis(W0))))

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
ca.set_actor_label("SceneCapture2D_fix")
cap = ca.capture_component2d
cap.set_editor_property("texture_target", rt)
cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("fov_angle", 52.0)
cap.set_editor_property("capture_every_frame", False)

def measure_and_shoot(tag):
    for a in actor_sub.get_all_level_actors():
        if a.get_name().startswith(("FIX_probe", "FIX_show")):
            actor_sub.destroy_actor(a)
    act = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), R(0.0, 180.0, 0.0))
    act.set_actor_label("FIX_show")
    w = None
    for c in act.get_components_by_class(unreal.StaticMeshComponent):
        if "Weapon" in c.get_name():
            w = c
    t = w.get_world_transform()
    o0 = t.transform_location(unreal.Vector(0, 0, 0))
    L("--- %s  weapon world loc=(%.1f,%.1f,%.1f)" % (tag, t.translation.x, t.translation.y, t.translation.z))
    for nm, v in (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))):
        d = t.transform_location(unreal.Vector(*v)) - o0
        L("      local %s 世界方向 (%.3f,%.3f,%.3f) 与上向夹角 %.1f°" % (
            nm, d.x, d.y, d.z, math.degrees(math.acos(max(-1.0, min(1.0, d.z))))))
    sm = w.get_editor_property("static_mesh"); b = sm.get_bounds()
    lo = b.origin - b.box_extent; hi = b.origin + b.box_extent
    cs = [t.transform_location(unreal.Vector(lo.x if i == 0 else hi.x,
                                             lo.y if j == 0 else hi.y,
                                             lo.z if k == 0 else hi.z))
          for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    xs = [c.x for c in cs]; ys = [c.y for c in cs]; zs = [c.z for c in cs]
    L("      斧头世界 AABB X %.0f~%.0f Y %.0f~%.0f Z %.0f~%.0f" % (
        min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    for nm, loc, pitch, yaw in [("side", (-560.0, -110.0, 150.0), 0.0, 0.0),
                                ("front", (0.0, -620.0, 160.0), -3.0, 90.0)]:
        ca.set_actor_location(unreal.Vector(*loc), False, False)
        ca.set_actor_rotation(R(pitch, yaw, 0.0), False)
        time.sleep(0.4)
        cap.capture_scene(); time.sleep(0.8)
        unreal.RenderingLibrary.export_render_target(ew, rt, out, "FIX_%s_%s" % (tag, nm))
        L("      拍 FIX_%s_%s" % (tag, nm))

Ax = unreal.Vector(1.0, 0.0, 0.0)
for tag, Ay in (("A_up", unreal.Vector(0.0, -0.2588, 0.9659)),
                ("B_down", unreal.Vector(0.0, 0.2588, -0.9659))):
    Wt = ML.make_rot_from_xy(Ax, Ay)
    tb = basis(Wt)
    Rn, e = solve_right(tb, Pw)
    chk = basis_err(basis(ML.compose_rotators(Pw, Rn)), tb)
    ry = ML.get_right_vector(Rn)
    rloc = unreal.Vector(ry.x * 0.215, ry.y * 0.215, ry.z * 0.215)
    sock.set_editor_property("relative_rotation", Rn)
    sock.set_editor_property("relative_location", rloc)
    sock.set_editor_property("relative_scale", unreal.Vector(0.01, 0.01, 0.01))
    L("")
    L(">>> %s  Wt=(%.2f,%.2f,%.2f)  Rs=(%.4f,%.4f,%.4f)  rLoc=(%.5f,%.5f,%.5f) 残差=%.3e 校验=%.3e" % (
        tag, Wt.pitch, Wt.yaw, Wt.roll, Rn.pitch, Rn.yaw, Rn.roll, rloc.x, rloc.y, rloc.z, e, chk))
    measure_and_shoot(tag)

L("")
L("=== DONE （未保存） ===")
