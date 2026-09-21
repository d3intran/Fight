# -*- coding: utf-8 -*-
"""
wp_107_fk_set.py —— 读 / 改 FK op 每条链的 rotation_mode（修左右腿摆幅不对称）

背景（wp_94 / wp_102 实测）
--------------------------
    源 run   左右脚摆幅比 0.92（对称），pelvis 起伏 27.9
    产物 run  左右脚摆幅比 **1.44 ~ 1.77**（左脚 71cm / 右脚 47cm），pelvis 起伏 33.9

嫌疑点（wp_104 / wp_105 实测）
-----------------------------
    op[1] FK Chains 的 rotation_mode = **INTERPOLATED**（按源/目标链长比例**重算**旋转）
    源/目标腿链骨数不同：TARGET `thigh_l→foot_l`、SOURCE `L_Hip→L_Foot`
    ⇒ 骨长比例不同就会被放大/缩小，左右两侧比例不一致就产生不对称

    `RetargetRotationMode` 取值：INTERPOLATED / MATCH_CHAIN / MATCH_SCALED_CHAIN /
    NONE / ONE_TO_ONE / ONE_TO_ONE_REVERSED
    `FKChainRotationMode` 额外有 COPY_LOCAL

API（wp_106 + rtg_31 实测；注意 rotation_mode **不在** TargetChainSettings 里）
------------------------------------------------------------------------------
    oc  = IKRetargeterController.get_op_controller(1)          # op[1] = "FK Chains"
    st  = oc.get_settings()
    arr = st.get_editor_property("chains_to_retarget")         # Array
    it  = arr[j]
    it.get_editor_property("target_chain_name" / "rotation_mode" / "translation_mode")
    it.set_editor_property("rotation_mode", unreal.RetargetRotationMode.ONE_TO_ONE)
    oc.set_settings(st)                                        # 写回

模式：Saved/Attack/wp107_mode.txt
    第 1 行 = dry（默认）/ apply / restore
    第 2 行 = 目标模式 one_to_one（默认）/ copy_local / interpolated / match_chain / match_scaled_chain

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_107_fk_set.py
"""
import json

import unreal

L = unreal.log
LW = unreal.log_warning

RTG = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
MODE_FILE = "E:/UE/Fight/Saved/Attack/wp107_mode.txt"
BASELINE = "E:/UE/Fight/Saved/Attack/wp107_baseline.json"
OUT = "E:/UE/Fight/Saved/Attack/wp107_fk_set.json"

TARGET_CHAINS = ["LeftLeg", "RightLeg", "LeftFoot", "RightFoot"]
PROPS = ("target_chain_name", "source_chain_name", "rotation_mode", "translation_mode",
         "rotation_alpha", "translation_alpha", "pole_vector_mode", "pole_vector_weight",
         "copy_pose_using_fk", "drive_ik_goal")

MODE_MAP = {
    "one_to_one": "ONE_TO_ONE",
    "copy_local": "COPY_LOCAL",
    "interpolated": "INTERPOLATED",
    "match_chain": "MATCH_CHAIN",
    "match_scaled_chain": "MATCH_SCALED_CHAIN",
    "none": "NONE",
    "one_to_one_reversed": "ONE_TO_ONE_REVERSED",
}


def read_mode_file():
    try:
        with open(MODE_FILE, encoding="utf-8") as f:
            lines = [x.strip().lower() for x in f.read().splitlines() if x.strip()]
    except Exception:
        lines = []
    return (lines[0] if lines else "dry"), (lines[1] if len(lines) > 1 else "one_to_one")


ACTION, WANT = read_mode_file()

rtg = unreal.load_object(None, RTG)
c = unreal.IKRetargeterController.get_controller(rtg)

# 定位 FK op
fk_idx = None
for i in range(c.get_num_retarget_ops()):
    if "FK" in str(c.get_op_name(i)):
        fk_idx = i
        break
if fk_idx is None:
    raise RuntimeError("找不到 FK Chains op")

oc = c.get_op_controller(fk_idx)
st = oc.get_settings()
arr = st.get_editor_property("chains_to_retarget")

L("=" * 108)
L("=== wp_107  FK op[%d] chains_to_retarget   action=%s   want=%s ===" % (fk_idx, ACTION, WANT))
L("=" * 108)
L("   数组长度 = %d" % len(arr))

current = {}
for it in arr:
    d = {}
    for p in PROPS:
        try:
            d[p] = str(it.get_editor_property(p))
        except Exception:
            pass
    tn = d.get("target_chain_name", "?")
    current[tn] = d
    mark = " <<<" if tn in TARGET_CHAINS else ""
    L("   %-24s rot=%-32s trans=%-34s%s" % (
        tn, d.get("rotation_mode", "?"), d.get("translation_mode", "?"), mark))

result = {"action": ACTION, "want": WANT, "op_index": fk_idx, "current": current, "changed": []}

if ACTION == "dry":
    L("")
    L("==> DRY-RUN。把 %s 写成两行：apply / one_to_one" % MODE_FILE)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, default=str, indent=1)
    L("已写 %s" % OUT)
    L("WP107_DONE")
else:
    try:
        with open(BASELINE, encoding="utf-8") as f:
            baseline = json.load(f)
    except Exception:
        baseline = {}
    if not baseline:
        baseline = {k: v.get("rotation_mode") for k, v in current.items()
                    if v.get("rotation_mode") and v.get("rotation_mode") != "?"}
        with open(BASELINE, "w", encoding="utf-8") as f:
            json.dump(baseline, f, ensure_ascii=False, default=str, indent=1)
        L("   baseline 已存 -> %s" % BASELINE)

    changed = 0
    for it in arr:
        try:
            tn = str(it.get_editor_property("target_chain_name"))
        except Exception:
            continue
        if tn not in TARGET_CHAINS:
            continue
        if ACTION == "restore":
            raw = baseline.get(tn)
            if raw is None:
                continue
            key = str(raw).split(".")[-1]
            desc = "restore"
        else:
            key = MODE_MAP.get(WANT, "ONE_TO_ONE")
            desc = WANT
        # 🔴 rotation_mode 的真实类型是 FKChainRotationMode（不是 RetargetRotationMode）；
        #    先取它，取不到再退到 RetargetRotationMode。顺序反了会 "Failed to convert type"。
        val = getattr(unreal.FKChainRotationMode, key, None)
        if val is None:
            val = getattr(unreal.RetargetRotationMode, key, None)
        if val is None:
            LW("   %-14s 枚举 %s 取不到" % (tn, key))
            continue
        try:
            it.set_editor_property("rotation_mode", val)
            changed += 1
            result["changed"].append({"chain": tn, "mode": key})
            L("   %-14s rotation_mode -> %s   (%s)" % (tn, val, desc))
        except Exception as ex:
            LW("   %-14s 写入失败: %s" % (tn, str(ex)[:90]))

    if changed:
        try:
            oc.set_settings(st)
            L("   set_settings OK")
        except Exception as ex:
            LW("   set_settings 失败: %s" % str(ex)[:90])
        ok = unreal.EditorAssetLibrary.save_loaded_asset(rtg)
        L("   已改 %d 条，资产保存=%s" % (changed, ok))
    else:
        L("   没有改动")

    L("")
    L("==> 下一步：wp_60_batch_retarget_all.py 重导，再跑 wp_102 看对称度")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, default=str, indent=1)
    L("已写 %s" % OUT)
    L("WP107_DONE")
