# -*- coding: utf-8 -*-
"""
清理诊断 / 验证期在 UE 里产生的临时资产与临时关卡 actor。
每次做完 UE 侧验证都要跑一遍，保证工程回到干净状态。

注意：本文件内容里刻意不出现 `.py` 字样路径，避免踩 ue_remote 的历史坑
（该坑已在 ue_remote.py 内修复，此处仅作双保险）。
"""
import unreal

eal = unreal.EditorAssetLibrary

for d in ("/Game/Temp", "/Game/Temp_SrcClean"):
    if eal.does_directory_exist(d):
        unreal.log("delete_directory %s -> %s" % (d, eal.delete_directory(d)))
    else:
        unreal.log("%s 不存在" % d)

left = eal.list_assets("/Game", recursive=False, include_folder=True)
unreal.log("剩余 /Game 顶层: %s" % [str(x) for x in left])

# 删除本管线/验证期生成的临时 actor（按已知前缀白名单，绝不动基线 actor）
TEMP_PREFIX = ("SIM_", "ABTest_", "XYZ_", "DBG_", "TMP_", "CAP_", "PROBE_")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in list(eas.get_all_level_actors()):
    lb = a.get_actor_label()
    if lb.startswith(TEMP_PREFIX):
        unreal.log("destroy temp actor: %s" % lb)
        eas.destroy_actor(a)

# 复核关卡 actor 是否回到基线
actors = eas.get_all_level_actors()
unreal.log("关卡 actor 数 = %d" % len(actors))
for a in actors:
    unreal.log("   %s  (%s)" % (a.get_actor_label(), a.get_class().get_name()))
unreal.log("=== DONE ===")
