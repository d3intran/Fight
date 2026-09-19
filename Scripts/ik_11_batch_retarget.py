# -*- coding: utf-8 -*-
"""
ik_11_batch_retarget.py —— 用 IK Retargeter 把源动画批量重定向到目标骨架

前置：UE 编辑器必须处于运行中（经 ue_remote 执行）。
      若报 ConnectionResetError，说明编辑器已崩溃/关闭，需先重启编辑器。

--------------------------------------------------------------------
⚠️ 踩坑记录（务必保留）：资产路径格式
  `EditorAssetLibrary.list_assets()` 返回的是 **"package.object" 形式**
      /Game/Character/Darius/LOL_Source/A_LOL_run.A_LOL_run
  而 `find_asset_data()` / `rename_asset()` 需要的是 **纯 package 路径**
      /Game/Character/Darius/LOL_Source/A_LOL_run

  把带 `.object` 的字符串拼进新路径再交给 `rename_asset()`，UE 会直接
  **EXCEPTION_ACCESS_VIOLATION 崩溃**（编辑器整个挂掉，本文件的前身实测踩过）。
  ⇒ 一切路径先 `pkg = a.split(".")[0]`。

⚠️ 另一个坑：`rename_asset()` 即使传入合法路径，其效果在**未 save 前也可能丢失**
  （编辑器在后续操作中重载旧状态时会回退）。要改名就 rename + save 成对做。
  本脚本因此**不做源资产改名**，改用 batch inputs 里的 search/replace 控制输出名。
--------------------------------------------------------------------

输出契约：
  源  A_LOL_*  (46 个，位于 /Game/Character/Darius/LOL_Source)
  目标 /Game/Character/Darius/Anims_TP/A_Darius_*（33 骨 -> 309 骨，保留原帧数）
"""
import unreal
import json
import os

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

SRC_DIR = "/Game/Character/Darius/LOL_Source"
# 🔁 输出目录可被 Saved/retarget_cycle.json 覆盖 —— 实验回路靠「每轮换一个新目录」
#    来绕开「在编辑器内删资产会崩」，见下方注释。
CFG = "E:/UE/Fight/Saved/retarget_cycle.json"
OUT_DIR = "/Game/Character/Darius/Anims_TP"
if os.path.isfile(CFG):
    try:
        with open(CFG, encoding="utf-8") as fh:
            OUT_DIR = json.load(fh).get("out_dir") or OUT_DIR
    except Exception as ex:
        LW("读 %s 失败: %s" % (CFG, ex))
RTG_PATH = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"

# 源名里这段前缀换成目标前缀，得到干净的输出名
SEARCH = "SK_LOL_Dariusskinned_mesh_darius_skin15_"
REPLACE = "A_Darius_"

# 只测这几个（None = 全部）。先单跑验证链路，再放开。
TEST_KEYS = ["run", "idle1"]


def pkg_of(p):
    """list_assets 返回 'package.object'，这里取纯 package 路径。"""
    return p.split(".")[0]


# ---------------------------------------------------------------- 收集源动画
all_assets = eal.list_assets(SRC_DIR, recursive=False, include_folder=False)
anims = []
for a in all_assets:
    pkg = pkg_of(a)
    o = unreal.load_asset(pkg)
    if o is not None and o.get_class().get_name() == "AnimSequence":
        anims.append(pkg)
anims.sort()
L("源动画 = %d 个" % len(anims))
for p in anims[:3]:
    L("   %s" % p.split("/")[-1])

selected = anims
if TEST_KEYS:
    selected = [p for p in anims if any(p.split("/")[-1].endswith(k) for k in TEST_KEYS)]
L("本次处理 = %d 个：%s" % (len(selected), [p.split("/")[-1] for p in selected]))

if not selected:
    raise SystemExit("没有选中的动画")

# ---------------------------------------------------------------- 构造 inputs
rtg = eal.load_asset(RTG_PATH)
L("")
L("retargeter = %s" % (rtg.get_name() if rtg else "NOT FOUND"))
if rtg is None:
    raise SystemExit("找不到 IK Retargeter")

# ---------------------------------------------------------------- 输出目录必须为空
# ⚠️ run_batch_retarget **不幂等**：若输出目录里已存在同名资产，它会先把新资产
#    改名成 <name>1，再 Force Delete 旧包，实测在第二个包上
#    EXCEPTION_ACCESS_VIOLATION，**整个编辑器崩溃**（2026-09-18 实测）。
#
# 🔴 2026-09-19 实测第二条崩溃路径（更狠）：
#    **用 `EditorAssetLibrary.delete_asset` 去清 AnimSequence 会直接崩编辑器**
#    （日志：`Force Deleting 1 Package(s)` → `Detected inconsistencies between
#    reference gathering algorithms. Switching 'Editor.UseLegacyGetReferencersForDeletion' on`
#    → EXCEPTION_ACCESS_VIOLATION，调用栈里是 EditorScriptingUtilities → UnrealEd）。
#    原版脚本在这里就是「先删再跑」，于是**每次跑都杀掉编辑器**，而且不报任何 Python 异常。
#
# ⇒ 本脚本**不再自己删**。输出目录非空就**大声中止**，让操作者用磁盘级清理：
#      deno task editor:down
#      rm -rf Content/Character/Darius/Anims_TP
#      deno task editor:up -- --hold
#    磁盘级清理不经过资产注册表，零风险；而且反正 `ik_31` 也要求新会话。
if eal.does_directory_exist(OUT_DIR):
    _old = eal.list_assets(OUT_DIR, recursive=False, include_folder=False)
    if _old:
        LW("!! 输出目录 %s 非空（%d 个资产）。" % (OUT_DIR, len(_old)))
        LW("   在编辑器内删除 AnimSequence 会让编辑器崩溃（见本文件注释），故本脚本拒绝继续。")
        LW("   请先做磁盘级清理：")
        LW("     deno task editor:down")
        LW("     rm -rf Content/Character/Darius/Anims_TP")
        LW("     deno task editor:up -- --hold")
        raise SystemExit(1)
    L("输出目录 %s 存在但为空，可直接写入。" % OUT_DIR)

