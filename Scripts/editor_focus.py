# -*- coding: utf-8 -*-
"""把 UE 编辑器主窗口恢复并前置。

## 为什么需要它
UE 编辑器里 **世界 tick 是由「Realtime 视口」的绘制驱动的**：
窗口一旦被最小化/隐藏，没有视口绘制 ⇒ `UWorld::Tick` 不被调用 ⇒
`get_game_time_in_seconds()` 停滞 ⇒ **动画（SkeletalMeshComponent 的姿势）永不求值**。

症状极具误导性：`SceneCapture2D.capture_scene()` 是**显式渲染请求**，照常出图，
于是你会得到一堆「看起来正常、但姿势全部相同」的假帧（md5 全同）。
`t.IdleWhenNotForeground 0` 之类 CVar **治不了这个**（那不是节流问题，是根本没 tick）。

⇒ 任何「按帧渲染动画」的脚本，跑之前先确认编辑器窗口没被最小化。

用法：`uv run --no-project python Scripts/editor_focus.py`
"""
import ctypes
import ctypes.wintypes as wt
import sys
import time

u32 = ctypes.windll.user32
SW_RESTORE = 9
SW_SHOW = 5

TITLE_KEY = "Unreal Editor"


def windows_of(pid):
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        p = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid:
            n = u32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 2)
            u32.GetWindowTextW(hwnd, buf, n + 2)
            out.append((hwnd, buf.value, bool(u32.IsIconic(hwnd)), bool(u32.IsWindowVisible(hwnd))))
        return True

    u32.EnumWindows(cb, 0)
    return out


def main():
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if pid is None:
        # 自动找 UnrealEditor.exe
        import subprocess
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq UnrealEditor.exe", "/FO", "CSV", "/NH"],
                           capture_output=True, text=True)
        pids = []
        for line in r.stdout.splitlines():
            parts = [x.strip('"') for x in line.split('","')]
            if parts and parts[0].lower() == "unrealeditor.exe":
                pids.append(int(parts[1]))
        if not pids:
            print("未发现 UnrealEditor.exe 进程")
            return 1
        pid = pids[0]
    print("目标 PID = %d" % pid)

    wins = windows_of(pid)
    print("窗口数 = %d" % len(wins))
    for h, t, icon, vis in wins:
        print("  hwnd=%-10s iconic=%-5s visible=%-5s title=%r" % (h, icon, vis, t))

    main_w = None
    for h, t, icon, vis in wins:
        if TITLE_KEY.lower() in t.lower():
            main_w = h
            break
    if main_w is None and wins:
        main_w = max(wins, key=lambda x: len(x[1]))[0]
    if main_w is None:
        print("找不到主窗口")
        return 1

    print("恢复 hwnd=%s ..." % main_w)
    u32.ShowWindow(main_w, SW_RESTORE)
    time.sleep(0.4)
    u32.ShowWindow(main_w, SW_SHOW)
    time.sleep(0.4)
    u32.SetForegroundWindow(main_w)
    u32.BringWindowToTop(main_w)
    time.sleep(0.6)
    for h, t, icon, vis in windows_of(pid):
        if h == main_w:
            print("恢复后：iconic=%s visible=%s title=%r" % (icon, vis, t))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
