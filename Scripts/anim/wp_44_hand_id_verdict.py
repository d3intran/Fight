# -*- coding: utf-8 -*-
"""wp_44 —— 决定：目标骨架里「持斧手」是 hand_r 还是 hand_l（只读，用数据说话）。

背景
----
RTG 的 mirror 映射把左右链交叉了（`Target[LeftArm] <- Source[RightArm]`），
而源 `Weapon` 挂在源 **R_Hand** 下。所以武器锚点该选哪个，取决于
「目标哪只手 = 源 R_Hand」——命名不可信，必须测。

三个独立判据：
  P1 链定义   IK_Darius 的 RightArm / LeftArm 链末端骨名 + RTG 的源链映射（字面推理）
  P2 互相关   逐帧 |手 − pelvis| 距离序列的 Pearson 相关（形状匹配，不需坐标系归一）
  P3 侧向位移 手相对 pelvis 的位置在「髋轴」上的投影（正负侧）

⚠️ 单位校准：实测 `AnimPoseSpaces.WORLD` 对本骨架的平移数值 **就是 cm**
   （`weapon_jnt_r` 离 `hand_r` 读数 0.444 → 真实 0.44cm）。**不要乘 100。**

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_44_hand_id_verdict.py
"""
import json
import math

import unreal

APE = unreal.AnimPoseExtensions
AL = unreal.AnimationLibrary
L = unreal.log
OPTS = unreal.AnimPoseEvaluationOptions()
OUT = "E:/UE/Fight/Saved/Attack/wp44_hand_id.json"
R = {}

SRC_ATK = "/Game/Character/Darius/LOL_Source/A_LOL_Darius_attack1"
TGT_ATK = "/Game/Character/Darius/Anims/A_Darius_Attack1_LOL"
IK_T = "/Game/Character/Darius/IK/IK_Darius"
RTG = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"


def wp(pose, bone):
    t = APE.get_bone_pose(pose, unreal.Name(bone), unreal.AnimPoseSpaces.WORLD)
    return (t.translation.x, t.translation.y, t.translation.z)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def nrm(v):
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def pearson(a, b):
    n = min(len(a), len(b))
    if n < 4:
        return 0.0
    a, b = a[:n], b[:n]
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((x - mb) ** 2 for x in b))
    return num / (da * db) if da * db > 1e-9 else 0.0


# ============================================================ P1 链定义
L("=" * 78)
L("=== P1 IK_Darius 链定义（RightArm / LeftArm 末端骨）===")
L("=" * 78)


def bone_of(ref):
    try:
        return str(ref.get_editor_property("bone_name"))
    except Exception:
        return "<ERR>"


rig = unreal.load_object(None, IK_T)
chains = unreal.IKRigController.get_controller(rig).get_retarget_chains()
chain_def = {}
for ch in chains:
    nm = str(ch.chain_name)
    s = bone_of(ch.get_editor_property("start_bone"))
    e = bone_of(ch.get_editor_property("end_bone"))
    chain_def[nm] = [s, e]
    if nm in ("RightArm", "LeftArm", "RightClavicle", "LeftClavicle", "Weapon"):
        L("   %-16s  %-18s -> %-18s" % (nm, s, e))
R["P1_chain_def"] = chain_def

# RTG 映射
rtg = unreal.load_object(None, RTG)
rc = unreal.IKRetargeterController.get_controller(rtg)
cmap = {}
for nm in chain_def:
    try:
        cmap[nm] = str(rc.get_source_chain(unreal.Name(nm)))
    except Exception:
        cmap[nm] = None
R["P1_rtg_map"] = cmap
L("")
L("   RTG 映射（目标链 <- 源链）：")
for nm in ("RightArm", "LeftArm", "rightArm", "Weapon"):
    if nm in cmap:
        L("      %-16s <- %s" % (nm, cmap[nm]))
L("")
L("   ⇒ 字面推理：目标 hand_? = 该链末端骨；其运动来源 = 映射到的源链末端")

# ============================================================ P2/P3 手部序列
L("")
L("=" * 78)
L("=== P2/P3 手部数据（单位已校准为 cm）===")
L("=" * 78)


