# -*- coding: utf-8 -*-
"""探针：`get_ref_pose_transform` 到底要什么参数、返回什么空间。

`ik_45` 里两种约定（前乘/后乘）算出了**完全相同**的结果，只可能是
`get_ref_pose_transform` 全部返回了单位旋转（我的 except 把失败吞了）。
它是 `USkinnedMeshComponent::GetRefPoseTransform(int32 BoneIndex)` ⇒ 大概率要**索引**。

顺带确认返回的是「父相对局部变换」还是「组件空间变换」——
判据：把整条链的局部变换 FK 起来，看末端是否等于 `get_ref_pose_position`（组件空间位置）。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

MESH_TGT = "/Game/Character/Darius/SK_Darius_GodKing"
PROBE = ["root", "pelvis", "spine_01", "thigh_l", "calf_l", "foot_l"]

sm = eal.load_asset(MESH_TGT)
a = actor_sub.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
a.set_actor_label("Probe_RefPose")
comp = a.get_editor_property("skeletal_mesh_component")
try:
    comp.set_skinned_asset_and_update(sm)
except Exception:
    comp.set_skeletal_mesh(sm)

L("################ 1. 参数形态：骨名 vs 索引")
for b in PROBE[:3]:
    idx = None
    try:
        idx = int(comp.get_bone_index(b))
    except Exception as ex:
        LW("  get_bone_index(%s): %s" % (b, str(ex)[:60]))
    L("  骨 %-12s index=%s" % (b, idx))
    for tag, arg in (("name", b), ("index", idx)):
        try:
            t = comp.get_ref_pose_transform(arg)
            r = t.rotation
            L("     [%s=%r] loc=(%.3f, %.3f, %.3f) rot=(%.4f, %.4f, %.4f, %.4f)"
              % (tag, arg, t.translation.x, t.translation.y, t.translation.z,
                 r.x, r.y, r.z, r.w))
        except Exception as ex:
            LW("     [%s=%r] 失败: %s" % (tag, arg, str(ex)[:90]))

L("")
L("################ 2. 与「动画第 0 帧的局部变换」对比（判断是否同一空间）")
anim = eal.load_asset("/Game/Character/Darius/Anims_TP/A_Darius_idle1")
if anim is None:
    anim = eal.load_asset("/Game/Character/Darius/Anims/A_Darius_idle1")
L("  anim = %s" % (anim.get_name() if anim else "NONE"))
for b in PROBE:
    try:
        t = AL.get_bone_pose_for_frame(anim, b, 0, False)
        r = t.rotation
        L("  %-12s anim_local loc=(%.3f, %.3f, %.3f) rot=(%.4f, %.4f, %.4f, %.4f)"
          % (b, t.translation.x, t.translation.y, t.translation.z, r.x, r.y, r.z, r.w))
    except Exception as ex:
        LW("  %-12s anim 读失败: %s" % (b, str(ex)[:60]))

L("")
L("################ 3. 组件空间位置对照（get_ref_pose_position）")
for b in PROBE:
    try:
        p = comp.get_ref_pose_position(b)
        L("  %-12s ref_pose_position = (%.2f, %.2f, %.2f)" % (b, p.x, p.y, p.z))
    except Exception as ex:
        LW("  %-12s get_ref_pose_position: %s" % (b, str(ex)[:70]))

L("")
L("################ 4. 用局部变换 FK 出来的位置 vs get_ref_pose_position")
IDQ = (0.0, 0.0, 0.0, 1.0)


def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def local(b):
    t = comp.get_ref_pose_transform(b)
    r = t.rotation
    return ((t.translation.x, t.translation.y, t.translation.z), (r.x, r.y, r.z, r.w))


for b in PROBE:
    chain, cur, guard = [], b, 0
    while cur and guard < 600:
        chain.append(cur)
        try:
            p = comp.get_parent_bone(cur)
            cur = str(p) if isinstance(p, str) else comp.get_bone_name(int(p))
        except Exception:
            cur = None
        guard += 1
        if cur in ("None", ""):
            cur = None
    chain = chain[::-1]
    pos, q = (0.0, 0.0, 0.0), IDQ
    for bn in chain:
        t, bq = local(bn)
        off = mv(qmat(q), t)
        pos = (pos[0] + off[0], pos[1] + off[1], pos[2] + off[2])
        q = qmul(q, bq)
    try:
        ref = comp.get_ref_pose_position(b)
        ref = (ref.x, ref.y, ref.z)
        d = sum((pos[i] - ref[i]) ** 2 for i in range(3)) ** 0.5
        L("  %-12s FK=(%.2f, %.2f, %.2f)  ref=(%.2f, %.2f, %.2f)  差=%.3f cm  %s"
          % (b, pos[0], pos[1], pos[2], ref[0], ref[1], ref[2], d,
             "⇒ 局部变换（FK 对得上）" if d < 1.0 else "⇒ 不是局部变换，空间不同"))
    except Exception as ex:
        LW("  %-12s 对照失败: %s" % (b, str(ex)[:70]))

actor_sub.destroy_actor(a)
L("=== DONE ===")
