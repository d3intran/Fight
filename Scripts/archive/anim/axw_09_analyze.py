import math
import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.log("### 关卡 actor 列表")
for a in eas.get_all_level_actors():
    unreal.log("   %-40s label=%-40s" % (a.get_name(), a.get_actor_label()))

UP_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo"
LOW_PATH = "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"

up = eal.load_asset(UP_PATH)
low = eal.load_asset(LOW_PATH)


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


def chain_of(anim, bone):
    return [str(x) for x in AL.find_bone_path_to_root(anim, bone)][::-1]


PARENTS = {}
for b in [str(n) for n in up.controller.get_model_interface().get_bone_track_names()]:
    c = chain_of(up, b)
    PARENTS[b] = c[1] if len(c) > 1 else None

unreal.log("### 关键骨的父级")
for b in ("root", "pelvis", "spine_01", "spine_03", "head", "hand_r", "weapon_jnt",
          "weapon_jnt_offset", "weapon_jnt_r", "sync_joint", "camera_main",
          "godking_hair_chain_01", "godking_hair_chain_02", "darius_godking_mesh_lod0_skeleton"):
    unreal.log("   %-36s parent = %s" % (b, PARENTS.get(b, "<no track>")))


def cs_of(anim, bone, f):
    chain = chain_of(anim, bone)
    p, q, s = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
    for bn in chain:
        t = AL.get_bone_pose_for_frame(anim, bn, f, False)
        tr = (t.translation.x, t.translation.y, t.translation.z)
        rq = (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w)
        sc = (t.scale3d.x, t.scale3d.y, t.scale3d.z)
        off = mv(qmat(q), (tr[0] * s[0], tr[1] * s[1], tr[2] * s[2]))
        p = (p[0] + off[0], p[1] + off[1], p[2] + off[2])
        q = qmul(q, rq)
        s = (s[0] * sc[0], s[1] * sc[1], s[2] * sc[2])
    return p, q


def ang(a, b):
    d = abs(sum(x * y for x, y in zip(a, b)))
    return math.degrees(2 * math.acos(max(-1.0, min(1.0, d))))


for label, anim, nf in (("UP", up, AL.get_num_frames(up)), ("LOW", low, AL.get_num_frames(low))):
    unreal.log("### %s : weapon_jnt 是否 = weapon_jnt_r (Copy Transforms 假设)" % label)
    for f in (0, nf // 2, nf - 1):
        pw, qw = cs_of(anim, "weapon_jnt", f)
        pr, qr = cs_of(anim, "weapon_jnt_r", f)
        po, qo = cs_of(anim, "weapon_jnt_offset", f)
        d = math.sqrt(sum((a - b) ** 2 for a, b in zip(pw, pr)))
        unreal.log("   f%-3d weapon_jnt=%s  weapon_jnt_r=%s  dist=%.3f cm  rot_diff=%.2f deg"
                   % (f, [round(v, 2) for v in pw], [round(v, 2) for v in pr], d, ang(qw, qr)))
        unreal.log("        weapon_jnt_offset=%s   |off - jnt|=%.3f"
                   % ([round(v, 2) for v in po],
                      math.sqrt(sum((a - b) ** 2 for a, b in zip(po, pw)))))

unreal.log("### 关键骨的 component-space（frame 0）")
for label, anim in (("UP", up), ("LOW", low)):
    for b in ("pelvis", "foot_l", "ball_l", "head", "hand_r", "weapon_jnt"):
        p, q = cs_of(anim, b, 0)
        unreal.log("   %s %-14s %s" % (label, b, [round(v, 2) for v in p]))
