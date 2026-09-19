# -*- coding: utf-8 -*-
"""关掉编辑器的「非前台/隐藏」节流，并把所有视口设为 Realtime —— 目标是**让世界 tick**。

## 为什么必须做（2026-09-19 血泪）
UE 编辑器里 `UWorld::Tick` 是由 **Realtime 视口的绘制**驱动的。
窗口被遮挡/最小化/非前台时，UE 会节流甚至完全停掉视口绘制 ⇒ **世界不 tick** ⇒
`SkeletalMeshComponent` 的动画**永不求值**。

症状极具误导性：`SceneCapture2D.capture_scene()` 是**显式渲染请求**，照常出图，
于是「按帧设姿势再截图」会产出一整套**姿势完全相同**的假帧（md5 全同）。
看起来像「采集冻结」，实际是**动画根本没在动**。

判据（本脚本自动跑）：`get_game_time_in_seconds()` 在 1.2 s 内是否前进。
不前进就别指望任何按帧渲染。

用法：`uv run --no-project python Scripts/ue_remote.py Scripts/disable_throttling.py`
"""
import time
import unreal

L = unreal.log
LW = unreal.log_warning

CVARS = [
    "t.IdleWhenNotForeground 0",     # 非前台不空转
    "t.MaxFPS 0",                    # 不限帧
    "r.Editor.Viewport.Throttle 0",  # 编辑器视口节流
    "Editor.bThrottleWhenHidden 0",
    "Slate.bAllowThrottling 0",      # Slate 层总节流开关
    "Slate.ThrottleWhenMouseIsMoving 0",
]

L("################ 1. 设置 CVar")
for cmd in CVARS:
    try:
        unreal.SystemLibrary.execute_console_command(None, cmd)
        L("   %s" % cmd)
    except Exception as ex:
        LW("   %s 失败: %s" % (cmd, str(ex)[:80]))

L("")
L("################ 2. 视口 Realtime")
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
try:
    keys = list(les.get_viewport_config_keys())
except Exception as ex:
    keys = []
    LW("   get_viewport_config_keys 失败: %s" % str(ex)[:90])
L("   视口配置键 %d 个: %s" % (len(keys), keys))
for k in keys:
    try:
        before = les.is_viewport_realtime(k)
    except Exception:
        before = "?"
    try:
        les.editor_set_viewport_realtime(True, k)
        after = les.is_viewport_realtime(k)
    except Exception as ex:
        after = "ERR:%s" % str(ex)[:50]
    L("   %-40s realtime %s -> %s" % (k, before, after))
try:
    les.editor_invalidate_viewports()
    L("   invalidate_viewports OK")
except Exception as ex:
    LW("   invalidate 失败: %s" % str(ex)[:80])

L("")
L("################ 3. 判据：世界是否 tick")
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
t0 = unreal.SystemLibrary.get_game_time_in_seconds(world)
time.sleep(1.2)
t1 = unreal.SystemLibrary.get_game_time_in_seconds(world)
dt = t1 - t0
if dt > 1e-6:
    L("   TICK_OK game_time %.4f -> %.4f (Δ=%.4f) —— 世界在 tick，按帧渲染可用" % (t0, t1, dt))
else:
    LW("   TICK_FROZEN game_time %.4f 停滞 —— 世界没 tick" % t0)
    LW("   ⇒ 按帧渲染会产出假帧。下一步：把编辑器窗口调到前台（不要被遮挡），"
       "或改用 PIE 渲染路线。")
L("=== DONE ===")
