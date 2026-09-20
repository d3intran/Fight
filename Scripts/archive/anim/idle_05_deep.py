import math
import unreal

AL = unreal.AnimationLibrary


def LO(p):
    try:
        return unreal.load_object(None, p)
    except Exception as ex:
        unreal.log("   load ERR %s : %s" % (p, str(ex)[:60]))
        return None


IDLE = "/Game/Character/Darius/Anims_TP_v2/A_Darius_idle1"
MERGED = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered"
AXEWALK = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo"
LOW = "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"

unreal.log("############ 1. 物理资产内容")
pa = LO("/Game/Character/Darius/SK_Darius_GodKing_Physics")
if pa:
    try:
        bs = pa.get_editor_property("skeletal_body_setups")
        names = [str(b.get_editor_property("bone_name")) for b in bs]
        unreal.log("   刚体数 = %d" % len(names))
        unreal.log("   骨名 = %s" % names[:50])
        unreal.log("   含 cape = %s" % [n for n in names if "cape" in n.lower()])
        # 约束
        try:
            cst = pa.get_editor_property("constraint_setup")
            unreal.log("   constraint_setup = %s" % cst)
        except Exception as ex:
            unreal.log("   constraint ERR %s" % str(ex)[:60])
    except Exception as ex:
        unreal.log("   ERR %s" % ex)

unreal.log("############ 2. 网格的物理/布料开关")
sm = LO("/Game/Character/Darius/SK_Darius_GodKing")
if sm:
    for prop in ("physics_asset", "cloth_lod_bias_mode", "enable_per_poly_collision",
                 "support_lod_streaming"):
        try:
            unreal.log("   %-28s = %s" % (prop, sm.get_editor_property(prop)))
        except Exception as ex:
            unreal.log("   %-28s ERR %s" % (prop, str(ex)[:50]))

unreal.log("############ 3. ABP 图节点")
abp = LO("/Game/Character/Darius/Blueprints/ABP_Darius_Test")
if abp:
    graphs = AL.get_animation_graphs(abp)
    unreal.log("   图 = %s" % [g.get_name() for g in graphs])
    for g in graphs:
        try:
            nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_Base)
        except Exception as ex:
            unreal.log("      %s ERR %s" % (g.get_name(), str(ex)[:50]))
            continue
        counts = {}
        for n in nodes:
            cn = n.get_class().get_name().replace("AnimGraphNode_", "")
            counts[cn] = counts.get(cn, 0) + 1
        unreal.log("   图 %-14s %s" % (g.get_name(), counts))


# ---------------------------------------------------------------- 姿态分析
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
CAPES = ["cape_chain_01_m", "cape_chain_05_m", "cape_chain_09_m",
         "cape_chain_01_l", "cape_chain_09_l", "cape_chain_01_r", "cape_chain_09_r"]
WANT = sorted(set([b for s in SEGS for b in s] + CAPES + ["thigh_l", "thigh_r"]))


def analyse(path, tag, frames=None):
    a = LO(path)
    if not a:
        return
    names = [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]
    lc = {n.lower(): n for n in names}
    chains = {}
    for b in WANT:
        k = b if b in names else lc.get(b.lower())
        if k:
            chains[b] = [str(x) for x in AL.find_bone_path_to_root(a, k)][::-1]
    nf = int(AL.get_num_frames(a))
    fl = frames or [0, nf // 2, nf]
    objs = [unreal.Name(b) for b in names]
    unreal.log("   ==== %s（%d 帧）" % (tag, nf))
    for f in fl:
        poses = AL.get_bone_poses_for_frame(a, objs, min(f, nf), False)
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

        # 前向：用髋轴推（component space，静止骨架的髋轴 = 世界 X）
        if "thigh_l" in chains and "thigh_r" in chains:
            right = nrm(sub(cs("thigh_r"), cs("thigh_l")))
            fwd = nrm(cross((0, 0, 1), right))     # component 空间：forward = up × right
        else:
            right, fwd = (1, 0, 0), (0, 1, 0)
        seg = []
        for a_, b_ in SEGS:
            v = sub(cs(b_), cs(a_))
            h = math.sqrt(v[0] ** 2 + v[1] ** 2)
            tilt = math.degrees(math.atan2(h, v[2])) if abs(v[2]) > 1e-6 else 90.0
            d = nrm((v[0], v[1], 0.0)) if h > 1e-6 else (0, 0, 0)
            seg.append("%s %5.1f°(前%+.2f 右%+.2f)" % (b_, tilt, dot(d, fwd), dot(d, right)))
        unreal.log("      f%-3d  %s" % (f, " | ".join(seg)))
        pel = cs("pelvis")
        row = []
        for c in ("cape_chain_01_m", "cape_chain_05_m", "cape_chain_09_m"):
            if c in chains:
                v = sub(cs(c), pel)
                d = nrm((v[0], v[1], 0.0))
                row.append("%s: 水平%.0f 前%+.2f 右%+.2f 垂%+.0f" % (
                    c[-5:], math.sqrt(v[0] ** 2 + v[1] ** 2), dot(d, fwd), dot(d, right), v[2]))
        unreal.log("           披风 %s" % " | ".join(row))


unreal.log("############ 4. 各动画的脊柱/头/披风（component space，前向=up×髋轴）")
analyse(IDLE, "Idle TP_v2", [0, 20, 40, 64])
analyse(AXEWALK, "AxeWalk_Mixamo（披风应为静止）", [0, 20])
analyse(MERGED, "Merged Walk", [0, 25])
analyse(LOW, "Walk_Layered", [0, 25])
unreal.log("############ DONE")
