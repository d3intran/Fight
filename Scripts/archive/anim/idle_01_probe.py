import math
import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

ABP = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
abp = eal.load_asset(ABP)

unreal.log("############ 1. ABP 图与节点")
graphs = AL.get_animation_graphs(abp)
unreal.log("   图数 = %d : %s" % (len(graphs), [g.get_name() for g in graphs]))
for g in graphs:
    try:
        nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_Base)
    except Exception as ex:
        unreal.log("   图 %-14s 取节点失败 %s" % (g.get_name(), ex))
        continue
    counts = {}
    for n in nodes:
        cn = n.get_class().get_name().replace("AnimGraphNode_", "")
        counts[cn] = counts.get(cn, 0) + 1
    unreal.log("   图 %-14s 节点: %s" % (g.get_name(), counts))

for g in graphs:
    for cls in (unreal.AnimGraphNode_SequencePlayer, unreal.AnimGraphNode_BlendSpacePlayer):
        try:
            nodes = g.get_graph_nodes_of_class(cls)
        except Exception:
            nodes = []
        for n in nodes:
            nd = n.get_editor_property("node")
            a = nd.get_editor_property("sequence" if cls is unreal.AnimGraphNode_SequencePlayer
                                       else "blend_space")
            unreal.log("   %-14s %-18s -> %s" % (g.get_name(),
                                                 cls.get_class().get_name() if False else cls.__name__,
                                                 a.get_path_name() if a else None))

unreal.log("############ 2. 物理资产")
for p in ("/Game/Character/Darius/SK_Darius_GodKing_Physics",
          "/Game/Character/Darius/SK_Darius_GodKing"):
    a = eal.load_asset(p)
    unreal.log("   %s -> %s" % (p, a.get_class().get_name() if a else None))
pa = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Physics")
if pa:
    try:
        bs = pa.get_editor_property("skeletal_body_setups")
        names = [str(b.get_editor_property("bone_name")) for b in bs]
        unreal.log("   刚体数 = %d" % len(names))
        unreal.log("   骨名 = %s" % names[:40])
        cape = [n for n in names if "cape" in n.lower() or "cloth" in n.lower()]
        unreal.log("   披风相关 = %s" % cape)
    except Exception as ex:
        unreal.log("   body setups ERR %s" % ex)
    try:
        cs = pa.get_editor_property("constraint_setup")
        unreal.log("   约束 = %s" % (cs.get_class().get_name() if cs else None))
    except Exception as ex:
        unreal.log("   constraint ERR %s" % ex)

unreal.log("############ 3. 网格上的物理/布料设置")
sk = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
for prop in ("physics_asset", "cloth_lod_bias_mode", "skeletal_mesh_source"):
    try:
        unreal.log("   %-24s = %s" % (prop, sk.get_editor_property(prop)))
    except Exception as ex:
        unreal.log("   %-24s ERR %s" % (prop, str(ex)[:60]))


# ------------------------------------------------ 姿态朝向测量
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


def ang_deg(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(nrm(a), nrm(b))))))


WATCH = ("pelvis", "spine_03", "head", "thigh_l", "thigh_r", "foot_l", "foot_r",
         "clavicle_l", "clavicle_r", "hand_l", "hand_r", "ball_l", "ball_r", "toe_l", "toe_r")


def analyse(path, tag):
    a = eal.load_asset(path)
    if not a:
        unreal.log("   %s 加载失败" % path)
        return
    names = [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]
    lc = {n.lower(): n for n in names}
    chains = {}
    for b in WATCH:
        key = b if b in names else lc.get(b.lower())
        if key:
            chains[b] = [str(x) for x in AL.find_bone_path_to_root(a, key)][::-1]
    nf = int(AL.get_num_frames(a))
    objs = [unreal.Name(b) for b in names]
    unreal.log("   ---- %s  (%d 帧)" % (tag, nf))
    up_ang, roll_ang, yaw_ang = [], [], []
    for f in range(0, nf + 1, max(1, nf // 8)):
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
                key = bn if bn in loc else lc.get(bn.lower())
                tr = loc.get(key) if key else None
                if tr is None:
                    continue
                t, q, s = tr
                off = mv(qmat(Q), (t[0] * S[0], t[1] * S[1], t[2] * S[2]))
                P = (P[0] + off[0], P[1] + off[1], P[2] + off[2])
                Q = qmul(Q, q)
                S = (S[0] * s[0], S[1] * s[1], S[2] * s[2])
            return P

        pel, sp3, hd = cs("pelvis"), cs("spine_03"), cs("head")
        hl, hr = cs("thigh_l"), cs("thigh_r")
        fl, fr = cs("foot_l"), cs("foot_r")
        up = nrm(sub(hd, pel))
        right = nrm(sub(hr, hl))
        fwd = nrm(cross(up, right))
        up_ang.append(ang_deg(up, (0, 0, 1)))
        roll_ang.append(ang_deg(right, (1, 0, 0)))
        yaw_ang.append(ang_deg(fwd, (0, 1, 0)))
        if f % max(1, nf // 4) == 0:
            unreal.log("      f%-3d up=%s right=%s fwd=%s  pelvis_z=%.1f head_z=%.1f"
                       % (f, [round(v, 3) for v in up], [round(v, 3) for v in right],
                          [round(v, 3) for v in fwd], pel[2], hd[2]))
    unreal.log("      躯干「竖直度」偏离世界 Z：均值 %.2f° 最大 %.2f°"
               % (sum(up_ang) / len(up_ang), max(up_ang)))
    unreal.log("      髋轴偏离世界 X（侧倾）：均值 %.2f° 最大 %.2f°"
               % (sum(roll_ang) / len(roll_ang), max(roll_ang)))
    unreal.log("      前向偏离世界 Y（偏航）：均值 %.2f° 最大 %.2f°"
               % (sum(yaw_ang) / len(yaw_ang), max(yaw_ang)))


unreal.log("############ 4. 姿态朝向（up=躯干竖直度 / right=髋轴 / fwd=前向）")
for p, t in (("/Game/Character/Darius/Anims_TP_v2/A_Darius_idle1", "Idle (Anims_TP_v2)"),
             ("/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered", "Merged Walk"),
             ("/Game/Character/Darius/Anims/A_Darius_Walk_Layered", "Walk_Layered")):
    analyse(p, t)
unreal.log("############ DONE")
