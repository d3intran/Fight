# -*- coding: utf-8 -*-
"""rtg_20_fix_verify —— RTG 候选修复 + 自动验收（纯求值，不生成/销毁任何 Actor）

用法：先写 Saved/Attack/rtg_fix_mode.txt（none / root_yaw180 / align / src_pelvis_yaw180），
再远程执行本脚本。脚本会：快照 → 施加修复 → 把源 run/idle1 重定向到 _Test 目录 → 落盘 → 用
AnimPose 量三件事并打 PASS/FAIL。
"""

import unreal
import json
import os

L = unreal.log
LW = unreal.log_warning
APE = unreal.AnimPoseExtensions

RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
OUT_DIR = "/Game/Character/Darius/Animations/LOL_Retarget_Test"
SNAP = "E:/UE/Fight/Saved/Attack/rtg_snapshot.json"
MODE_FILE = "E:/UE/Fight/Saved/Attack/rtg_fix_mode.txt"

SRC_RUN = "/Game/Character/Darius/LOL_Source/A_LOL_Darius_run"
SRC_IDLE = "/Game/Character/Darius/LOL_Source/A_LOL_Darius_idle1"
TGT_RUN = f"{OUT_DIR}/A_Darius_run"
TGT_IDLE = f"{OUT_DIR}/A_Darius_idle1"

TGT_BONES = ["foot_l", "ball_l", "foot_r", "ball_r", "pelvis", "head", "hand_r", "weapon_jnt"]
SRC_BONES = ["L_Foot", "L_Toe", "R_Foot", "R_Toe", "Pelvis", "Head", "R_Hand", "Weapon"]

mode = "none"
try:
    if os.path.isfile(MODE_FILE):
        mode = open(MODE_FILE, "r", encoding="utf-8").read().strip() or "none"
except Exception as ex:
    LW(f"[MODE] read err {ex}")
L(f"[MODE] = {mode}")

rtg = unreal.load_object(None, RTG_PATH)
c = unreal.IKRetargeterController.get_controller(rtg)
eal = unreal.EditorAssetLibrary

# ============================================================ 1. 快照
snap = {"mode": mode}
try:
    snap["target_root_offset"] = [c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.TARGET).x,
                                  c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.TARGET).y,
                                  c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.TARGET).z]
    snap["source_root_offset"] = [c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.SOURCE).x,
                                  c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.SOURCE).y,
                                  c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.SOURCE).z]
except Exception as ex:
    LW(f"[SNAP] root offset err {ex}")
try:
    rs = c.get_root_settings()
    ro = rs.get_editor_property("rotation_offset")
    to = rs.get_editor_property("translation_offset")
    snap["root_settings"] = {"rot": [ro.pitch, ro.yaw, ro.roll], "trans": [to.x, to.y, to.z],
                             "blend_to_source": rs.get_editor_property("blend_to_source"),
                             "rot_alpha": rs.get_editor_property("rotation_alpha")}
    L(f"[SNAP] root_settings rot={ro.pitch:.2f},{ro.yaw:.2f},{ro.roll:.2f}  trans={to.x:.2f},{to.y:.2f},{to.z:.2f}")
except Exception as ex:
    LW(f"[SNAP] root settings err {ex}")
try:
    ops = [str(c.get_op_name(i)) for i in range(c.get_num_retarget_ops())]
    snap["ops"] = ops
    L(f"[SNAP] ops = {ops}")
except Exception as ex:
    LW(f"[SNAP] ops err {ex}")
try:
    tgt_map = {}
    tgt_rig = unreal.load_object(None, "/Game/Character/Darius/IK/IK_Darius")
    for ch in unreal.IKRigController.get_controller(tgt_rig).get_retarget_chains():
        tgt_map[str(ch.chain_name)] = str(c.get_source_chain(ch.chain_name))
    snap["chain_map"] = tgt_map
    L(f"[SNAP] 链映射条数 = {len(tgt_map)}")
except Exception as ex:
    LW(f"[SNAP] chain map err {ex}")
try:
    with open(SNAP, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, ensure_ascii=False)
    L(f"[SNAP] 已写入 {SNAP}")
except Exception as ex:
    LW(f"[SNAP] write err {ex}")

