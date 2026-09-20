import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

BM = {
    "root": "root",
    "pelvis": "pelvis",
    "spine": "spine_03",
    "head": "head",
    "hip_l": "thigh_l", "hip_r": "thigh_r",
    "knee_l": "calf_l", "knee_r": "calf_r",
    "foot_l": "foot_l", "foot_r": "foot_r",
    "toe_l": "ball_l", "toe_r": "ball_r",
    "hand_l": "hand_l", "hand_r": "hand_r",
}


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


def report(path):
    a = eal.load_asset(path)
    unreal.log("================ %s" % path)
    if not a:
        unreal.log_error("  load FAILED")
        return
    nf = int(AL.get_num_frames(a))
    unreal.log("  num_frames = %d   length = %.4f" % (nf, a.get_play_length()))

    paths = {}
    for key, bone in BM.items():
        try:
            paths[bone] = [str(x) for x in AL.find_bone_path_to_root(a, bone)][::-1]
        except Exception as e:
            unreal.log("  bone %s -> ERR %s" % (bone, e))
            paths[bone] = []

    all_bones = sorted(set(b for p in paths.values() for b in p))
    unreal.log("  chain bones = %s" % all_bones)

    local = {}
    for f in range(nf):
        d = {}
        for b in all_bones:
            try:
                t = AL.get_bone_pose_for_frame(a, b, f, False)
                d[b] = ((t.translation.x, t.translation.y, t.translation.z),
                        (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
                        (t.scale3d.x, t.scale3d.y, t.scale3d.z))
            except Exception:
                d[b] = None
        local[f] = d

    def cs(key, f):
        chain = paths.get(BM[key]) or []
        p, q, s = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
        for bn in chain:
            tr = local[f].get(bn)
            if tr is None:
                continue
            t, bq, bs = tr
            off = mv(qmat(q), (t[0] * s[0], t[1] * s[1], t[2] * s[2]))
            p = (p[0] + off[0], p[1] + off[1], p[2] + off[2])
            q = qmul(q, bq)
            s = (s[0] * bs[0], s[1] * bs[1], s[2] * bs[2])
        return p

    keys = ["root", "pelvis", "spine", "head", "foot_l", "foot_r", "toe_l", "toe_r", "hand_l", "hand_r"]
    unreal.log("  --- component-space (cm) at frame 0 / mid / last ---")
    for k in keys:
        if not paths.get(BM[k]):
            continue
        vals = [cs(k, f) for f in (0, nf // 2, nf - 1)]
        unreal.log("  %-8s f0=%s  fmid=%s  flast=%s" % (
            k,
            [round(v, 2) for v in vals[0]],
            [round(v, 2) for v in vals[1]],
            [round(v, 2) for v in vals[2]]))

    unreal.log("  --- per-frame min/max over all frames ---")
    for k in keys:
        if not paths.get(BM[k]):
            continue
        ps = [cs(k, f) for f in range(nf)]
        lo = [min(p[i] for p in ps) for i in range(3)]
        hi = [max(p[i] for p in ps) for i in range(3)]
        unreal.log("  %-8s min=%s  max=%s" % (k, [round(v, 2) for v in lo], [round(v, 2) for v in hi]))

    unreal.log("  --- local translation of root / pelvis ---")
    for b in ("root", "pelvis"):
        if b not in local[0]:
            unreal.log("  %s : no track" % b)
            continue
        samples = []
        for f in range(0, nf, max(1, nf // 8)):
            tr = local[f].get(b)
            samples.append(tr[0] if tr else None)
        unreal.log("  %s local t: %s" % (b, [[round(x, 3) for x in s] if s else None for s in samples]))
    tr = local[0].get("root")
    if tr:
        unreal.log("  root scale = %s" % [round(x, 4) for x in tr[2]])


for p in ("/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo",
          "/Game/Character/Darius/Anims/A_Darius_Walk_Layered",
          "/Game/Character/Darius/Anims/A_Darius_Walk_InPlace"):
    report(p)
