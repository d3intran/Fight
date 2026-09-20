import unreal

SM = "/Game/Character/Darius/SK_Darius_GodKing"
PA = "/Game/Character/Darius/SK_Darius_GodKing_Physics"
ABP = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
CH = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"

ANIMS = [
    "/Game/Character/Darius/Anims/A_Darius_Walk_Layered",
    "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered",
]


def LO(p):
    try:
        return unreal.load_object(None, p)
    except Exception as ex:
        unreal.log("   load ERR %s | %s" % (p, str(ex)[:60]))
        return None


def RP(o, props, tag):
    for pr in props:
        try:
            unreal.log("   %-34s = %s" % (tag + pr, getattr(o, pr) if not hasattr(o, 'get_editor_property') else o.get_editor_property(pr)))
        except Exception:
            pass


unreal.log("############ 0. API 面")
unreal.log("   BodySetup props: %s" % [m for m in dir(unreal.BodySetup) if 'phys' in m.lower() or 'mass' in m.lower() or 'damp' in m.lower() or 'geom' in m.lower() or 'collis' in m.lower()])
try:
    unreal.log("   SkeletalBodySetup props: %s" % [m for m in dir(unreal.SkeletalBodySetup) if not m.startswith('_')])
except Exception as ex:
    unreal.log("   SBS dir ERR %s" % ex)
unreal.log("   PhysicsAsset fns: %s" % [m for m in dir(unreal.PhysicsAsset) if not m.startswith('_')])
unreal.log("   RigidBody struct props: %s" % [m for m in dir(unreal.RigidBody) if not m.startswith('_')])

sk = LO(SM)
pa = LO(PA)
unreal.log("############ 1. 网格")
if sk:
    unreal.log("   physics_asset = %s" % sk.get_editor_property("physics_asset"))
    skel = sk.get_editor_property("skeleton")
    unreal.log("   skeleton = %s" % skel)
    unreal.log("   num lods = %s" % sk.get_editor_property("lodmax_size") if hasattr(sk, 'get_editor_property') else "")

unreal.log("############ 2. 物理资产刚体：PhysicsType 是核心")
bodies = None
for prop in ("skeletal_body_setups",):
    try:
        bodies = pa.get_editor_property(prop)
        unreal.log("   %s -> len=%d" % (prop, len(bodies)))
    except Exception as ex:
        unreal.log("   %s ERR %s" % (prop, str(ex)[:70]))
if bodies:
    ntype = {}
    for b in bodies:
        try:
            bn = str(b.get_editor_property("bone_name"))
            pt = str(b.get_editor_property("physics_type"))
            ntype[pt] = ntype.get(pt, 0) + 1
            if not bn.startswith("cape"):
                continue
            try:
                agg = b.get_editor_property("aggregate_geom")
                shapes = agg.get_editor_property("shapes")
                sh = []
                for s in shapes:
                    st = str(s.get_editor_property("shape_type"))
                    try:
                        r = round(s.get_editor_property("sphere_radius"), 2)
                    except Exception:
                        r = "?"
                    try:
                        bl = [round(v, 2) for v in (s.get_editor_property("box_extents").x,
                                                    s.get_editor_property("box_extents").y,
                                                    s.get_editor_property("box_extents").z)]
                    except Exception:
                        bl = "?"
                    sh.append("%s r=%s box=%s" % (st, r, bl))
                unreal.log("      %-22s type=%-22s mass=%-8s damp=(%s,%s) col_enum=%s  shapes=%s" % (
                    bn, pt,
                    b.get_editor_property("body_mass") if hasattr(b, 'get_editor_property') else "?",
                    "?", "?",
                    "?", sh))
            except Exception as ex:
                unreal.log("      %-22s type=%-22s (shapes ERR %s)" % (bn, pt, str(ex)[:50]))
        except Exception as ex:
            unreal.log("      body ERR %s" % str(ex)[:60])
    unreal.log("   ★ PhysicsType 统计 = %s" % ntype)

unreal.log("############ 3. 约束（swing/twist 限位）")
try:
    cs = pa.get_constraints(True)
except Exception:
    try:
        cs = pa.get_constraints()
    except Exception as ex:
        cs = []
        unreal.log("   get_constraints ERR %s" % str(ex)[:70])
