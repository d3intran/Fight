# -*- coding: utf-8 -*-
"""独立清空重定向输出目录 Anims_TP。

⚠️ 为什么必须独立成一个脚本、而不是塞进批量重定向脚本里：
  2026-09-18 实测，在**编辑器已经加载过这 6 个资产**（例如它们在资产编辑器标签页里
  开着、或刚被脚本读过）之后再 `delete_asset()`，UE 会在**第一个删除**上
  EXCEPTION_ACCESS_VIOLATION（调用栈穿 python311.dll），编辑器整个崩掉。
  在编辑器刚启动、这些资产尚未被加载时删除，则正常。

  所以流程固定为：**先跑本脚本，再跑批量重定向**。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

DIRS = ["/Game/Character/Darius/Anims_TP"]

total = 0
for d in DIRS:
    L("=== 清理 %s ===" % d)
    if not eal.does_directory_exist(d):
        L("   <目录不存在>")
        continue
    items = sorted(eal.list_assets(d, recursive=False, include_folder=False))
    L("   待删 %d 个" % len(items))
    for a in items:
        pkg = str(a).split(".")[0]
        name = pkg.split("/")[-1]
        try:
            # 先确保没有被资产编辑器打开（打开状态下删除会崩）
            try:
                unreal.AssetToolsHelpers.get_asset_tools().close_editor_for_assets([unreal.load_asset(pkg)])
            except Exception:
                pass
            r = eal.delete_asset(pkg)
            L("   del %-40s -> %s" % (name, r))
            total += 1
        except Exception as ex:
            LW("   del %-40s 异常: %s" % (name, str(ex)[:90]))

L("")
L("共删除 %d 个" % total)
L("")
L("=== 复查 ===")
clean = True
for d in DIRS:
    if not eal.does_directory_exist(d):
        L("   %-40s <目录不存在>" % d)
        continue
    left = eal.list_assets(d, recursive=False, include_folder=False)
    L("   %-40s 剩余 %d 个" % (d, len(left)))
    for a in list(left)[:8]:
        LW("       %s" % str(a).split(".")[0])
    if left:
        clean = False
L("干净 = %s" % clean)
if not clean:
    LW("!! 没清干净，此时跑批量重定向会崩编辑器。")
    raise SystemExit(1)
L("=== DONE ===")
