# -*- coding: utf-8 -*-
"""给**源** IK Rig 补上缺失的链 —— 根因级修法。

## 为什么
`auto_align_all_bones(CHAIN_TO_CHAIN)` 靠「链里子骨的方向」定朝向，所以：
- **链尾骨**没有子骨 ⇒ 定不出方向 ⇒ 偏移恒为 **0**；
- **没有源对应的目标链**里的骨 ⇒ 同样对不上。

`ik_50`/实测已查明两边的链清单：
| | 目标 IK_Darius_Target | 源 IK_LOL_Source |
| :--- | ---: | ---: |
| 链数 | **30** | **10** |
| 内容 | Spine/Neck/Head/Pelvis/Left·RightLeg/Left·RightFoot/Left·RightClavicle/Left·RightArm + **手指 10 条 + 掌骨 8 条** | Spine/Neck/Head/Pelvis/Left·RightLeg/Left·RightClavicle/Left·RightArm |

差的 **20 条** = 手指 10 + 掌骨 8 + **LeftFoot / RightFoot 2**。
⇒ **`foot_l` / `foot_r` 的偏移恒为 0 就是这么来的**，也正是脚掌拧 66.6°/44.4° 的病根。
（我用 `ik_53` 的解析 twist 修正绕过去了，但那是补丁；这里是修根。）

## 做法
1. 用 `unreal.IKRigController.add_retarget_chain(name, start, end, goal)` 给**源**补链。
2. 用 `IKRetargeterController.set_source_chain(源链, 目标链)` 把新链接到目标链上。
3. 存盘（**IK Rig 和 Retargeter 都要存**）。

⚠️ 本脚本只加**源侧的脚链**（保守起步）；手指/掌骨要不要补是另一个决定（会显著增大链数）。
⚠️ 改前已备份：`Saved/Backup_ikrig/*.uasset.bak`。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
kc = unreal.IKRigController
E = unreal.RetargetSourceOrTarget

IK_SRC = "/Game/Character/Darius/Retarget/IK_LOL_Source"
IK_TGT = "/Game/Character/Darius/Retarget/IK_Darius_Target"
RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"

# 要补的源链：(链名, 起始骨, 结束骨, 目标链名)
NEW_CHAINS = [
    ("LeftFoot", "L_Foot", "L_Toe", "LeftFoot"),
    ("RightFoot", "R_Foot", "R_Toe", "RightFoot"),
]

L("add_retarget_chain 签名：%s" % kc.add_retarget_chain.__doc__)
L("get_retarget_chain_start_bone 签名：%s" % kc.get_retarget_chain_start_bone.__doc__)
L("set_source_chain 签名：%s"
  % unreal.IKRetargeterController.set_source_chain.__doc__)

ik_src = eal.load_asset(IK_SRC)
ik_tgt = eal.load_asset(IK_TGT)
rtg = eal.load_asset(RTG)
cs = kc.get_controller(ik_src)
ctrl = unreal.IKRetargeterController.get_controller(rtg)

L("")
L("################ 1. 现有源链的起止骨（确认参数形式）")
for nm in ("LeftLeg", "RightLeg", "LeftArm", "Spine"):
    for arg in (nm, unreal.Name(nm)):
        try:
            s = cs.get_retarget_chain_start_bone(arg)
            e = cs.get_retarget_chain_end_bone(arg)
            L("   %-10s (arg=%s) %s -> %s" % (nm, type(arg).__name__, s, e))
            break
        except Exception as ex:
            LW("   %-10s (arg=%s) 失败: %s" % (nm, type(arg).__name__, str(ex)[:80]))

L("")
L("################ 2. 给源补链")
before = len(cs.get_retarget_chains())
L("   补前源链数 = %d" % before)
for name, start, end, _tgt in NEW_CHAINS:
    done = False
    for args in ((name, start, end, ""), (name, start, end),
                 (unreal.Name(name), unreal.Name(start), unreal.Name(end), "")):
        try:
            r = cs.add_retarget_chain(*args)
            L("   add_retarget_chain%s -> %s" % (args, r))
            done = True
            break
        except Exception as ex:
            LW("   add_retarget_chain%s 失败: %s" % (args, str(ex)[:110]))
    if not done:
        LW("   !! %s 没能加上" % name)
after = len(cs.get_retarget_chains())
L("   补后源链数 = %d" % after)

L("")
L("################ 3. 接链（源链 -> 目标链）")
for name, start, end, tgt in NEW_CHAINS:
    ok = False
    for args in ((name, tgt), (name, tgt, "")):
        try:
            r = ctrl.set_source_chain(*args)
            L("   set_source_chain%s -> %s ；读回 %s" % (args, r, ctrl.get_source_chain(tgt)))
            ok = True
            break
        except Exception as ex:
            LW("   set_source_chain%s 失败: %s" % (args, str(ex)[:110]))
    if not ok:
        LW("   !! %s -> %s 没接上" % (name, tgt))

L("")
L("################ 4. 存盘（IK Rig 与 Retargeter 都要存）")
for p in (IK_SRC, IK_TGT, RTG):
    try:
        L("   save %-20s -> %s" % (p.split("/")[-1], eal.save_asset(p, only_if_is_dirty=False)))
    except Exception as ex:
        LW("   save %s 失败: %s" % (p, str(ex)[:110]))
L("=== DONE ===")