# ============================================================ 2. 施加修复
changed = False
# 卫生：每次都把 Pelvis Motion op 的旋转偏移归零，保证各轮试验同一基线
try:
    oc0 = c.get_op_controller(0)
    s0 = oc0.get_settings()
    s0.set_editor_property("rotation_offset_global", unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
    s0.set_editor_property("rotation_offset_local", unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
    oc0.set_settings(s0)
    rtg.modify()
    changed = True
    L("[FIX] 基线卫生：Pelvis Motion 旋转偏移已归零")
except Exception as ex:
    LW(f"[FIX] pelvis 归零 err {ex}")

try:
    zero_q = unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0).quaternion()
    for b, side in (("Root", unreal.RetargetSourceOrTarget.SOURCE), ("Pelvis", unreal.RetargetSourceOrTarget.SOURCE),
                    ("root", unreal.RetargetSourceOrTarget.TARGET), ("pelvis", unreal.RetargetSourceOrTarget.TARGET)):
        try:
            c.set_rotation_offset_for_retarget_pose_bone(unreal.Name(b), zero_q, side)
        except Exception:
            pass
    L("[FIX] 基线卫生：两侧 retarget-pose Root/Pelvis 旋转偏移已归零")
except Exception as ex:
    LW(f"[FIX] 姿态归零 err {ex}")

def qmul(a, b):
    ax, ay, az, aw = a.x, a.y, a.z, a.w
    bx, by, bz, bw = b.x, b.y, b.z, b.w
    return unreal.Quat(aw * bx + ax * bw + ay * bz - az * by,
                       aw * by - ax * bz + ay * bw + az * bx,
                       aw * bz + ax * by - ay * bx + az * bw,
                       aw * bw - ax * bx - ay * by - az * bz)


def qconj(a):
    return unreal.Quat(-a.x, -a.y, -a.z, a.w)


if mode in ("src_root_yaw180_world", "legcross", "src_root_yaw180_world_legcross", "mirror"):
    if mode.startswith("src"):
        side, bone, rig_path = unreal.RetargetSourceOrTarget.SOURCE, "Root", "/Game/Character/Darius/IK/IK_LOL_Darius"
    else:
        side, bone, rig_path = unreal.RetargetSourceOrTarget.TARGET, "root", "/Game/Character/Darius/IK/IK_Darius"
    try:
        rig = unreal.load_object(None, rig_path)
        rc = unreal.IKRigController.get_controller(rig)
        r_ref = rc.get_ref_pose_transform_of_bone(unreal.Name(bone)).rotation
        r_world = unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0).quaternion()
        # 把「世界空间绕 Z 转 180°」共轭进该骨的自身坐标系
        off = qmul(qconj(r_ref), qmul(r_world, r_ref))
        c.set_rotation_offset_for_retarget_pose_bone(unreal.Name(bone), off, side)
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
        changed = True
        back = c.get_rotation_offset_for_retarget_pose_bone(unreal.Name(bone), side).rotator()
        L(f"[FIX] {mode}: {bone} 的 world-yaw180 局部化偏移 = ({off.x:.3f},{off.y:.3f},{off.z:.3f},{off.w:.3f})  读回=({back.pitch:.2f},{back.yaw:.2f},{back.roll:.2f})")
        if mode == "mirror":
            pairing = []
            for a, b in (("Leg", "Leg"), ("Foot", "Foot"), ("Arm", "Arm"), ("Clavicle", "Clavicle"),
                         ("Thumb", "Thumb"), ("Index", "Index"), ("Middle", "Middle"),
                         ("Ring", "Ring"), ("Pinky", "Pinky"), ("IndexMetacarpal", "IndexMetacarpal"),
                         ("MiddleMetacarpal", "MiddleMetacarpal"), ("RingMetacarpal", "RingMetacarpal"),
                         ("PinkyMetacarpal", "PinkyMetacarpal")):
                pairing.append((f"Right{a}", f"Left{b}"))
                pairing.append((f"Left{a}", f"Right{b}"))
        elif mode in ("legcross", "src_root_yaw180_world_legcross"):
            pairing = (("RightLeg", "LeftLeg"), ("LeftLeg", "RightLeg"),
                       ("RightFoot", "LeftFoot"), ("LeftFoot", "RightFoot"))
        else:
            pairing = (("LeftLeg", "LeftLeg"), ("RightLeg", "RightLeg"),
                       ("LeftFoot", "LeftFoot"), ("RightFoot", "RightFoot"))
        for src_ch, tgt_ch in pairing:
            ok = c.set_source_chain(unreal.Name(src_ch), unreal.Name(tgt_ch))
            L(f"[FIX]   链映射 Target[{tgt_ch}] <- Source[{src_ch}] ok={ok}"
              f"  (读回 {c.get_source_chain(unreal.Name(tgt_ch))})")
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
    except Exception as ex:
        LW(f"[FIX] {mode} err {ex}")
