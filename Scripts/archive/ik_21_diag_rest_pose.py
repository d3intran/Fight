# -*- coding: utf-8 -*-
"""诊断 v6：拿骨架 rest pose 当权威基线，判定 pelvis 的 147 到底对不对；
同时查预览网格有没有设。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary


def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def mm(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def mag(v):
    return (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5


SK_PATH = "/Game/Character/Darius/SK_Darius_GodKing_Skeleton"
sk = eal.load_asset(SK_PATH)

L("################ 1. 骨架 rest pose（权威基线）")
rp = None
try:
    rp = sk.get_reference_pose()
    L("  AnimPose 可用方法: %s" % ", ".join(sorted([x for x in dir(rp) if not x.startswith("_")])))
except Exception as ex:
    LW("  get_reference_pose 失败: %s" % str(ex)[:120])


def pose_local(pose, bone):
    for fn in ("get_bone_pose", "get_transform"):
        f = getattr(pose, fn, None)
        if f is None:
            continue
        for args in ((bone,), (bone, unreal.AnimPoseSpaces.LOCAL), (bone,)):
            try:
                return f(*args)
            except Exception:
                continue
    return None


if rp is not None:
    for b in ("darius_godking_mesh_LOD0_Skeleton", "root", "pelvis"):
        t = pose_local(rp, b)
        if t is None:
            LW("  rest %-36s 取不到" % b)
            continue
        tr = t.translation
        L("  rest %-36s T=(%10.4f,%10.4f,%10.4f)  |T|=%.4f  scale=(%.3f,%.3f,%.3f)"
          % (b, tr.x, tr.y, tr.z, mag((tr.x, tr.y, tr.z)),
             t.scale3d.x, t.scale3d.y, t.scale3d.z))

L("")
L("################ 2. 预览网格是否设置")
for fn in ("get_skeleton_preview_mesh", "get_skeleton_additional_preview_meshes"):
    f = getattr(sk, fn, None)
    if f is None:
        continue
    try:
        L("  %s() = %s" % (fn, f()))
    except Exception as ex:
        LW("  %s() 失败: %s" % (fn, str(ex)[:110]))

L("")
L("################ 3. 动画 pelvis 的局部 T vs rest")
def anim_local(pkg, bone, frame=0):
    a = eal.load_asset(pkg)
    t = AL.get_bone_pose_for_frame(a, bone, frame, False)
    tr = t.translation
    return mag((tr.x, tr.y, tr.z)), (tr.x, tr.y, tr.z)


for pkg in ("/Game/Character/Darius/Anims_TP/A_Darius_idle1",
            "/Game/Character/Darius/Anims/A_Darius_Idle1_TP"):
    for b in ("root", "pelvis"):
        try:
            m, t3 = anim_local(pkg, b)
            L("  %-34s %-8s |T|=%10.4f  T=(%9.3f,%9.3f,%9.3f)"
              % (pkg.split("/")[-1], b, m, t3[0], t3[1], t3[2]))
        except Exception as ex:
            LW("  %s %s 失败: %s" % (pkg.split("/")[-1], b, str(ex)[:70]))
L("=== DONE ===")
