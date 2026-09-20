import math
import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

OUTER = "darius_godking_mesh_lod0_skeleton"
NEW = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"
WALK = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered"
OLD = "/Game/Character/Darius/Anims_TP_v2/A_Darius_idle1"


def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def report(path, tag):
    a = eal.load_asset(path)
    if not a:
        unreal.log("   %s 加载失败" % path)
        return
    names = [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]
    # 把最外层骨补进来（309 轨道的资产缺它，缺了就会丢掉 ref pose 的 scale=100）
    alln = names + ([OUTER] if OUTER not in names else [])
    lc = {n.lower(): n for n in alln}
    WANT = ["pelvis", "thigh_l", "thigh_r", "foot_l", "foot_r", "ball_l", "ball_r", "head"]
    chains = {}
    for b in WANT:
        k = b if b in alln else lc.get(b.lower())
        if k:
            chains[b] = [str(x) for x in AL.find_bone_path_to_root(a, k)][::-1]
    nf = int(AL.get_num_frames(a))
    objs = [unreal.Name(b) for b in alln]
    poses = AL.get_bone_poses_for_frame(a, objs, 0, False)
    loc = {}
    for i, b in enumerate(alln):
        t = poses[i]
        loc[b] = ((t.translation.x, t.translation.y, t.translation.z),
                  (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
                  (t.scale3d.x, t.scale3d.y, t.scale3d.z))

    def cs(b):
        P, Q, S = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
        for bn in chains.get(b, []):
            k = bn if bn in loc else lc.get(bn.lower())
            tr = loc.get(k) if k else None
            if tr is None:
                continue
            t, q, s = tr
            off = mv(qmat(Q), (t[0] * S[0], t[1] * S[1], t[2] * S[2]))
            P = (P[0] + off[0], P[1] + off[1], P[2] + off[2])
            Q = qmul(Q, q)
            S = (S[0] * s[0], S[1] * s[1], S[2] * s[2])
        return P, S

    o = loc.get(OUTER)
    unreal.log("   ==== %-22s frames=%d tracks=%d  最外层骨 t=%s scale=%s" % (
        tag, nf, len(names),
        [round(v, 4) for v in o[0]] if o else None,
        [round(v, 4) for v in o[2]] if o else None))
    for b in ("pelvis", "ball_l", "ball_r", "foot_l", "foot_r", "head"):
        if b in chains:
            P, S = cs(b)
            unreal.log("      %-8s z=%8.2f   scale=%s" % (b, P[2], [round(v, 3) for v in S]))


for p, t in ((NEW, "新待机 AxeIdle_Layered"), (OLD, "旧待机 Idle_TPv2"), (WALK, "合并走路")):
    report(p, t)
unreal.log("### DONE")