if not eal.does_directory_exist(OUT_DIR):
    L("make_directory %s -> %s" % (OUT_DIR, eal.make_directory(OUT_DIR)))

ads = []
for p in selected:
    ad = eal.find_asset_data(p)
    if ad is None:
        LW("   find_asset_data 失败: %s" % p)
        continue
    ads.append(ad)
L("有效 AssetData = %d" % len(ads))

inp = unreal.IKRetargetBatchOperationInputs()
for k, v in (
    ("assets_to_retarget", ads),
    ("ik_retarget_asset", rtg),
    ("target_path", OUT_DIR),
    ("use_source_path", False),
    ("include_referenced_assets", False),
    ("overwrite_existing_files", True),
    ("search", SEARCH),
    ("replace", REPLACE),
):
    try:
        inp.set_editor_property(k, v)
    except Exception as ex:
        LW("   set %s 失败: %s" % (k, str(ex)[:120]))

L("")
L("=== run_batch_retarget ===")
try:
    res = unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
    L("   返回 %d 项" % (len(res) if res else 0))
    for r in (res or []):
        try:
            L("      -> %s" % r.package_name)
        except Exception:
            L("      -> %s" % r)
except Exception as ex:
    LW("   失败: %s" % str(ex).replace("\n", " ")[:400])

# ---------------------------------------------------------------- 清点
L("")
L("=== %s 清点 ===" % OUT_DIR)
out = []
for a in sorted(eal.list_assets(OUT_DIR, recursive=False, include_folder=False)):
    pkg = pkg_of(a)
    o = unreal.load_asset(pkg)
    cls = o.get_class().get_name() if o else "?"
    extra = ""
    if o is not None and cls == "AnimSequence":
        for prop in ("sequence_length", "number_of_frames"):
            try:
                extra += "  %s=%s" % (prop, o.get_editor_property(prop))
            except Exception:
                pass
    out.append(pkg)
    L("   %-34s %-14s%s" % (pkg.split("/")[-1], cls, extra))
L("共 %d 个" % len(out))

# ---------------------------------------------------------------- ⚠️ 最外层骨缩放修复不在这里做
# 重定向产物会给最外层骨 `darius_godking_mesh_LOD0_Skeleton` 写一条 **scale = 1** 的假轨道
# （骨架 rest pose 是 100）⇒ 角色被渲染成 1.85 厘米高，Persona 里看不见。
#
# 🔴 **修它必须换到下一个编辑器会话**：本脚本跑完 → 存盘 → **重启编辑器** → 跑 `ik_31`。
#    原因（2026-09-18 带对照组的实验）：刚刚由 `run_batch_retarget` 生成、还没落盘重载的
#    AnimSequence，其数据模型是**空的**（`get_bone_track_names()` 返回 **0** 条，
#    而正常动画是 **309** 条）。此时调用任何动画数据改写接口（`remove_bone_animation` 等）
#    都会拿这个空模型覆盖回去，**把整段动画清成静止姿态**。
#    对照实验：同样的操作作用在**已落盘重载过**的旧动画上完全安全（5 个姿态不变、scale 仍 100）。
#
# 所以本脚本只负责产出 + 存盘，缩放修复交给 ik_31。

# ---------------------------------------------------------------- 存盘
# ⚠️ run_batch_retarget 只把资产建在内存里，**不会写盘**（实测：返回 6 项，
#    但 Anims_TP 目录下 0 个 .uasset）。必须逐个显式 save。
L("")
L("=== 存盘 ===")
n_saved = 0
for pkg in out:
    try:
        if eal.save_asset(pkg):
            n_saved += 1
        else:
            LW("   save 返回 False: %s" % pkg.split("/")[-1])
    except Exception as ex:
        LW("   save 异常 %s : %s" % (pkg.split("/")[-1], str(ex)[:80]))
L("存盘 %d / %d" % (n_saved, len(out)))

import os
_disk = "E:/UE/Fight/Content/Character/Darius/Anims_TP"
n_disk = 0
if os.path.isdir(_disk):
    n_disk = len([f for f in os.listdir(_disk) if f.endswith(".uasset")])
L("磁盘 .uasset 数 = %d" % n_disk)
if n_disk < len(out):
    LW("!! 应落盘 %d 个，实际 %d 个 —— 有资产没写盘。" % (len(out), n_disk))
    raise SystemExit(1)
L("=== DONE ===")
