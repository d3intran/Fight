# -*- coding: utf-8 -*-
"""把两套骨架的完整骨列表 + 链定义导出成文本，作为重新规划的底座。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

OUT = "E:/UE/Fight/Saved/Retarget/Clean/skeleton_facts.txt"
RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"

lines = []


def W(s):
    lines.append(s)
    L(s)


def dump_skeleton(tag, path):
    sk = eal.load_asset(path)
    W("")
    W("=" * 78)
    W("### %s : %s" % (tag, path))
    W("=" * 78)
    if sk is None:
        W("  <加载失败>")
        return
    W("  类 = %s" % sk.get_class().get_name())
    names = None
    for fn in ("get_bone_names",):
        pass
    try:
        rp = sk.get_reference_pose()
        names = [str(x) for x in rp.get_bone_names()]
    except Exception as ex:
        W("  get_reference_pose/get_bone_names 失败: %s" % str(ex)[:120])
    if names is None:
        return
    W("  骨数 = %d" % len(names))
    # 参考姿势的局部平移模长，按模长排序便于识别末端/微骨
    rows = []
    for n in names:
        try:
            t = rp.get_bone_pose(n, unreal.AnimPoseSpaces.LOCAL)
            tr = t.translation
            m = (tr.x * tr.x + tr.y * tr.y + tr.z * tr.z) ** 0.5
            rows.append((n, m, tr.x, tr.y, tr.z, t.scale3d.x))
        except Exception:
            rows.append((n, -1.0, 0.0, 0.0, 0.0, 0.0))
    W("")
    W("  %-42s %10s %10s %10s %10s %8s" % ("bone", "|T|", "Tx", "Ty", "Tz", "scaleX"))
    for n, m, tx, ty, tz, sx in rows:
        W("  %-42s %10.4f %10.3f %10.3f %10.3f %8.3f" % (n, m, tx, ty, tz, sx))


dump_skeleton("源骨架（净化后 59 骨）", "/Game/Character/Darius/LOL_Source/SK_LOL_Darius_Skeleton")
dump_skeleton("目标骨架（2XKO 309 骨）", "/Game/Character/Darius/SK_Darius_GodKing_Skeleton")

# ---------------------------------------------------------------- IK Rig / 链
W("")
W("=" * 78)
W("### 两套 IK Rig 的链定义")
W("=" * 78)
for tag, p in (("源 IK_LOL_Source", "/Game/Character/Darius/Retarget/IK_LOL_Source"),
               ("目标 IK_Darius_Target", "/Game/Character/Darius/Retarget/IK_Darius_Target")):
    rig = eal.load_asset(p)
    W("")
    W("--- %s" % tag)
    if rig is None:
        W("  <加载失败>")
        continue
    ctrl = unreal.IKRigController.get_controller(rig)
    try:
        W("  retarget root = %s" % ctrl.get_retarget_root())
    except Exception as ex:
        W("  retarget root 读取失败: %s" % str(ex)[:80])
    chains = ctrl.get_retarget_chains() or []
    W("  链数 = %d" % len(chains))
    for c in chains:
        try:
            nm = str(c.get_editor_property("chain_name"))
            s = ctrl.get_retarget_chain_start_bone(nm)
            e = ctrl.get_retarget_chain_end_bone(nm)
            W("    %-22s %-28s -> %s" % (nm, s, e))
        except Exception as ex:
            W("    <err %s>" % str(ex)[:70])

# ---------------------------------------------------------------- op 栈
W("")
W("=" * 78)
W("### 当前 op 栈状态")
W("=" * 78)
rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)
for i in range(ctrl.get_num_retarget_ops()):
    W("  [%d] %-20s enabled=%s" % (i, ctrl.get_op_name(i), ctrl.get_retarget_op_enabled(i)))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
L("")
L("已写出 = %s  (%d 行)" % (OUT, len(lines)))
L("=== DONE ===")
