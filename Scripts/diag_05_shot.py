import unreal, time

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()

# 关闭节流
for cmd in ["t.IdleWhenNotForeground 0", "r.Editor.Viewport.Throttle 0", "Editor.bThrottleWhenHidden 0"]:
    unreal.SystemLibrary.execute_console_command(gw, cmd)

# 清掉可能残留的调试相机
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor):
    a.destroy_actor()
time.sleep(0.2)

dest = r"E:/UE/Fight/Saved/Shots/diag_pie_view.png"
import os
os.makedirs(r"E:/UE/Fight/Saved/Shots", exist_ok=True)

unreal.SystemLibrary.execute_console_command(gw, f'HighResShot 1600x900 filename="{dest}"')
print("shot ->", dest)
print("viewmode:", unreal.SystemLibrary.get_console_variable_string_value("r.ViewMode"))
