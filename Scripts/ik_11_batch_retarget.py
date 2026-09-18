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

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

SRC_DIR = "/Game/Character/Darius/LOL_Source"
OUT_DIR = "/Game/Character/Darius/Anims_TP"
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
L("=== DONE ===")
