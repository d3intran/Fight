# -*- coding: utf-8 -*-
"""一行判据：编辑器世界有没有在 tick。

**为什么这件事必须单独有个脚本**
UE 编辑器里 `UWorld::Tick` 由「Realtime 视口绘制」驱动；窗口一旦被最小化/隐藏，
世界就**完全不 tick**。此时 `SkeletalMeshComponent` 的动画永不求值 ⇒
任何「按帧设姿势再截图」的脚本都会产出**一整套姿势相同的假帧**（md5 全同），
而 `SceneCapture2D.capture_scene()` 是显式渲染请求，照常出图 —— 极具误导性。

⇒ 跑任何按帧渲染的脚本**之前**先跑本脚本。不 tick 就先 `Scripts/editor_focus.py` 恢复窗口。
"""
import time
import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
t0 = unreal.SystemLibrary.get_game_time_in_seconds(world)
time.sleep(1.2)
t1 = unreal.SystemLibrary.get_game_time_in_seconds(world)
dt = t1 - t0
if dt > 1e-6:
    unreal.log("TICK_OK game_time %.4f -> %.4f (Δ=%.4f) —— 世界在 tick，按帧渲染可用"
               % (t0, t1, dt))
else:
    unreal.log_warning("TICK_FROZEN game_time %.4f 停滞 —— 世界没 tick，"
                       "按帧渲染会产出假帧；先跑 Scripts/editor_focus.py" % t0)
unreal.log("=== DONE ===")
