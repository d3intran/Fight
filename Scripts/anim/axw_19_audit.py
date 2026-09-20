import math
import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

MERGED = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered"
LOW_PATH = "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"
UP_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo"

merged = eal.load_asset(MERGED)
low = eal.load_asset(LOW_PATH)
up = eal.load_asset(UP_PATH)


def track_names(anim):
    return [str(n) for n in anim.controller.get_model_interface().get_bone_track_names()]


names = track_names(merged)
chains = {b: [str(x) for x in AL.find_bone_path_to_root(merged, b)][::-1] for b in names}
lc = {n.lower(): n for n in names}


def read(anim):
    nf = int(AL.get_num_frames(anim))
    objs = [unreal.Name(b) for b in names]
    out = {}
    for f in range(nf + 1):
        poses = AL.get_bone_poses_for_frame(anim, objs, f, False)
        out[f] = {b: ((poses[i].translation.x, poses[i].translation.y, poses[i].translation.z),
                      (poses[i].rotation.x, poses[i].rotation.y, poses[i].rotation.z, poses[i].rotation.w),
                      (poses[i].scale3d.x, poses[i].scale3d.y, poses[i].scale3d.z))
                  for i, b in enumerate(names)}
    return out


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def qrot(q, v):
    x, y, z, w = q
    m = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def fk(tracks, bone, f):
    P, Q, S = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
    for bn in chains.get(bone, []):
        key = bn if bn in tracks[f] else lc.get(bn.lower())
        tr = tracks[f].get(key) if key else None
        if tr is None:
            continue
        t, q, s = tr
        off = qrot(Q, (t[0] * S[0], t[1] * S[1], t[2] * S[2]))
        P = (P[0] + off[0], P[1] + off[1], P[2] + off[2])
        Q = qmul(Q, q)
        S = (S[0] * s[0], S[1] * s[1], S[2] * s[2])
    return P, Q


M = read(merged)
L = read(low)
U = read(up)

unreal.log("### 1. weapon_jnt_offset 是否仍贴在 weapon_jnt 上（它的局部键取自 LOW）")
worst = 0.0
for f in range(len(M)):
    a, _ = fk(M, "weapon_jnt_offset", f)
    b, _ = fk(M, "weapon_jnt", f)
    worst = max(worst, math.dist(a, b))
unreal.log("   最大偏差 %.4f cm（应≈0）" % worst)

unreal.log("### 2. 上半身真的换了吗（局部键 vs LOW 不同的骨数）")
upper_like = []
for b in names:
    diff = False
    for f in range(min(len(M), len(L))):
        rm = M[f][b][1]
        rl = L[f][b][1]
        ang = math.degrees(2 * math.acos(max(-1.0, min(1.0, abs(sum(x * y for x, y in zip(rm, rl)))))))
        if ang > 0.5:
            diff = True
            break
    if diff:
        upper_like.append(b)
unreal.log("   与 LOW 有差别的骨 = %d 根" % len(upper_like))
unreal.log("   其中不在 spine_01 子树里的（只应是 weapon_jnt）= %s" % (
    [b for b in upper_like if b in ("weapon_jnt", "weapon_jnt_offset", "pelvis", "root")]))

unreal.log("### 3. 上半身 vs UP 的「形状」一致性（去掉骨盆差异后的相对姿态）")
# 以 spine_01 为参照：比较 spine_01→head / spine_01→hand_r 的向量方向
for ref, tgt in (("spine_01", "head"), ("spine_01", "hand_r"), ("spine_01", "hand_l")):
    for lbl, T, nf in (("MERGED", M, len(M) - 1), ("UP", U, len(U) - 1)):
        worst = 0.0
        for f in range(nf + 1):
            pr, _ = fk(T, ref, f)
            pt, _ = fk(T, tgt, f)
            v = tuple(pt[i] - pr[i] for i in range(3))
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            v = tuple(x / n for x in v)
            if lbl == "MERGED":
                mv = v
            else:
                uv = v
                d = math.degrees(math.acos(max(-1.0, min(1.0, abs(sum(a * b for a, b in zip(mv, uv)))))))
                worst = max(worst, d)
        if lbl == "UP":
            unreal.log("   %-9s -> %-9s 最大方向差 %.2f°" % (ref, tgt, worst))

unreal.log("### 4. AnimBP / 混合空间引用链")
abp = eal.load_asset("/Game/Character/Darius/Blueprints/ABP_Darius_Test")
try:
    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
    unreal.log("   ABP_Darius_Test 编译通过")
except Exception as ex:
    unreal.log("   ABP 编译 ERR %s" % ex)
for g in unreal.AnimationLibrary.get_animation_graphs(abp):
    try:
        nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_BlendSpacePlayer)
    except Exception:
        nodes = []
    for n in nodes:
        nd = n.get_editor_property("node")
        bsp = nd.get_editor_property("blend_space")
        unreal.log("   图 %-12s BlendSpacePlayer -> %s" % (g.get_name(), bsp.get_name() if bsp else None))
    try:
        snodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_SequencePlayer)
    except Exception:
        snodes = []
    for n in snodes:
        nd = n.get_editor_property("node")
        sq = nd.get_editor_property("sequence")
        unreal.log("   图 %-12s SequencePlayer  -> %s" % (g.get_name(), sq.get_name() if sq else None))

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
unreal.log("### 5. 关卡角色蓝图模板的 anim_class")
try:
    cdo = unreal.get_default_object(bp)
    comps = cdo.get_components_by_class(unreal.SkeletalMeshComponent)
    for c in comps:
        ac = c.get_editor_property("anim_class")
        unreal.log("   %-20s anim_class = %s" % (c.get_name(), ac.get_name() if ac else None))
except Exception as ex:
    unreal.log("   ERR %s" % ex)
unreal.log("### DONE")
