import math
import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

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


def raw_chain(anim, bone):
    return [str(x) for x in AL.find_bone_path_to_root(anim, bone)]


def build(anim):
    names = [str(n) for n in anim.controller.get_model_interface().get_bone_track_names()]
    chains = {}
    for b in names:
        try:
            chains[b] = raw_chain(anim, b)[::-1]
        except Exception:
            chains[b] = []
    parents = {}
    for b in names:
        rc = raw_chain(anim, b)
        parents[b] = rc[1] if len(rc) > 1 else None
    return names, chains, parents


up_names, up_chains, up_parents = build(up)
low_names, low_chains, low_parents = build(low)

unreal.log("### 关键骨父级（修正版）")
for b in ("pelvis", "spine_01", "head", "hand_r", "weapon_jnt", "weapon_jnt_offset",
          "weapon_jnt_r", "sync_joint", "godking_hair_chain_01", "godking_hair_chain_02",
          "camera_main", "thigh_l", "ball_l"):
    unreal.log("   %-30s parent=%-30s" % (b, up_parents.get(b, "?")))


def cs_all(anim, chains, f):
    out = {}
    for b, chain in chains.items():
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
        out[b] = p
    return out


common = sorted(set(up_names) & set(low_names))
cu = cs_all(up, up_chains, 0)
cl = cs_all(low, low_chains, 0)

rows = []
for b in common:
    du = cu[b]
    dl = cl[b]
    dz = du[2] - dl[2]
    d = math.sqrt(sum((x - y) ** 2 for x, y in zip(du, dl)))
    rows.append((abs(dz), d, b, du, dl))

rows.sort(reverse=True)
unreal.log("### frame0 component-space 差异最大的 25 根骨")
unreal.log("   %-34s %8s %8s | UP z / LOW z" % ("bone", "|dz|", "dist"))
for adz, d, b, du, dl in rows[:25]:
    unreal.log("   %-34s %8.1f %8.1f | %7.2f / %7.2f" % (b, adz, d, du[2], dl[2]))

unreal.log("### UP 里 z 最低的 12 根骨")
for b in sorted(common, key=lambda x: cu[x][2])[:12]:
    unreal.log("   %-34s z=%8.2f  %s" % (b, cu[b][2], [round(v, 1) for v in cu[b]]))
unreal.log("### LOW 里 z 最低的 12 根骨")
for b in sorted(common, key=lambda x: cl[x][2])[:12]:
    unreal.log("   %-34s z=%8.2f  %s" % (b, cl[b][2], [round(v, 1) for v in cl[b]]))

unreal.log("### 每帧统计：UP 全身最低骨 z")
nf = AL.get_num_frames(up)
for f in range(0, nf + 1, 8):
    cf = cs_all(up, up_chains, f)
    b = min(common, key=lambda x: cf[x][2])
    unreal.log("   f%-3d 最低骨 %-30s z=%7.2f" % (f, b, cf[b][2]))
