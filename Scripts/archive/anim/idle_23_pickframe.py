import math
import unreal

AL = unreal.AnimationLibrary

WALK = "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"
a = unreal.load_object(None, WALK)
names = [str(x) for x in a.controller.get_model_interface().get_bone_track_names()]
lc = {n.lower(): n for n in names}
WANT = ["pelvis", "clavicle_l", "clavicle_r", "thigh_l", "thigh_r", "calf_l", "calf_r",
        "foot_l", "foot_r", "ball_l", "ball_r", "toe_l", "toe_r"]
chains = {}
for b in WANT:
    k = b if b in names else lc.get(b.lower())
    chains[b] = [str(x) for x in AL.find_bone_path_to_root(a, k)][::-1]
nf = int(AL.get_num_frames(a))
objs = [unreal.Name(b) for b in names]


def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def qmul(p, q):
    ax, ay, az, aw = p
    bx, by, bz, bw = q
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


rows = []
for f in range(nf + 1):
    poses = AL.get_bone_poses_for_frame(a, objs, f, False)
    loc = {}
    for i, b in enumerate(names):
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
        return P
    # ★ 自校准：角色右轴 = 锁骨线（clavicle_r - clavicle_l）的水平分量
    sv = tuple(cs("clavicle_r")[i] - cs("clavicle_l")[i] for i in range(3))
    n = math.hypot(sv[0], sv[1]) or 1.0
    right = (sv[0] / n, sv[1] / n)
    pel = cs("pelvis")

    def lat(p):
        return (p[0] - pel[0]) * right[0] + (p[1] - pel[1]) * right[1]
    bl, br = cs("ball_l"), cs("ball_r")
    sep = math.dist(bl, br)
    rows.append((f, lat(bl), lat(br), sep, bl[2], br[2]))

rows_sorted = sorted(rows, key=lambda r: abs(r[3] - 45.0))
unreal.log("### 目标：脚间距接近 45cm、左右次序正确、两脚都贴地")
unreal.log("   %-4s %9s %9s %9s %9s %9s %s" % ("f", "lat_l", "lat_r", "间距", "ballL_z", "ballR_z", "判定"))
for r in rows_sorted[:14]:
    ok = (r[1] < 0 < r[2]) and abs(r[4] - r[5]) < 6.0
    unreal.log("   %-4d %9.1f %9.1f %9.1f %9.1f %9.1f %s" % (
        r[0], r[1], r[2], r[3], r[4], r[5], "★可用" if ok else ""))
unreal.log("### 全部帧的间距分布")
unreal.log("   min=%.1f max=%.1f" % (min(r[3] for r in rows), max(r[3] for r in rows)))
unreal.log("### DONE")
