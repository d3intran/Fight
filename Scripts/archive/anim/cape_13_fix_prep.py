import math
import unreal

AL = unreal.AnimationLibrary
unreal.log("BlueprintGraphPin: %s" % [m for m in dir(unreal.BlueprintGraphPin) if not m.startswith("_")])

abp = unreal.load_object(None, "/Game/Character/Darius/Blueprints/ABP_Darius_Test")
unreal.log("############ 1. AnimGraph 各节点的输入 pin 与连线")
for g in AL.get_animation_graphs(abp):
    if g.get_name() != "AnimGraph":
        continue
    for n in g.get_graph_nodes_of_class(unreal.AnimGraphNode_Base):
        cn = n.get_class().get_name().replace("AnimGraphNode_", "")
        try:
            pins = n.list_input_pins()
        except Exception as ex:
            unreal.log("   %-24s list_input_pins ERR %s" % (cn, str(ex)[:50]))
            continue
        for p in pins:
            pn = str(p.get_pin_name())
            names = []
            try:
                for x in p.list_connected_pins():
                    try:
                        names.append("%s.%s" % (x.get_owning_node().get_name(), x.get_pin_name()))
                    except Exception:
                        names.append("?")
            except Exception as ex:
                names = ["ERR %s" % str(ex)[:40]]
            unreal.log("   %-24s in:%-16s <- %s" % (cn, pn, names))

unreal.log("############ 2. 斧头网格的局部尺寸（确认长轴/刃向）")
sm = unreal.load_object(None, "/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
if not sm:
    for cand in ("/Game/Character/Darius/SM_Darius_GodKing_Axe",
                 "/Game/Character/Darius/Weapon/SM_Darius_GodKing_Axe",
                 "/Game/Weapons/SM_Darius_GodKing_Axe"):
        sm = unreal.load_object(None, cand)
        if sm:
            unreal.log("   找到: %s" % cand)
            break
unreal.log("   sm = %s" % sm)
if sm:
    try:
        b = sm.get_bounds()
        unreal.log("   bounds box_extent = %s  sphere_r=%.1f" % (
            [round(v, 1) for v in (b.box_extent.x, b.box_extent.y, b.box_extent.z)], b.sphere_radius))
    except Exception as ex:
        unreal.log("   bounds ERR %s" % str(ex)[:60])
    try:
        unreal.log("   材质槽 = %s" % [str(s.get_editor_property("material_slot_name"))
                                      for s in sm.get_editor_property("static_materials")])
    except Exception as ex:
        unreal.log("   材质 ERR %s" % str(ex)[:50])

unreal.log("############ 3. 走路下半身逐帧（**修正大小写**，component 空间 面朝 -X、右 = -Y）")


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


def analyse(path, tag, only=None):
    a = unreal.load_object(None, path)
    if not a:
        unreal.log("   %s 载入失败" % path)
        return
    names = [str(x) for x in a.controller.get_model_interface().get_bone_track_names()]
    lc = {n.lower(): n for n in names}
    WANT = ["pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r",
            "ball_l", "ball_r", "toe_l", "toe_r", "head"]
    chains = {}
    for b in WANT:
        k = b if b in names else lc.get(b.lower())
        if k:
            chains[b] = [str(x) for x in AL.find_bone_path_to_root(a, k)][::-1]
    nf = int(AL.get_num_frames(a))
    objs = [unreal.Name(b) for b in names]
    frames = only if only is not None else list(range(nf + 1))
    unreal.log("   ==== %s (%d 帧)  f | 次序差 前后差 最窄侧距 | ball_z(l/r) | lat_l/lat_r | fwd_l/fwd_r" % (tag, nf))
    for f in frames:
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
        pel = cs("pelvis")
        lat = lambda p: -(p[1] - pel[1])
        fwd = lambda p: -(p[0] - pel[0])
        ll, lr = lat(cs("ball_l")), lat(cs("ball_r"))
        fl, fr = fwd(cs("ball_l")), fwd(cs("ball_r"))
        zl, zr = cs("ball_l")[2], cs("ball_r")[2]
        unreal.log("      f%-3d %8.1f %7.1f %8.1f | %6.1f/%6.1f | %+7.1f/%+7.1f | %+7.1f/%+7.1f" % (
            f, lr - ll, abs(fl - fr), min(abs(ll), abs(lr)), zl, zr, ll, lr, fl, fr))


analyse("/Game/Character/Darius/Anims/A_Darius_Walk_Layered", "Walk_Layered",
        only=list(range(0, 51, 5)))
analyse("/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered", "新待机", only=[0, 32])
unreal.log("############ DONE")
