import math
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.log("PIE = %s" % les.is_in_play_in_editor())

unreal.log("############ 1. AnimGraph 连线（RigidBody 到底有没有接进去）")
abp = unreal.load_object(None, "/Game/Character/Darius/Blueprints/ABP_Darius_Test")
if abp:
    for g in unreal.AnimationLibrary.get_animation_graphs(abp):
        if g.get_name() != "AnimGraph":
            continue
        for n in g.get_graph_nodes_of_class(unreal.AnimGraphNode_Base):
            cn = n.get_class().get_name().replace("AnimGraphNode_", "")
            try:
                outs = [str(p.get_name()) for p in n.list_output_pins()]
            except Exception as ex:
                outs = ["ERR %s" % str(ex)[:40]]
            ins = []
            for pin in outs:
                try:
                    p = n.find_output_pin(pin)
                    lk = p.get_editor_property("linked_to") if p else None
                    ins.append("%s->%s" % (pin, [str(x.get_owning_node().get_name()) for x in lk] if lk else None))
                except Exception as ex:
                    ins.append("%s ERR %s" % (pin, str(ex)[:30]))
            unreal.log("   %-24s out=%s  link=%s" % (cn, outs, ins))

unreal.log("############ 2. 斧头（WeaponAxe 组件）")
gw = ues.get_game_world()
ch = None
if gw:
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        if a.get_class().get_name().startswith("BP_DariusCharacter"):
            ch = a
            break
if ch:
    for c in ch.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name() != "WeaponAxe":
            continue
        unreal.log("   组件 %s" % c.get_name())
        for prop in ("relative_location", "relative_rotation", "relative_scale3d",
                     "absolute_location", "absolute_rotation", "attach_socket_name"):
            try:
                unreal.log("      %-22s = %s" % (prop, c.get_editor_property(prop)))
            except Exception as ex:
                unreal.log("      %-22s ERR %s" % (prop, str(ex)[:50]))
        for sock in ("Blade_Tip", "Blade_Edge", "Pommel", "None"):
            try:
                p = c.get_socket_location(sock)
                unreal.log("      socket %-12s world = %s" % (sock, [round(v, 2) for v in (p.x, p.y, p.z)]))
            except Exception as ex:
                unreal.log("      socket %-12s ERR %s" % (sock, str(ex)[:40]))
        try:
            tip = c.get_socket_location("Blade_Tip")
            pom = c.get_socket_location("Pommel")
            d = (tip.x - pom.x, tip.y - pom.y, tip.z - pom.z)
            n = math.sqrt(sum(v * v for v in d)) or 1.0
            d = tuple(v / n for v in d)
            unreal.log("      刃方向(Blade_Tip-Pommel) = %s" % [round(v, 3) for v in d])
            unreal.log("      与「朝下」(0,0,-1) 夹角 = %.1f°"
                       % math.degrees(math.acos(max(-1, min(1, -d[2])))))
            unreal.log("      与「朝上」(0,0,+1) 夹角 = %.1f°"
                       % math.degrees(math.acos(max(-1, min(1, d[2])))))
        except Exception as ex:
            unreal.log("      刃方向 ERR %s" % str(ex)[:60])

unreal.log("############ 3. 找走路里最适合当「站立站姿」的帧")
WALK = "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"
wa = unreal.load_object(None, WALK)
if wa:
    AL = unreal.AnimationLibrary
    names = [str(x) for x in wa.controller.get_model_interface().get_bone_track_names()]
    nf = int(AL.get_num_frames(wa))
    chains = {}
    for b in ("pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r",
              "ball_l", "ball_r", "toe_l", "toe_r"):
        if b in names:
            chains[b] = [str(x) for x in AL.find_bone_path_to_root(wa, b)][::-1]
    objs = [unreal.Name(b) for b in names]

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

    rows = []
    for f in range(nf + 1):
        poses = AL.get_bone_poses_for_frame(wa, objs, f, False)
        loc = {}
        for i, b in enumerate(names):
            t = poses[i]
            loc[b] = ((t.translation.x, t.translation.y, t.translation.z),
                      (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
                      (t.scale3d.x, t.scale3d.y, t.scale3d.z))

        def cs(b):
            P, Q, S = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
            for bn in chains.get(b, []):
                tr = loc.get(bn)
                if tr is None:
                    continue
                t, q, s = tr
                off = mv(qmat(Q), (t[0] * S[0], t[1] * S[1], t[2] * S[2]))
                P = (P[0] + off[0], P[1] + off[1], P[2] + off[2])
                Q = qmul(Q, q)
                S = (S[0] * s[0], S[1] * s[1], S[2] * s[2])
            return P
        # component 空间：面朝 -X，右 = -Y
        lat = lambda p, r: -(p[1] - r[1])
        fwd = lambda p, r: -(p[0] - r[0])
        pel = cs("pelvis")
        ll, lr = lat(cs("ball_l"), pel), lat(cs("ball_r"), pel)
        fl, fr = fwd(cs("ball_l"), pel), fwd(cs("ball_r"), pel)
        zl, zr = cs("ball_l")[2], cs("ball_r")[2]
        rows.append((f, lr - ll, abs(fl - fr), min(abs(ll), abs(lr)), zl, zr, ll, lr, fl, fr))
    unreal.log("   f    次序差(lat_r-lat_l)  前后差  最窄侧距  球z(l/r)       lat_l/lat_r")
    for r in rows:
        unreal.log("   %-3d %10.1f %12.1f %9.1f   %6.1f/%6.1f  %+7.1f/%+7.1f" % (
            r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
unreal.log("############ DONE")
