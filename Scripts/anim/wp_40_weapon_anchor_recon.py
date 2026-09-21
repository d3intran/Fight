# -*- coding: utf-8 -*-
"""武器锚点审计（只读）——「斧头到底该挂哪个骨」的一次性裁决。

背景（已被 AGENTS.md / recon.txt 确认的硬事实）
------------------------------------------------
目标骨架 SK_Darius_GodKing 自带三个武器锚点骨：
    weapon_jnt     父 = root      ← 2XKO 的「插地死斧」位
    weapon_jnt_r   父 = hand_r    ← 右手武器挂点
    weapon_jnt_l   父 = hand_l    ← 左手武器挂点
源骨架 SK_LOL_Darius 里武器骨 Weapon 的父级 = R_Hand，真实层级 Axe_Head < Weapon < R_Hand。
⇒ 与源**同构**的挂点是 weapon_jnt_r。而当前 RTG 的 Weapon 链建在 weapon_jnt 上（父 = root），
   层级不对应 ⇒ FK 重定向写出的局部变换被当成「相对 root」⇒ 斧头钉在脚下、产物轨恒定不变。

四段检查（全部只读，不写任何资产）：
  A 骨架侧   两侧武器骨的父级
  B 链侧     IK_Darius / IK_LOL_Darius 的链定义 + RTG 链映射 + FK op 链设置
  C 动画侧   产物里 weapon_jnt / weapon_jnt_r 的局部平移行程（0 = 冻结）
  D 世界空间  「武器锚点 ↔ 手」的距离、锚点 ↔ 锚点距离，目标 vs 源

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_40_weapon_anchor_recon.py

输出：Saved/Attack/weapon_anchor_recon.json
"""
import json
import math

import unreal

APE = unreal.AnimPoseExtensions
AL = unreal.AnimationLibrary
L = unreal.log
LW = unreal.log_warning

OUT = "E:/UE/Fight/Saved/Attack/weapon_anchor_recon.json"

TGT_MESH = "/Game/Character/Darius/SK_Darius_GodKing"
SRC_MESH = "/Game/Character/Darius/LOL_Source/SK_LOL_Darius"
IK_T = "/Game/Character/Darius/IK/IK_Darius"
IK_S = "/Game/Character/Darius/IK/IK_LOL_Darius"
RTG = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
AXE = "/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe"

SRC_ANIM_DIR = "/Game/Character/Darius/LOL_Source"
TGT_ANIM_DIRS = ["/Game/Character/Darius/Anims", "/Game/Character/Darius/Anims_TP_v2",
                 "/Game/Character/Darius/Animations/LOL_Retarget_Test"]

OPTS = unreal.AnimPoseEvaluationOptions()
R = {}


# ------------------------------------------------------------------ 小工具
def wp(pose, bone):
    """世界空间骨骼位姿 -> (loc_xyz, quat_xyzw)"""
    t = APE.get_bone_pose(pose, unreal.Name(bone), unreal.AnimPoseSpaces.WORLD)
    return ((t.translation.x, t.translation.y, t.translation.z),
            (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w))