unreal.log("   约束数 = %d" % len(cs))
for c in cs[:6]:
    try:
        t = c.get_editor_property("instance")
        fields = [m for m in dir(t) if not m.startswith("_")]
        want = [m for m in ("linear_limit_x", "linear_limit_y", "linear_limit_z",
                            "angular_limit_mode", "swing_base_swing_limit", "swing_max_swing_limit",
                            "twist_limit", "linear_springging", "angular_spring", "swing_chain_spring",
                            "twist_spring", "linear_damping", "angular_damping", "break_through") if m in fields]
        vals = {}
        for m in want:
            try:
                vals[m] = t.get_editor_property(m)
            except Exception:
                pass
        unreal.log("   %s<->%s  %s" % (
            c.get_editor_property("constraint_bone1_name"),
            c.get_editor_property("constraint_bone2_name"), vals))
    except Exception as ex:
        unreal.log("   constraint ERR %s" % str(ex)[:70])
try:
    fields = [m for m in dir(unreal.ConstraintInstance) if not m.startswith("_")]
    unreal.log("   ConstraintInstance 可用字段: %s" % fields)
except Exception as ex:
    unreal.log("   CI dir ERR %s" % ex)

unreal.log("############ 4. RBAN 节点设置")
abp = LO(ABP)
if abp:
    for g in unreal.AnimationLibrary.get_animation_graphs(abp):
        try:
            nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_RigidBody)
        except Exception:
            nodes = []
        for n in nodes:
            nd = n.get_editor_property("node")
            unreal.log("   图 %s RigidBody 节点，可读写属性：")
            for m in dir(nd):
                if m.startswith("_"):
                    continue
                try:
                    unreal.log("      %-42s = %s" % (m, nd.get_editor_property(m)))
                except Exception:
                    pass

unreal.log("############ 5. 动画里有没有披风骨轨道")
AL = unreal.AnimationLibrary
for ap in ANIMS:
    a = LO(ap)
    if not a:
        continue
    try:
        names = [str(x) for x in a.controller.get_model_interface().get_bone_track_names()]
    except Exception as ex:
        unreal.log("   %s track ERR %s" % (ap, str(ex)[:60]))
        continue
    cape = [x for x in names if "cape" in x.lower()]
    unreal.log("   %s  轨道数=%d  披风轨道数=%d" % (ap.split("/")[-1], len(names), len(cape)))
    nf = int(AL.get_num_frames(a))
    objs = [unreal.Name(x) for x in cape] if cape else []
    if objs:
        p0 = AL.get_bone_poses_for_frame(a, objs, 0, False)
        pm = AL.get_bone_poses_for_frame(a, objs, max(1, nf // 2), False)
        pe = AL.get_bone_poses_for_frame(a, objs, nf, False)
        for i, bn in enumerate(cape[:6]):
            d1 = ((p0[i].translation.x - pm[i].translation.x) ** 2 + (p0[i].translation.y - pm[i].translation.y) ** 2 +
                  (p0[i].translation.z - pm[i].translation.z) ** 2) ** 0.5
            d2 = ((pm[i].translation.x - pe[i].translation.x) ** 2 + (pm[i].translation.y - pe[i].translation.y) ** 2 +
                  (pm[i].translation.z - pe[i].translation.z) ** 2) ** 0.5
            unreal.log("      %-18s 位移漂移 f0->mid %.4f   mid->last %.4f" % (bn, d1, d2))

unreal.log("############ 6. 披风链在骨架里的挂点")
if skel:
    for b in ("cape_chain_01_l", "cape_chain_01_m", "cape_chain_01_r", "cape_chain_09_l"):
        try:
            path = [str(x) for x in unreal.SkeletonLibrary.find_bone_path_to_root(skel, b)]
            unreal.log("   %-16s 父链 = %s" % (b, path))
        except Exception as ex:
            unreal.log("   %-16s ERR %s" % (b, str(ex)[:60]))

unreal.log("############ 7. 角色网格组件设置")
bp = LO(CH)
if bp:
    for c in bp.get_components_by_class(unreal.SkeletalMeshComponent):
        unreal.log("   组件 %s" % c.get_name())
        for pr in ("physics_asset", "b_enable_update_rate_optimizations", "anim_update_rate_params",
                   "b_enable_animation", "visibilitybasedlod", "b_override_anim_update_rate"):
            try:
                unreal.log("      %-40s = %s" % (pr, c.get_editor_property(pr)))
            except Exception:
                pass
unreal.log("############ DONE")
