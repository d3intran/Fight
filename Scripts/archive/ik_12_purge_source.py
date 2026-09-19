# -*- coding: utf-8 -*-
"""清理源骨架导入目标目录，为「干净导入」让路。

为什么必须清空：
  UE 5.8 走 Interchange 导入 FBX。当**目标包名已存在**时，Interchange 会走
  重导入路径，只重建 SkeletalMesh，**静默跳过整个动画工厂**（不报错、不打日志）。
  实测对照（同一 FBX、同一 pipeline）：

      目标包名已存在   -> 产出 1 个资产 / 0 个动画   ← 故障
      同目录换新包名   -> 产出 48 个资产 / 46 个动画 ← 正常
      全新目录         -> 产出 48 个资产 / 46 个动画 ← 正常

  ⇒ 目录无关，包名才是变量。导入前必须保证目标目录为空。

本脚本只删「导入产物」目录，不碰 Retarget / Anims / Blueprints。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

LIST_DIRS = [
    "/Game/Character/Darius/LOL_Source",
    "/Game/Temp/ImportExp",
]


def nuke_dir(d):
    if not eal.does_directory_exist(d):
        L("  %-46s <不存在，跳过>" % d)
        return 0
    n = 0
    for a in sorted(eal.list_assets(d, recursive=True, include_folder=False)):
        pkg = str(a).split(".")[0]
        try:
            ok = eal.delete_asset(pkg)
        except Exception as ex:
            ok = "EXC:%s" % str(ex)[:70]
        L("    del %-58s -> %s" % (pkg.replace(d + "/", ""), ok))
        n += 1
    return n


total = 0
for d in LIST_DIRS:
    L("=== 清理 %s ===" % d)
    total += nuke_dir(d)

L("")
L("共处理 %d 个资产" % total)
L("")
L("=== 复查：目标目录剩余 ===")
clean = True
for d in LIST_DIRS:
    if not eal.does_directory_exist(d):
        L("  %-46s <目录已不存在>" % d)
        continue
    left = eal.list_assets(d, recursive=True, include_folder=False)
    L("  %-46s 剩余 %d 个" % (d, len(left)))
    for a in sorted(left)[:10]:
        LW("      %s" % str(a).split(".")[0])
    if left:
        clean = False

L("")
L("干净 = %s" % clean)
if not clean:
    LW("!! 目标目录未清空，此时导入必然静默丢动画。先解决占用再继续。")
L("=== DONE ===")