def dist(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def parent_map(mesh_path):
    """目标骨架的 骨->父骨 映射（USkeleton.bone_tree 的 FBoneNode）"""
    try:
        mesh = unreal.load_object(None, mesh_path)
        sk = mesh.get_editor_property("skeleton")
    except Exception as ex:
        LW("[A] 取 skeleton 失败 %s: %s" % (mesh_path, ex))
        return {}, None
    bt = None
    for prop in ("bone_tree", "BoneTree"):
        try:
            bt = sk.get_editor_property(prop)
            if bt is not None and len(bt) > 0:
                break
        except Exception:
            bt = None
    if bt is None:
        cands = [p for p in dir(sk) if "bone" in p.lower()]
        LW("[A] 读不到 bone_tree，候选属性: %s" % cands[:15])
        return {}, sk
    names, pidx = [], []
    for n in bt:
        try:
            names.append(str(n.get_editor_property("name")))
            pidx.append(int(n.get_editor_property("parent_index")))
        except Exception:
            names.append("?"); pidx.append(-1)
    m = {}
    for i, nm in enumerate(names):
        p = pidx[i]
        m[nm] = names[p] if 0 <= p < len(names) else None
    return m, sk


# ================================================================== A 骨架侧
L("=" * 78)
L("=== A 骨架侧：武器锚点骨的父级 ===")
L("=" * 78)
tgt_pm, tgt_sk = parent_map(TGT_MESH)
A = {"target": {}, "source": {}}
for b in ("weapon_jnt", "weapon_jnt_r", "weapon_jnt_l", "weapon_jnt_offset", "hand_r", "hand_l", "root"):
    pc = tgt_pm.get(b)
    A["target"][b] = pc
    L("   目标 %-20s 父 = %s %s" % (b, pc, "" if pc is None else
                                    ("  <= 与源 Weapon 同构 ✓" if (b == "weapon_jnt_r" and pc == "hand_r")
                                     else ("  <= !!! 不是 hand_r" if b == "weapon_jnt_r" else ""))))
src_pm, src_sk = parent_map(SRC_MESH)
for b in ("Weapon", "Axe_Head", "Axe_Handle", "SnapWeapon", "SnapWeapon2Hand", "R_Hand", "L_Hand", "Root"):
    pc = src_pm.get(b)
    A["source"][b] = pc
    L("   源   %-20s 父 = %s" % (b, pc))
if not src_pm:
    L("   [INFO] 源骨架 bone_tree 读不到（净化后的 SK_LOL_Darius 可能是 60 骨变体）")
R["A_parents"] = A

# ================================================================== B 链侧
L("")
L("=" * 78)
L("=== B 链侧：IK Rig 的链定义 + RTG 映射 ===")
L("=" * 78)
B = {}
for tag, p in (("TARGET", IK_T), ("SOURCE", IK_S)):
    rig = unreal.load_object(None, p)
    if rig is None:
        L("   [WARN] %s 载不到: %s" % (tag, p)); continue
    try:
        chains = unreal.IKRigController.get_controller(rig).get_retarget_chains()
    except Exception as ex:
        LW("   [WARN] %s get_retarget_chains 失败: %s" % (tag, ex)); continue
    rows = []
    for ch in chains:
        try:
            rows.append({"name": str(ch.chain_name),
                         "start": str(ch.start_bone),
                         "end": str(ch.end_bone)})
        except Exception as ex:
            rows.append({"err": str(ex)})
    B[tag] = rows
    L("   %s IK Rig 链 %d 条：" % (tag, len(rows)))
    for r in rows:
        mark = ""
        if "eapon" in str(r.get("name", "")):
            mark = "   <<< 武器链"
            if tag == "TARGET" and str(r.get("start")) == "weapon_jnt":
                mark += "  ★ 落点是 weapon_jnt（父=root）—— 与源不同构"
            if tag == "TARGET" and str(r.get("start")) == "weapon_jnt_r":
                mark += "  ✓ 落点是 weapon_jnt_r（父=hand_r）"
        L("      %-24s %-18s -> %-18s%s" % (r.get("name"), r.get("start"), r.get("end"), mark))

rtg = unreal.load_object(None, RTG)
if rtg:
    c = unreal.IKRetargeterController.get_controller(rtg)
    try:
        tgt_chains = [str(ch.chain_name) for ch in
                      unreal.IKRigController.get_controller(unreal.load_object(None, IK_T)).get_retarget_chains()]
        cmap = {ch: str(c.get_source_chain(unreal.Name(ch))) for ch in tgt_chains}
        B["rtg_chain_map"] = cmap
        L("   RTG 链映射（%d 条），武器相关：" % len(cmap))
        for k, v in cmap.items():
            if "eapon" in k:
                L("      %-24s <- %-24s%s" % (k, v, "   ★ 源 Weapon 被送进目标 weapon_jnt" if v == "Weapon" else ""))
    except Exception as ex:
        LW("   RTG 链映射读不到: %s" % ex)
    try:
        ops = []
        for i in range(c.get_num_retarget_ops()):
            nm = str(c.get_op_name(i))
            e = {"i": i, "op": nm}
            try:
                st = c.get_op_controller(i).get_settings()
                e["enabled"] = st.get_editor_property("enabled")
                if nm == "FK Chains":
                    arr = st.get_editor_property("chains_to_retarget")
                    e["chain_count"] = len(arr)
                    for it in arr:
                        try:
                            if "eapon" in str(it.get_editor_property("target_chain_name")):
                                e["weapon_fk"] = {
                                    "target": str(it.get_editor_property("target_chain_name")),
                                    "source": str(it.get_editor_property("source_chain_name")),
                                    "rotation_mode": str(it.get_editor_property("rotation_mode")),
                                    "translation_mode": str(it.get_editor_property("translation_mode")),
                                }
                        except Exception:
                            pass
                if nm == "Run IK Rig":
                    e["ik_chains"] = [str(x.get_editor_property("target_chain_name"))
                                      for x in st.get_editor_property("chains")]
            except Exception as ex:
                e["err"] = str(ex)
            ops.append(e)
        B["rtg_ops"] = ops
        L("   RTG op 栈：")
        for o in ops:
            L("      op[%d] %-14s enabled=%s %s" % (
                o["i"], o["op"], o.get("enabled"),
                "" if not o.get("weapon_fk") else "武器 FK: %s" % json.dumps(o["weapon_fk"], ensure_ascii=False)))
    except Exception as ex:
        LW("   op 栈读不到: %s" % ex)
R["B_chains"] = B

# ================================================================== C 动画侧
L("")
L("=" * 78)
L("=== C 动画侧：产物里武器骨的局部平移行程（0 = 冻结/不跟手）===")
L("=" * 78)
C = {}
for d in TGT_ANIM_DIRS:
    for p in unreal.EditorAssetLibrary.list_assets(d, recursive=False, include_folder=False):
        a = unreal.load_object(None, p)
        if not isinstance(a, unreal.AnimSequence):
            continue
        nf = AL.get_num_frames(a)
        rec = {"frames": nf}
        for bone in ("weapon_jnt", "weapon_jnt_r", "weapon_jnt_l"):
            peak = 0.0
            rot_peak = 0.0
            prev = None
            prevq = None
            for f in range(0, nf + 1, max(1, nf // 8)):
                try:
                    t = AL.get_bone_pose_for_frame(a, unreal.Name(bone), f, True)
                except Exception:
                    prev = None
                    prevq = None
                    continue
                cur = (t.translation.x, t.translation.y, t.translation.z)
                curq = (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w)
                if prev is not None:
                    peak = max(peak, dist(cur, prev))
                    dq = abs(sum(curq[k] * prevq[k] for k in range(4)))
                    rot_peak = max(rot_peak, math.degrees(2.0 * math.acos(min(1.0, dq))))
                prev = cur
                prevq = curq
            rec[bone] = round(peak, 6)
            rec[bone + "_rot"] = round(rot_peak, 3)
        C[a.get_name()] = rec
        moving = [b for b in ("weapon_jnt", "weapon_jnt_r", "weapon_jnt_l")
                  if rec[b + "_rot"] > 0.5 or rec[b] > 1e-5]
        verdict = ("被驱动: %s" % moving) if moving else "三个锚点全冻结 -> 完全没被驱动"
        L("   %-34s 帧%-4d | wjnt 平移%9.5f 旋%7.2f | wjnt_r %9.5f %7.2f | wjnt_l %9.5f %7.2f | %s" % (
            a.get_name(), nf,
            rec["weapon_jnt"], rec["weapon_jnt_rot"],
            rec["weapon_jnt_r"], rec["weapon_jnt_r_rot"],
            rec["weapon_jnt_l"], rec["weapon_jnt_l_rot"], verdict))
R["C_anim_travel"] = C

# ================================================================== D 世界空间
L("")
L("=" * 78)
L("=== D 世界空间：「锚点 ↔ 手」距离，目标(米) vs 源(cm) ===")
L("=" * 78)
D = {"pairs": []}


def probe(anim_path, hand, anchors, unit_scale, tag):
    a = unreal.load_object(None, anim_path)
    if a is None:
        L("   [WARN] 载不到 %s" % anim_path); return None
    nf = AL.get_num_frames(a)
    out = {"anim": anim_path, "frames": nf, "unit_to_cm": unit_scale, "distances": {}}
    for an in anchors:
        vals = []
        for f in range(0, nf + 1, max(1, nf // 6)):
            try:
                pose = APE.get_anim_pose_at_frame(a, f, OPTS)
                ph, _ = wp(pose, hand)
                pa, _ = wp(pose, an)
            except Exception:
                continue
            vals.append(dist(ph, pa) * unit_scale)
        if vals:
            lo, hi = min(vals), max(vals)
            out["distances"][an] = {"min_cm": round(lo, 2), "max_cm": round(hi, 2),
                                    "range_cm": round(hi - lo, 2), "mean_cm": round(sum(vals) / len(vals), 2)}
            L("   %-7s %-34s %-16s -> %-10s min=%7.2f max=%7.2f 摆幅=%6.2f cm" % (
                tag, a.get_name(), "%s .. %s" % (hand, an), "", lo, hi, hi - lo))
    return out


L("   [源] Weapon 是 R_Hand 的子骨 ⇒ 距离恒定/近恒定才是源的本意")
D["source"] = probe("/Game/Character/Darius/LOL_Source/A_LOL_Darius_idle1", "R_Hand",
                    ["Weapon", "Axe_Head"], 1.0, "源")
D["source_run"] = probe("/Game/Character/Darius/LOL_Source/A_LOL_Darius_run", "R_Hand",
                        ["Weapon", "Axe_Head"], 1.0, "源")

L("")
L("   [目标] 重定向产物：两个锚点各自离 hand_r 多远")
for ap in ("/Game/Character/Darius/Animations/LOL_Retarget_Test/A_Darius_idle1",
           "/Game/Character/Darius/Animations/LOL_Retarget_Test/A_Darius_run"):
    for hb in ("hand_r", "hand_l"):
        got = probe(ap, hb, ["weapon_jnt", "weapon_jnt_r", "weapon_jnt_l"], 1.0, "目标")
        if got:
            D["pairs"].append(got)

R["D_world"] = D

# ------------------------------------------------------------------ 落盘 + 裁决
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(R, f, indent=1, ensure_ascii=False, default=str)
L("")
L("=" * 78)
L("=== 裁决 ===")
L("=" * 78)
L("   1) 源结构的武器骨        : %s" % ("Weapon 父 = %s" % A["source"].get("Weapon") if A["source"] else "（未读到）"))
L("   2) 目标武器锚点          : weapon_jnt(父=root) / weapon_jnt_r(父=%s)" % A["target"].get("weapon_jnt_r"))
L("   3) RTG 把源 Weapon 送到  : 目标链 Weapon（=%s）" % next(
    (r.get("start") for r in B.get("TARGET", []) if "eapon" in str(r.get("name"))), "?"))
L("   4) 结论                  : 应把 Weapon 链落点改为 weapon_jnt_r，并把斧头几何改挂 weapon_jnt_r")
L("")
L("已写 %s" % OUT)
L("WP40_WEAPON_ANCHOR_RECON_DONE")
