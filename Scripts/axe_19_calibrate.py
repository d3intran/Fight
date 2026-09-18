# -*- coding: utf-8 -*-
"""标定 hand_rSocket 的相对旋转组合顺序，再据此求解目标姿态并实测验证"""
import unreal, math

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
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

for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("BP_DariusCharacter", "FIX_")):
        actor_sub.destroy_actor(a)

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
sock = sk.find_socket(unreal.Name("hand_rSocket"))

def measure(rel_rot, rel_loc=None, rel_scale=None):
    if rel_loc is not None:
        sock.set_editor_property("relative_location", rel_loc)
    if rel_scale is not None:
        sock.set_editor_property("relative_scale", rel_scale)
    sock.set_editor_property("relative_rotation", rel_rot)
    for a in actor_sub.get_all_level_actors():
        if a.get_name().startswith(("FIX_show", "FIX_probe")):
            actor_sub.destroy_actor(a)
    act = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), R(0.0, 180.0, 0.0))
    act.set_actor_label("FIX_show")
    w = None
    for c in act.get_components_by_class(unreal.StaticMeshComponent):
        if "Weapon" in c.get_name():
            w = c
    return w.get_world_rotation(), w.get_world_location()

ZERO = unreal.Vector(0.0, 0.0, 0.0)
SCALE = unreal.Vector(0.01, 0.01, 0.01)

Wa, La = measure(R(0.0, 0.0, 0.0), ZERO, SCALE)
L("relRot=(0,0,0)   -> Wa=(%.4f,%.4f,%.4f)  loc=(%.2f,%.2f,%.2f)" % (Wa.pitch, Wa.yaw, Wa.roll, La.x, La.y, La.z))
T = R(0.0, 90.0, 0.0)
Wb, Lb = measure(T, ZERO, SCALE)
L("relRot=(0,90,0)  -> Wb=(%.4f,%.4f,%.4f)" % (Wb.pitch, Wb.yaw, Wb.roll))

order_left = basis_err(basis(ML.compose_rotators(Wa, T)), basis(Wb))
order_right = basis_err(basis(ML.compose_rotators(T, Wa)), basis(Wb))
L("")
L("假设 World = Compose(Parent, Rel):  残差 = %.6f" % order_left)
L("假设 World = Compose(Rel, Parent):  残差 = %.6f" % order_right)
order = "Parent*Rel" if order_left < order_right else "Rel*Parent"
L(">>> 判定组合顺序 = %s" % order)

def solve(target_basis, fixed, mode):
    best = [0.0, 0.0, 0.0]; best_e = 1e18
    for step in (60.0, 20.0, 6.0, 2.0, 0.6, 0.2, 0.06, 0.02, 0.006):
        improved = True; guard = 0
        while improved and guard < 40:
            improved = False; guard += 1
            for axis in range(3):
                for sgn in (1.0, -1.0):
                    cand = list(best); cand[axis] += sgn * step
                    rr = R(*cand)
                    w = ML.compose_rotators(fixed, rr) if mode == "Parent*Rel" else ML.compose_rotators(rr, fixed)
                    e = basis_err(basis(w), target_basis)
                    if e < best_e - 1e-12:
                        best_e = e; best = cand; improved = True
    return R(*best), best_e

# 目标姿态候选：local X -> 世界+X（刃面法线朝侧向）；local Y -> 上（前倾 15°）/ 下
Ax = unreal.Vector(1.0, 0.0, 0.0)
for tag, Ay in (("A_up", unreal.Vector(0.0, -0.2588, 0.9659)),
                ("B_down", unreal.Vector(0.0, 0.2588, -0.9659))):
    Wt = ML.make_rot_from_xy(Ax, Ay)
    tb = basis(Wt)
    Rn, e = solve(tb, Wa, order)
    ry = ML.get_right_vector(Rn)
    rloc = unreal.Vector(ry.x * 0.215, ry.y * 0.215, ry.z * 0.215)
    Wc, Lc = measure(Rn, rloc, SCALE)
    err = basis_err(basis(Wc), tb)
    L("")
    L(">>> %s  目标 Wt=(%.2f,%.2f,%.2f)  Rs=(%.4f,%.4f,%.4f)  rLoc=(%.5f,%.5f,%.5f)" % (
        tag, Wt.pitch, Wt.yaw, Wt.roll, Rn.pitch, Rn.yaw, Rn.roll, rloc.x, rloc.y, rloc.z))
    L("    求解残差=%.3e   实测世界旋转=(%.4f,%.4f,%.4f)  实测姿态误差=%.3e" % (e, Wc.pitch, Wc.yaw, Wc.roll, err))
    L("    实测武器世界位置=(%.1f,%.1f,%.1f)" % (Lc.x, Lc.y, Lc.z))
L("=== DONE ===")
