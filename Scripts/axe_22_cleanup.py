# -*- coding: utf-8 -*-
"""清理本次诊断遗留的临时 actor，恢复关卡基线"""
import unreal

def L(s=""):
    unreal.log(str(s))

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

killed = []
for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith(("BP_DariusCharacter", "FIX_", "SceneCapture2D_", "AXE_", "XYZ_", "ABTest_",
                     "StaticMeshActor_0", "StaticMeshActor_5", "StaticMeshActor_6",
                     "StaticMeshActor_7", "StaticMeshActor_8", "StaticMeshActor_9",
                     "CameraActor_", "AxeProxy", "AxeCap_")):
        killed.append(n)
        actor_sub.destroy_actor(a)
L("已清理: %s" % killed)
L("关卡最终 actor:")
for a in actor_sub.get_all_level_actors():
    L("   %-28s %s" % (a.get_name(), a.get_class().get_name()))

for k in les.get_viewport_config_keys():
    try:
        les.editor_set_game_view(False, k)
        les.editor_set_viewport_realtime(True, k)
        les.set_level_viewport_camera_info(unreal.Vector(-1000, -1000, 800), unreal.Rotator(pitch=-28.0, yaw=45.0, roll=0.0), k)
    except Exception:
        pass
les.editor_invalidate_viewports()
L("视口已复位")
L("=== DONE ===")