def collect(anim_path, ref_bone, hands, lateral_axis_bones):
    a = unreal.load_object(None, anim_path)
    if a is None:
        L("   !! 载不到 %s" % anim_path)
        return None
    nf = AL.get_num_frames(a)
    dist = {h: [] for h in hands}
    lat = {h: [] for h in hands}
    for f in range(nf + 1):
        try:
            pose = APE.get_anim_pose_at_frame(a, f, OPTS)
            r = wp(pose, ref_bone)
            try:
                p1 = wp(pose, lateral_axis_bones[0])
                p2 = wp(pose, lateral_axis_bones[1])
                axis = sub(p1, p2)
            except Exception:
                axis = (1.0, 0.0, 0.0)
            for h in hands:
                v = sub(wp(pose, h), r)
                dist[h].append(nrm(v))
                lat[h].append(dot(v, axis) / (nrm(axis) + 1e-9))
        except Exception:
            pass
    return {"anim": anim_path, "frames": nf, "dist": dist, "lat": lat}


src = collect(SRC_ATK, "Pelvis", ["R_Hand", "L_Hand"], ("L_Hip", "R_Hip"))
tgt = collect(TGT_ATK, "pelvis", ["hand_r", "hand_l"], ("thigh_l", "thigh_r"))
if src and tgt:
    R["P2_src"] = {k: [round(x, 2) for x in v] for k, v in src["dist"].items()}
    R["P2_tgt"] = {k: [round(x, 2) for x in v] for k, v in tgt["dist"].items()}
    L("   [源]   R_Hand 离 Pelvis : %6.1f ~ %6.1f cm" % (min(src["dist"]["R_Hand"]), max(src["dist"]["R_Hand"])))
    L("   [源]   L_Hand 离 Pelvis : %6.1f ~ %6.1f cm" % (min(src["dist"]["L_Hand"]), max(src["dist"]["L_Hand"])))
    L("   [目标] hand_r 离 pelvis : %6.1f ~ %6.1f cm" % (min(tgt["dist"]["hand_r"]), max(tgt["dist"]["hand_r"])))
    L("   [目标] hand_l 离 pelvis : %6.1f ~ %6.1f cm" % (min(tgt["dist"]["hand_l"]), max(tgt["dist"]["hand_l"])))
    L("")
    L("   P2 Pearson 相关（距离序列形状，越高越说明同源）：")
    cors = {}
    for sh in ("R_Hand", "L_Hand"):
        for th in ("hand_r", "hand_l"):
            c = pearson(src["dist"][sh], tgt["dist"][th])
            cors["%s<->%s" % (sh, th)] = round(c, 4)
            L("      %-9s <-> %-8s  r = %+.4f" % (sh, th, c))
    R["P2_corr"] = cors
    L("")
    L("   P3 侧向投影（髋轴 点积，正负侧；只看符号一致性）：")
    for sh in ("R_Hand", "L_Hand"):
        v = src["lat"][sh]
        L("      [源]   %-8s 均值 %+8.2f  范围 %+8.2f ~ %+8.2f" % (sh, sum(v) / len(v), min(v), max(v)))
    for th in ("hand_r", "hand_l"):
        v = tgt["lat"][th]
        L("      [目标] %-8s 均值 %+8.2f  范围 %+8.2f ~ %+8.2f" % (th, sum(v) / len(v), min(v), max(v)))
    R["P3"] = {"src": {k: [round(min(v), 2), round(max(v), 2)] for k, v in src["lat"].items()},
               "tgt": {k: [round(min(v), 2), round(max(v), 2)] for k, v in tgt["lat"].items()}}

# ============================================================ 裁决
L("")
L("=" * 78)
L("=== 裁决 ===")
L("=" * 78)
ra = chain_def.get("RightArm", ["?", "?"])
la = chain_def.get("LeftArm", ["?", "?"])
L("   RightArm 链 : %s -> %s     RTG 源链 = %s" % (ra[0], ra[1], cmap.get("RightArm")))
L("   LeftArm  链 : %s -> %s     RTG 源链 = %s" % (la[0], la[1], cmap.get("LeftArm")))
L("   源 Weapon 挂载手 = R_Hand（J4 实测 mean 30.78cm vs L_Hand 73.04cm）")
L("")
L("   ⇒ 若 RightArm 链末端 = hand_r 且其源链 = LeftArm ⇒ 目标 hand_r <- 源 L_Hand")
L("     ⇒ 目标 hand_l <- 源 R_Hand ⇒ 武器锚点应选 **weapon_jnt_l**")
L("   ⇒ 反之若映射未交叉/末端不同，锚点为 weapon_jnt_r")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(R, f, indent=1, ensure_ascii=False, default=str)
L("")
L("已写 %s" % OUT)
L("WP44_HAND_ID_DONE")
