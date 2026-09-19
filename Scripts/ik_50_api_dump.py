# -*- coding: utf-8 -*-
"""把 IK Retargeter / IK Rig 的 Python API 全量列出来。

## 为什么需要它
`ik_44` 探到 `get_all_chain_settings()` 返回**空数组**，于是「链」这条线一直没走通。
但 `HANDOFF.md §5` 把「给源 IK Rig 补上缺失的链（锁骨 / 颈 / 头 / 手 / 脚 / 脚趾）」
列为头号未决项 —— 这是**根因级**的修法：
`auto_align_all_bones(CHAIN_TO_CHAIN)` 靠「链里子骨方向」定朝向，
目标 29 条链里约 20 条**没有源对应**，那些骨自然对不上。

要动链就必须知道**到底有哪些接口可用**。本脚本把 `dir()` 出来的成员连同
`help()` 签名一起打印，一次问清楚，别再一次次猜。
"""
import unreal

L = unreal.log
eal = unreal.EditorAssetLibrary

RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
IK_SRC = "/Game/Character/Darius/Retarget/IK_LOL_Source"
IK_TGT = "/Game/Character/Darius/Retarget/IK_Darius_Target"


def dump(obj, tag, filt=None):
    names = sorted(n for n in dir(obj) if not n.startswith("_"))
    if filt:
        names = [n for n in names if any(f in n for f in filt)]
    L("")
    L("################ %s —— %d 个成员" % (tag, len(names)))
    for n in names:
        doc = ""
        try:
            d = getattr(obj, n).__doc__
            if d:
                doc = d.strip().splitlines()[0][:110]
        except Exception:
            pass
        L("   %-52s %s" % (n, doc))


rtg = eal.load_asset(RTG)
L("retargeter = %s" % (rtg.get_name() if rtg else "NOT FOUND"))
if rtg is None:
    raise SystemExit("找不到 IK Retargeter")

ctrl = unreal.IKRetargeterController.get_controller(rtg)
L("controller = %s" % ctrl)

dump(ctrl, "IKRetargeterController")
dump(rtg, "IKRetargeter 资产")
dump(unreal.IKRetargeter, "unreal.IKRetargeter (类)")

# 只看和「链 / 姿势」有关的，避免刷屏
KEY = ("chain", "pose", "align", "bone", "rig", "map", "reset", "root", "pelvis")
dump(ctrl, "IKRetargeterController（关键字过滤）", KEY)

for p in (IK_SRC, IK_TGT):
    o = eal.load_asset(p)
    L("")
    L("################ %s -> %s" % (p.split("/")[-1], o.get_class().get_name() if o else "NOT FOUND"))
    if o:
        dump(o, p.split("/")[-1], KEY)

# 姿势名 / 当前姿势（这些是「链之外」的第二条根因线索）
for fn in ("get_retarget_pose_names", "get_current_retarget_pose_name",
           "get_retarget_pose_name", "get_retarget_root_bone_name",
           "get_num_retarget_poses"):
    try:
        L("   ctrl.%s() -> %s" % (fn, getattr(ctrl, fn)()))
    except Exception as ex:
        L("   ctrl.%s() 失败: %s" % (fn, str(ex)[:120]))

L("=== DONE ===")