elif mode in ("src_root_yaw180", "src_pelvis_yaw1802", "tgt_root_yaw180"):
    if mode == "src_root_yaw180":
        side, bone = unreal.RetargetSourceOrTarget.SOURCE, "Root"
    elif mode == "src_pelvis_yaw1802":
        side, bone = unreal.RetargetSourceOrTarget.SOURCE, "Pelvis"
    else:
        side, bone = unreal.RetargetSourceOrTarget.TARGET, "root"
    try:
        q = unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0).quaternion()
        c.set_rotation_offset_for_retarget_pose_bone(unreal.Name(bone), q, side)
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
        changed = True
        back = c.get_rotation_offset_for_retarget_pose_bone(unreal.Name(bone), side).rotator()
        L(f"[FIX] {mode}: 骨骼 {bone} 的 retarget-pose 旋转偏移 -> yaw=180 (读回 yaw={back.yaw:.2f})")
    except Exception as ex:
        LW(f"[FIX] {mode} err {ex}")
elif mode == "align_src":
    try:
        c.auto_align_all_bones(unreal.RetargetSourceOrTarget.SOURCE,
                               unreal.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
        changed = True
        L("[FIX] auto_align_all_bones(SOURCE, CHAIN_TO_CHAIN) 已执行")
        for b in ("Pelvis", "L_Hip", "R_Hip", "L_Foot", "R_Foot", "Spine1", "L_Shoulder", "R_Shoulder"):
            q = c.get_rotation_offset_for_retarget_pose_bone(unreal.Name(b), unreal.RetargetSourceOrTarget.SOURCE)
            r = q.rotator()
            L(f"[FIX]   SRC {b:<12} off=({r.pitch:8.2f},{r.yaw:8.2f},{r.roll:8.2f})")
    except Exception as ex:
        LW(f"[FIX] align_src err {ex}")
elif mode == "pose_root_yaw180":
    bone = "root" if mode == "pose_root_yaw180" else "pelvis"
    try:
        q = unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0).quaternion()
        c.set_rotation_offset_for_retarget_pose_bone(unreal.Name(bone), q, unreal.RetargetSourceOrTarget.TARGET)
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
        changed = True
        back = c.get_rotation_offset_for_retarget_pose_bone(unreal.Name(bone), unreal.RetargetSourceOrTarget.TARGET).rotator()
        L(f"[FIX] TARGET retarget-pose {bone} 旋转偏移 -> yaw=180 (读回 yaw={back.yaw:.2f})")
    except Exception as ex:
        LW(f"[FIX] {mode} err {ex}")
elif mode in ("no_run_ik", "with_run_ik"):
    want = (mode == "with_run_ik")
    try:
        for i in range(c.get_num_retarget_ops()):
            if str(c.get_op_name(i)) == "Run IK Rig":
                c.set_retarget_op_enabled(i, want)
                L(f"[FIX] op[{i}] Run IK Rig enabled = {want}")
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
        changed = True
    except Exception as ex:
        LW(f"[FIX] {mode} err {ex}")
elif mode == "fk_onetoone":
    try:
        rm = getattr(unreal, "FKChainRotationMode", None) or getattr(unreal, "RetargetRotationMode", None)
        L(f"[FIX] 枚举成员 = {[m for m in dir(rm) if not m.startswith('_')] if rm else None}")
        want = getattr(rm, "ONE_TO_ONE", None)
        oc1 = c.get_op_controller(1)
        s1 = oc1.get_settings()
        arr = s1.get_editor_property("chains_to_retarget")
        L(f"[FIX] FK 链数 = {len(arr)}  -> rotation_mode = {want}")
        new = []
        for cs in arr:
            cs.set_editor_property("rotation_mode", want)
            new.append(cs)
        s1.set_editor_property("chains_to_retarget", new)
        oc1.set_settings(s1)
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
        changed = True
        back = oc1.get_settings().get_editor_property("chains_to_retarget")
        L(f"[FIX] 读回前 3 条: {[str(x.get_editor_property('rotation_mode')) for x in back[:3]]}")
    except Exception as ex:
        LW(f"[FIX] fk_onetoone err {ex}")
