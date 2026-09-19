# -*- coding: utf-8 -*-
"""诊断 v3：用纯 Python 四元数把局部变换逐级复合，算出关键关节的**组件空间**坐标。
判据与 G2 一致：只看关节位置，不依赖骨骼朝向约定。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary


# ---------------------------------------------------------------- 纯 python 变换
def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def mm(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def tr_of(t):
    return (t.translation.x, t.translation.y, t.translation.z), (t.rotation.x, t.rotation.y,
                                                                 t.rotation.z, t.rotation.w)


def compose_world(chain, locals_):
    """chain = [根, ..., 骨]；locals_ = {bone: (t, q)}，返回该骨的世界位置。"""
    M = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    P = (0.0, 0.0, 0.0)
    for bn in chain:
        t, q = locals_[bn]
        rt = mv(M, t)
        P = (P[0] + rt[0], P[1] + rt[1], P[2] + rt[2])
        M = mm(M, qmat(q))
    return P


def world_pos(anim, bone, frame):
    path = AL.find_bone_path_to_root(anim, bone)
    chain = [str(x) for x in path]
    if not chain or chain[-1] != "root":
        pass
    locs = {}
    for bn in chain:
        locs[bn] = tr_of(AL.get_bone_pose_for_frame(anim, bn, frame, False))
    return chain, compose_world(chain, locs)


def report(pkg, bones, frames=(0,)):
    a = eal.load_asset(pkg)
    if a is None:
        LW("  %s NOT FOUND" % pkg)
        return
    L("")
    L("--- %s" % pkg.split("/")[-1])
    ok_bones = []
    for b in bones:
        try:
            if AL.does_bone_name_exist(a, b):
                ok_bones.append(b)
        except Exception:
            pass
    if not ok_bones:
        LW("    这些骨名都不存在: %s" % bones)
        return
    for f in frames:
        L("    第 %d 帧:" % f)
        for b in ok_bones:
            try:
                chain, p = world_pos(a, b, f)
                L("      %-16s 世界位置 = (%8.2f, %8.2f, %8.2f)   路径长 %d" % (b, p[0], p[1], p[2], len(chain)))
            except Exception as ex:
                LW("      %-16s 失败: %s" % (b, str(ex)[:80]))
    try:
        L("    根骨链示例: %s" % [str(x) for x in AL.find_bone_path_to_root(a, ok_bones[0])])
    except Exception as ex:
        LW("    路径查询失败: %s" % str(ex)[:100])


L("################ 1. 本轮新产物（目标骨架）")
report("/Game/Character/Darius/Anims_TP/A_Darius_idle1",
       ["pelvis", "spine_01", "foot_l", "foot_r", "head"], frames=(0, 32))
report("/Game/Character/Darius/Anims_TP/A_Darius_run",
       ["pelvis", "foot_l", "foot_r"], frames=(0, 17))

L("")
L("################ 2. 旧一套（同一目标骨架，作对照）")
report("/Game/Character/Darius/Anims/A_Darius_Idle1_TP",
       ["pelvis", "spine_01", "foot_l", "foot_r", "head"], frames=(0, 32))
report("/Game/Character/Darius/Anims/A_Darius_Run_TP",
       ["pelvis", "foot_l", "foot_r"], frames=(0, 17))

L("")
L("################ 3. 源侧（源骨架）")
report("/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_idle1",
       ["Pelvis", "L_Foot", "R_Foot", "Head"], frames=(0,))

L("")
L("################ 4. 目标骨架 rest pose 的 pelvis 世界位置（对照基线）")
sk = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
if sk:
    try:
        L("  mesh 骨架名 = %s" % sk.get_editor_property("skeleton"))
    except Exception:
        pass
L("=== DONE ===")
