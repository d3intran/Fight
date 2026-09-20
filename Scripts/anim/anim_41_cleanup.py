# -*- coding: utf-8 -*-
"""清理渲染遗留 actor，回到关卡基线（7 个）。
⚠️ spawn 出来的 actor 的 get_name() 是 `SkeletalMeshActor_0` 这类名字，
   而 set_actor_label() 设的是 label —— 清理时**两个都要匹配**。"""
import unreal

L = unreal.log
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

if les.is_in_play_in_editor():
    L("!! PIE 运行中")
    raise SystemExit(1)

PREFIX = ("AnimChk_", "SceneCapture2D_", "SkeletalMeshActor_", "SIM_", "AXE_",
          "AxeCap_", "CameraActor_", "TempAudit_", "DariusShowcase")
killed = []
for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    try:
        lb = a.get_actor_label()
    except Exception:
        lb = n
    if n.startswith(PREFIX) or lb.startswith(PREFIX):
        killed.append("%s / %s" % (n, lb))
        actor_sub.destroy_actor(a)
L("已销毁 %d 个：" % len(killed))
for k in killed:
    L("   %s" % k)
left = sorted([a.get_actor_label() for a in actor_sub.get_all_level_actors()])
L("")
L("剩余 %d 个：" % len(left))
for x in left:
    L("   %s" % x)
if len(left) != 7:
    L("!! 不是 7 个，请手工复核")
L("=== DONE ===")