elif mode == "root_settings_yaw180":
    try:
        rs = c.get_root_settings()
        rs.set_editor_property("rotation_offset", unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
        c.set_root_settings(rs)
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
        changed = True
        ro = c.get_root_settings().get_editor_property("rotation_offset")
        L(f"[FIX] 目标 root rotation_offset -> yaw=180  (读回 yaw={ro.yaw:.2f})")
    except Exception as ex:
        LW(f"[FIX] root_settings_yaw180 err {ex}")
elif mode == "align":
    try:
        c.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET,
                               unreal.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
        changed = True
        for b in ("thigh_l", "thigh_r", "upperarm_l", "upperarm_r", "pelvis"):
            q = c.get_rotation_offset_for_retarget_pose_bone(unreal.Name(b), unreal.RetargetSourceOrTarget.TARGET)
            r = q.rotator()
            L(f"[FIX] align 后 TGT {b:<12} off=({r.pitch:7.2f},{r.yaw:7.2f},{r.roll:7.2f})")
    except Exception as ex:
        LW(f"[FIX] align err {ex}")
elif mode == "pelvis_op_yaw180":
    try:
        oc = c.get_op_controller(0)
        s = oc.get_settings()
        s.set_editor_property("rotation_offset_global", unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
        oc.set_settings(s)
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
        changed = True
        back = oc.get_settings().get_editor_property("rotation_offset_global")
        L(f"[FIX] Pelvis Motion.rotation_offset_global -> yaw=180  (读回 yaw={back.yaw:.2f})")
    except Exception as ex:
        LW(f"[FIX] pelvis_op_yaw180 err {ex}")
elif mode == "src_pelvis_yaw180":
    try:
        q = unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0).quaternion()
        c.set_rotation_offset_for_retarget_pose_bone(unreal.Name("Pelvis"), q, unreal.RetargetSourceOrTarget.SOURCE)
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
        changed = True
        back = c.get_rotation_offset_for_retarget_pose_bone(unreal.Name("Pelvis"), unreal.RetargetSourceOrTarget.SOURCE).rotator()
        L(f"[FIX] 源 retarget-pose Pelvis 旋转偏移 -> yaw=180 (读回 yaw={back.yaw:.2f})")
    except Exception as ex:
        LW(f"[FIX] src_pelvis_yaw180 err {ex}")
elif mode == "restore":
    try:
        for side, tag in ((unreal.RetargetSourceOrTarget.TARGET, "TARGET"), (unreal.RetargetSourceOrTarget.SOURCE, "SOURCE")):
            try:
                c.reset_retarget_pose(unreal.Name("Default Pose"), [], side)
                L(f"[FIX] reset_retarget_pose({tag}) 完成")
            except Exception as ex:
                LW(f"[FIX] reset {tag} err {ex}")
        for i in range(c.get_num_retarget_ops()):
            nm = str(c.get_op_name(i))
            oc = c.get_op_controller(i)
            st = oc.get_settings()
            if nm == "Run IK Rig":
                c.set_retarget_op_enabled(i, True)
                L(f"[FIX] op[{i}] {nm} -> enabled")
            if nm == "FK Chains":
                rm = getattr(unreal, "FKChainRotationMode", None)
                back_mode = getattr(rm, "INTERPOLATED", None)
                arr = st.get_editor_property("chains_to_retarget")
                new = []
                for cs in arr:
                    cs.set_editor_property("rotation_mode", back_mode)
                    new.append(cs)
                st.set_editor_property("chains_to_retarget", new)
                oc.set_settings(st)
                L(f"[FIX] op[{i}] {nm} -> rotation_mode=INTERPOLATED")
        oc0 = c.get_op_controller(0)
        s0 = oc0.get_settings()
        s0.set_editor_property("rotation_offset_global", unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
        s0.set_editor_property("rotation_offset_local", unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
        oc0.set_settings(s0)
        rs = c.get_root_settings()
        rs.set_editor_property("rotation_offset", unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
        c.set_root_settings(rs)
        zero = unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0).quaternion()
        for b in ("root", "pelvis"):
            try:
                c.set_rotation_offset_for_retarget_pose_bone(unreal.Name(b), zero, unreal.RetargetSourceOrTarget.TARGET)
            except Exception:
                pass
        rtg.modify()
        eal.save_asset(RTG_PATH, only_if_is_dirty=False)
        changed = True
        L("[FIX] 已还原：Run IK 开启 / FK=Interpolated / 各旋转偏移归零")
    except Exception as ex:
        LW(f"[FIX] restore err {ex}")
else:
    L("[FIX] mode=none，不改 RTG（基线对照）")

# ============================================================ 3. 重定向到 _Test
if not eal.does_directory_exist(OUT_DIR):
    eal.make_directory(OUT_DIR)

ads = []
for p in (SRC_RUN, SRC_IDLE):
    ad = eal.find_asset_data(p)
    if ad:
        ads.append(ad)
    else:
        LW(f"[RETGT] 找不到 {p}")
L(f"[RETGT] 待重定向 {len(ads)} 条 -> {OUT_DIR}")
try:
    inp = unreal.IKRetargetBatchOperationInputs()
    inp.set_editor_property("assets_to_retarget", ads)
    inp.set_editor_property("ik_retarget_asset", rtg)
    inp.set_editor_property("target_path", OUT_DIR)
    inp.set_editor_property("use_source_path", False)
    inp.set_editor_property("include_referenced_assets", False)
    inp.set_editor_property("overwrite_existing_files", True)
    inp.set_editor_property("search", "A_LOL_Darius_")
    inp.set_editor_property("replace", "A_Darius_")
    res = unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
    L(f"[RETGT] 产物 {len(res) if res else 0} 项")
    for r in (res or []):
        L(f"[RETGT]   {r.package_name if hasattr(r, 'package_name') else r}")
except Exception as ex:
    LW(f"[RETGT] err {ex}")

for p in (TGT_RUN, TGT_IDLE):
    if eal.does_asset_exist(p):
        L(f"[RETGT] save_asset({p}) = {eal.save_asset(p, only_if_is_dirty=False)}")
    else:
        LW(f"[RETGT] 产物缺失: {p}")

# ============================================================ 4. 量三件事
def probe(clip_path, bones, n=11):
    a = unreal.load_object(None, clip_path)
    if not a:
        LW(f"[PROBE] 缺 {clip_path}")
        return None, None, None
    keys = a.get_editor_property("number_of_sampled_keys")
    frames = sorted(set(int(round(i * (keys - 1) / (n - 1))) for i in range(n)))
    opts = unreal.AnimPoseEvaluationOptions()
    rows = {}
    for f in frames:
        try:
            pose = APE.get_anim_pose_at_frame(a, f, opts)
        except Exception as ex:
            LW(f"[PROBE] pose err {ex}")
            return None, None, None
        row = {}
        for b in bones:
            try:
                row[b] = APE.get_bone_pose(pose, unreal.Name(b), unreal.AnimPoseSpaces.WORLD).translation
            except Exception:
                pass
        rows[f] = row
    unit = 1.0
    pz = rows[frames[0]].get("pelvis") or rows[frames[0]].get("Pelvis")
    if pz is not None and abs(pz.z) < 5.0:
        unit = 100.0
    return frames, rows, unit


def metrics(tag, clip, bones, pa, pb, ta, tb, va, vb):
    frames, rows, unit = probe(clip, bones)
    if rows is None:
        return None
    r0 = rows[frames[0]]
    def g(b):
        return r0.get(b)
    out = {"tag": tag, "clip": clip, "unit": unit, "frames": len(frames)}
    try:
        fa, fb = g(ta), g(tb)
        if fa and fb:
            out[f"{ta}_x"] = round(fa.x * unit, 2)
            out[f"{tb}_x"] = round(fb.x * unit, 2)
            out["dx_lr"] = round((fa.x - fb.x) * unit, 2)
        if g(pa) and g(ta):
            tv = (g(pa) - g(ta)) * unit
            n = tv.length()
            out["toe_vec"] = [round(tv.x / n, 3), round(tv.y / n, 3), round(tv.z / n, 3)] if n > 1e-6 else None
            out["toe_dot_negY"] = round(-out["toe_vec"][1], 3) if out["toe_vec"] else None
        # 与朝向无关的左右判定：left_axis = Z × forward
        if g(pa) and g(ta) and g(ta) and g(tb):
            fwd = g(pa) - g(ta)
            fwd = unreal.Vector(fwd.x, fwd.y, 0.0)
            if fwd.length() > 1e-6:
                fwd.normalize()
                zax = unreal.Vector(0.0, 0.0, 1.0)
                lft = zax.cross(fwd)
                d = g(ta) - g(tb)
                out["lr_score"] = round(lft.dot(unreal.Vector(d.x, d.y, 0.0)) * unit, 2)
                # 持斧手左右一致性：hand_r 相对 pelvis 在 left_axis 上的投影
                hv = r0.get("hand_r") or r0.get("R_Hand")
                pv = r0.get("pelvis") or r0.get("Pelvis")
                if hv is not None and pv is not None:
                    dv = hv - pv
                    out["hand_score"] = round(lft.dot(unreal.Vector(dv.x, dv.y, 0.0)) * unit, 2)
    except Exception as ex:
        out["vec_err"] = str(ex)
    spans = {}
    for b in (ta, tb):
        pts = [rows[f][b] for f in frames if b in rows[f]]
        if len(pts) >= 2:
            spans[b] = round(max((p - pts[0]).length() for p in pts) * unit, 2)
    out["travel_cm"] = spans
    if g("pelvis") or g("Pelvis"):
        pv = g("pelvis") or g("Pelvis")
        out["pelvis_z"] = round(pv.z * unit, 2)
    L(f"[METRIC {tag}] {json.dumps(out, ensure_ascii=False)}")
    return out


L("=== 源基线 (run / idle1) ===")
src_run = metrics("SRC_run", SRC_RUN, SRC_BONES, "L_Toe", "R_Toe", "L_Foot", "R_Foot", "L_Foot", "R_Foot")
src_idle = metrics("SRC_idle", SRC_IDLE, SRC_BONES, "L_Toe", "R_Toe", "L_Foot", "R_Foot", "L_Foot", "R_Foot")

L("=== 重定向产物 ===")
tgt_run = metrics("TGT_run", TGT_RUN, TGT_BONES, "ball_l", "ball_r", "foot_l", "foot_r", "ball_l", "ball_r")
tgt_idle = metrics("TGT_idle", TGT_IDLE, TGT_BONES, "ball_l", "ball_r", "foot_l", "foot_r", "ball_l", "ball_r")

# ============================================================ 5. PASS/FAIL
L("=== 验收 ===")
if src_run and tgt_run:
    def chk(name, ok, detail):
        L(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        return ok
    r = []
    r.append(chk("朝向一致(脚尖同向)",
                 abs(tgt_run.get("toe_dot_negY", 0) - src_run.get("toe_dot_negY", 9)) < 0.5,
                 f"源 dot(-Y)={src_run.get('toe_dot_negY')} / 产物 dot(-Y)={tgt_run.get('toe_dot_negY')}"))
    r.append(chk("左右次序一致(朝向无关)",
                 (src_run.get("lr_score", 0) > 0) == (tgt_run.get("lr_score", 0) > 0),
                 f"源 lr_score={src_run.get('lr_score')} / 产物 lr_score={tgt_run.get('lr_score')}"))
    st = (src_run.get("travel_cm") or {}).get("L_Foot", 0)
    tt = (tgt_run.get("travel_cm") or {}).get("foot_l", 0)
    r.append(chk("运动量传递", tt >= 0.5 * st, f"源 L 位移={st}cm / 产物 foot_l 位移={tt}cm"))
    pz = tgt_run.get("pelvis_z", -999)
    r.append(chk("站立不翻/不离地", 60.0 <= pz <= 160.0, f"产物 pelvis_z={pz}cm (期望 60~160)"))
    L(f"[VERDICT] {mode} -> {'ALL PASS' if all(r) else 'HAS FAIL'}")

L("RTG_FIX_VERIFY_DONE")
