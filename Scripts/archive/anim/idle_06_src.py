import math
import os
import unreal

AL = unreal.AnimationLibrary


def LO(p):
    try:
        return unreal.load_object(None, p)
    except Exception:
        return None


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


def sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def nrm(v):
    n = math.sqrt(dot(v, v))
    return tuple(x / n for x in v) if n > 1e-9 else (0.0, 0.0, 0.0)


SEGS = [("pelvis", "spine_01"), ("spine_01", "spine_02"), ("spine_02", "spine_03"),
        ("spine_03", "neck_01"), ("neck_01", "head")]
EXTRA = ["thigh_l", "thigh_r", "foot_l", "foot_r", "ball_l", "ball_r",
         "cape_chain_01_m", "cape_chain_05_m", "cape_chain_09_m",
         "cape_chain_01_l", "cape_chain_09_l", "cape_chain_01_r", "cape_chain_09_r"]
WANT = sorted(set([b for s in SEGS for b in s] + EXTRA))


def analyse(path, tag):
    a = LO(path)
    if not a:
        unreal.log("   %s 加载失败" % path)
        return
    names = [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]
    lc = {n.lower(): n for n in names}
    chains = {}
    for b in WANT:
        k = b if b in names else lc.get(b.lower())
        if k:
            chains[b] = [str(x) for x in AL.find_bone_path_to_root(a, k)][::-1]
    nf = int(AL.get_num_frames(a))
    objs = [unreal.Name(b) for b in names]
    unreal.log("   ==== %s（%d 帧，%d 轨道）" % (tag, nf, len(names)))
    for f in (0, nf // 2):
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

        right = nrm(sub(cs("thigh_r"), cs("thigh_l"))) if ("thigh_l" in chains and "thigh_r" in chains) else (1, 0, 0)
        fwd = nrm(cross(right, (0, 0, 1)))     # component 空间：面朝 -Y，forward = right × up
        seg = []
        for a_, b_ in SEGS:
            v = sub(cs(b_), cs(a_))
            h = math.sqrt(v[0] ** 2 + v[1] ** 2)
            tilt = math.degrees(math.atan2(h, v[2])) if abs(v[2]) > 1e-6 else 90.0
            d = nrm((v[0], v[1], 0.0)) if h > 1e-6 else (0, 0, 0)
            seg.append("%s %5.1f°(前%+.2f 右%+.2f)" % (b_, tilt, dot(d, fwd), dot(d, right)))
        unreal.log("      f%-3d %s" % (f, " | ".join(seg)))
        pel = cs("pelvis")
        row = []
        for c in ("cape_chain_01_m", "cape_chain_05_m", "cape_chain_09_m"):
            if c in chains:
                v = sub(cs(c), pel)
                d = nrm((v[0], v[1], 0.0))
                row.append("%s 水平%.0f 前%+.2f 右%+.2f 垂%+.0f" % (
                    c[-5:], math.sqrt(v[0] ** 2 + v[1] ** 2), dot(d, fwd), dot(d, right), v[2]))
        unreal.log("           披风 %s" % " | ".join(row))
        if "foot_l" in chains and "ball_l" in chains:
            unreal.log("           脚底 ball_l z=%.1f  ball_r z=%.1f  pelvis z=%.1f" % (
                cs("ball_l")[2], cs("ball_r")[2], pel[2]))


unreal.log("############ 候选待机源的姿态质量")
analyse("/Game/Character/Darius/Anims/A_Darius_AxeIdle_Mixamo", "AxeIdle_Mixamo")
analyse("/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo", "AxeWalk_Mixamo")
analyse("/Game/Character/Darius/Anims_TP_v2/A_Darius_idle1", "Idle TP_v2（当前用的）")
analyse("/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered", "Merged Walk（对照）")

unreal.log("############ 本机有没有可用的 Mixamo 待机源")
for d in ("E:/UE/Assets", "E:/UE/Assets/mixamo_src", "E:/UE/Fight/Content/Mixamo",
          "E:/UE/Fight/Content/Mixamo_Upright"):
    if not os.path.isdir(d):
        unreal.log("   %s 不存在" % d)
        continue
    fs = sorted(f for f in os.listdir(d) if f.lower().endswith((".fbx", ".glb", ".gltf")))
    unreal.log("   %-40s %s" % (d, fs))
unreal.log("############ DONE")
