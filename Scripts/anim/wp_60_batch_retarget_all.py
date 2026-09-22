# -*- coding: utf-8 -*-
"""wp_60 —— 批量重定向 LoL 全部动画到 Animations/LOL_Retarget，并**同一步**修掉最外层骨假 scale 轨。

背景
----
RTG 的 Export / 批量重定向会给骨架最外层骨 `darius_godking_mesh_LOD0_Skeleton`
写一条 **scale = 1** 的假轨（正常应回落 rest = **100**）。同一根因造成两个症状：
  ① 角色被渲染成 1.85cm（"人物特别小"）
  ② Chaos Cloth 的约束距离按 100× 写死 ⇒ 披风被撑爆、拧成一团
⇒ 所以「导出」和「删假轨」必须成对执行，本脚本把它合成一步，避免忘记。

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_60_batch_retarget_all.py

⚠️ 导出只是流水线第 1 步，后面还有两步缺一不可：
    2) 烘焙握法   -> Scripts/anim/wp_50_bake_weapon_grip.py（自动配对；跳过源空片段）
    3) 修整体朝向 -> Scripts/anim/wp_72_fix_facing.py
       （RTG 的 mirror 配方会让整体多转 180°，产物朝 +Y 而骨架正常前方是 −Y ⇒ 背对玩家）
"""
import json

import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary
L = unreal.log
LW = unreal.log_warning

SRC_DIR = "/Game/Character/Darius/LOL_Source"
OUT_DIR = "/Game/Character/Darius/Animations/LOL_Retarget"
RTG = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
BP = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
OUTER = "darius_godking_mesh_LOD0_Skeleton"
REPORT = "E:/UE/Fight/Saved/Attack/wp60_batch_retarget.json"

# ---------------------------------------------------------------- 1. 收集源动画
src = []
for p in sorted(eal.list_assets(SRC_DIR, recursive=False, include_folder=False)):
    if "A_LOL_Darius_" not in p or "BindPose" in p:
        continue
    ad = eal.find_asset_data(p)
    if ad:
        src.append((p, ad))
L("=" * 78)
L("=== 源动画 %d 条 ===" % len(src))
L("=" * 78)
for p, _ in src:
    L("   %s" % p.rsplit("/", 1)[-1])

if not src:
    LW("!! 没找到源动画")
    raise SystemExit(1)

# ---------------------------------------------------------------- 2. 批量重定向
if not eal.does_directory_exist(OUT_DIR):
    eal.make_directory(OUT_DIR)

rtg = unreal.load_object(None, RTG)
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [ad for _, ad in src])
inp.set_editor_property("ik_retarget_asset", rtg)
inp.set_editor_property("target_path", OUT_DIR)
inp.set_editor_property("use_source_path", False)
inp.set_editor_property("include_referenced_assets", False)
inp.set_editor_property("overwrite_existing_files", True)
inp.set_editor_property("search", "A_LOL_Darius_")
inp.set_editor_property("replace", "A_Darius_")
L("")
L("=== 批量重定向 -> %s ===" % OUT_DIR)
res = unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
L("产物 %d 项" % (len(res) if res else 0))

# ---------------------------------------------------------------- 3. 删假 scale 轨
L("")
L("=== 修最外层骨假 scale 轨 ===")
fixed, bad, ok_cnt, total = [], [], 0, 0
for p in sorted(eal.list_assets(OUT_DIR, recursive=False, include_folder=False)):
    o = unreal.load_object(None, p)
    if not isinstance(o, unreal.AnimSequence):
        continue
    total += 1
    ctrl = o.get_editor_property("controller")
    # ⚠️ 必须用 **data_model_interface**：`model_interface` 返回的骨名列表里**不含**最外层骨，
    #    用整名匹配会一条都删不掉（本脚本第一版实测"删掉假轨 0 条"）。改用子串匹配。
    try:
        names = [str(x) for x in
                 o.get_editor_property("data_model_interface").get_bone_track_names()]
    except Exception:
        names = []
    idx = next((i for i, n in enumerate(names) if "lod0_skeleton" in n.lower()), -1)
    if idx >= 0:
        try:
            ctrl.remove_bone_track(names[idx])
            fixed.append(o.get_name())
        except Exception as ex:
            LW("   %s remove 失败: %s" % (o.get_name(), str(ex)[:60]))
    sc = None
    try:
        sc = AL.get_bone_pose_for_frame(o, unreal.Name(OUTER), 0, False).scale3d.x
    except Exception:
        pass
    if sc is not None and abs(sc - 100.0) < 1e-3:
        ok_cnt += 1
    else:
        bad.append([o.get_name(), sc])
    eal.save_asset(p, only_if_is_dirty=False)

L("   产物总数 %d；删掉假轨 %d 条" % (total, len(fixed)))
L("   复核 scale == 100 通过 %d 条；异常 %d 条 %s" % (ok_cnt, len(bad), bad[:8]))

# ---------------------------------------------------------------- 4. BP socket 复查
# ⚠️ 2026-09-22 实测：本段读数可能与实际不符——用户已把 Parent Socket 改成 weapon_jnt_l
#    （uasset 字符串 + PIE 斧头位置双重验证），但这里打印出 hand_rSocket。
#    SubobjectData 枚举到的对象不一定是 SCS 生效模板，勿据此让用户重改。
#    PIE 表现才是权威：斧头在 weapon_jnt_l 上位置正常。
sock = None
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
bp = unreal.load_object(None, BP)
for h in sub.k2_gather_subobject_data_for_blueprint(bp):
    dd = sub.k2_find_subobject_data_from_handle(h)
    oo = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(dd)
    if isinstance(oo, unreal.StaticMeshComponent) and "Weapon" in oo.get_name():
        sock = str(oo.get_attach_socket_name())
        v = oo.get_editor_property("relative_location")
        s = oo.get_editor_property("relative_scale3d")
        L("")
        L("=== BP WeaponAxe ===")
        L("   socket = '%s'    (此读数可能是 CDO 旧值; 权威判定看 PIE 斧头位置/uasset)" % sock)
        L("   rel_loc = (%.6f, %.6f, %.6f)   rel_scale = (%.4f, %.4f, %.4f)" % (
            v.x, v.y, v.z, s.x, s.y, s.z))

with open(REPORT, "w", encoding="utf-8") as f:
    json.dump({"src_count": len(src), "out_dir": OUT_DIR, "target_total": total,
               "fixed_tracks": fixed, "scale_ok": ok_cnt,
               "scale_bad": [[n, str(s)] for n, s in bad],
               "weapon_socket": sock}, f, indent=1, ensure_ascii=False)
L("")
L("已写 %s" % REPORT)
L("WP60_DONE")
