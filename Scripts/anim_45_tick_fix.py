# -*- coding: utf-8 -*-
"""诊断并尝试修复「编辑器世界不 tick」。

## 背景
UE 编辑器里 `UWorld::Tick` 由 Realtime 视口的绘制驱动。实测：编辑器启动后
`game_time` 只前进了 ~193 s 就**完全停滞**（此后 1.2 s 内 Δ=0）——
典型的「窗口失去前台 ⇒ 应用进入 idle ⇒ 不 tick」。

不 tick 的后果：`SkeletalMeshComponent` 的动画**永不求值**，任何「按帧设姿势再截图」
都会产出一整套姿势相同的**假帧**（而 SceneCapture 是显式渲染请求，照常出图）。

## 本脚本做三件事
A. 把节流相关 CVar **读回来**（`execute_console_command` 对不存在的 CVar 不报错，
   所以「设了」≠「生效」——必须读回值）
B. 拉长到 5 s 采样，区分「完全不 tick」与「被节流到极低频」
C. 试 PIE（Simulate）：PIE 世界由编辑器主循环直接 tick，**不依赖视口 realtime**，
   是「不 tick」问题的一条独立逃生路线
"""
import time
import unreal

L = unreal.log
LW = unreal.log_warning

CVARS = [
    "t.IdleWhenNotForeground",
    "t.MaxFPS",
    "r.Editor.Viewport.Throttle",
    "Editor.bThrottleWhenHidden",
    "Slate.bAllowThrottling",
    "Slate.ThrottleWhenMouseIsMoving",
    "Slate.EnableGlobalInvalidation",
]

# ---------------------------------------------------------------- A. CVar 读回
L("################ A. CVar 是否存在 / 当前值")
for name in CVARS:
    vals = []
    for fn_name in ("get_console_variable_int", "get_console_variable_float",
                    "get_console_variable_string"):
        fn = getattr(unreal.SystemLibrary, fn_name, None)
        if fn is None:
            continue
        try:
            vals.append("%s=%s" % (fn_name.replace("get_console_variable_", ""), fn(name)))
        except Exception as ex:
            vals.append("%s ERR" % fn_name.replace("get_console_variable_", ""))
    try:
        ret = unreal.SystemLibrary.execute_console_command(None, name)
    except Exception as ex:
        ret = "EXC:%s" % str(ex)[:60]
    L("   %-36s %s   | 执行返回=%r" % (name, "  ".join(vals) or "<无读接口>", str(ret)[:120]))

# ---------------------------------------------------------------- B. 长窗口 tick 采样
L("")
L("################ B. 5 s 内 tick 采样（每 0.5 s 一次）")
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
samples = []
for i in range(10):
    samples.append(unreal.SystemLibrary.get_game_time_in_seconds(world))
    time.sleep(0.5)
uniq = len(set(round(x, 6) for x in samples))
L("   编辑器世界 game_time: %s" % ["%.4f" % x for x in samples])
L("   ⇒ 不同取值 %d 个 / 10 次采样" % uniq)
if uniq == 1:
    LW("   完全停滞：编辑器世界**根本没在 tick**")
elif uniq < 5:
    LW("   极低频：被节流（每 5 s 只有 %d 次 tick）" % uniq)
else:
    L("   正常 tick")

# ---------------------------------------------------------------- C. PIE 逃生路线
L("")
L("################ C. PIE（Simulate）世界是否 tick")
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

play_fn = None
for nm in ("editor_play_simulate", "editor_play_in_viewport", "editor_request_begin_play"):
    f = getattr(les, nm, None)
    if f is not None:
        play_fn = (nm, f)
        break
L("   进入 PIE 的接口: %s" % (play_fn[0] if play_fn else "<没有>"))

if play_fn is None:
    LW("   本 UE 版本没暴露进入 PIE 的 Python 接口，PIE 路线不可用")
else:
    try:
        L("   %s() -> %s" % (play_fn[0], play_fn[1]()))
    except Exception as ex:
        LW("   %s() 失败: %s" % (play_fn[0], str(ex)[:120]))
    time.sleep(6.0)
    gw = None
    try:
        gw = ues.get_game_world()
    except Exception as ex:
        LW("   get_game_world: %s" % str(ex)[:90])
    L("   game_world = %s" % gw)
    if gw is not None:
        s = []
        for i in range(6):
            s.append(unreal.SystemLibrary.get_game_time_in_seconds(gw))
            time.sleep(0.5)
        L("   PIE 世界 game_time: %s" % ["%.4f" % x for x in s])
        L("   ⇒ 不同取值 %d / 6  %s"
          % (len(set(round(x, 6) for x in s)),
             "PIE 在 tick —— 渲染动画应改走 PIE 路线" if len(set(round(x, 6) for x in s)) > 1
             else "PIE 也没 tick"))
    end_fn = getattr(les, "editor_request_end_play", None)
    if end_fn is not None:
        try:
            L("   结束 PIE -> %s" % end_fn())
        except Exception as ex:
            LW("   结束 PIE 失败: %s" % str(ex)[:120])
        time.sleep(2.0)
L("=== DONE ===")
