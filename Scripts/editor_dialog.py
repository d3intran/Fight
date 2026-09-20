# -*- coding: utf-8 -*-
"""列出/操作 UE 编辑器的顶层窗口，用来发现**模态对话框**。

## 为什么需要它
`ue_remote.py` 走的是 UE 的 Remote Execution（TCP），它由**游戏线程**处理。
只要弹出一个模态对话框（崩溃恢复提示、自动保存提示、资产重载确认…），
游戏线程就被阻塞，Remote Execution **完全无响应** ——
现象和「编辑器没起来」一模一样，但进程在、内存也在涨。

本脚本用 `ctypes` 枚举 UE 进程的顶层窗口（`EnumWindows` + `GetWindowThreadProcessId`），
把类名/标题/可见性/是否启用列出来，必要时**按 Enter / Esc 关掉对话框**。

用法：
    uv run --no-project python Scripts/editor_dialog.py            # 只列窗口
    uv run --no-project python Scripts/editor_dialog.py --enter    # 列完给前台窗口发 Enter
    uv run --no-project python Scripts/editor_dialog.py --esc
"""
import ctypes
import ctypes.wintypes as wt
import sys
import time

u32 = ctypes.windll.user32
psapi = ctypes.windll.psapi

SW_RESTORE = 9
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
WM_CLOSE = 0x0010
VK_RETURN, VK_ESCAPE = 0x0D, 0x1B

CB = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


def pids_of(name):
    """按进程名找 PID（不依赖 tasklist / psutil）。"""
    import subprocess
    out = subprocess.run(
        [r"C:\Windows\System32\tasklist.exe", "/FI", "IMAGENAME eq %s" % name, "/FO", "CSV", "/NH"],
        capture_output=True, text=True, errors="replace").stdout
    pids = []
    for ln in out.splitlines():
        parts = [p.strip('"') for p in ln.split('","')]
        if len(parts) >= 2 and parts[1].isdigit():
            pids.append(int(parts[1]))
    return pids


def title(h):
    n = u32.GetWindowTextLengthW(h)
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    u32.GetWindowTextW(h, buf, n + 1)
    return buf.value


def cls(h):
    buf = ctypes.create_unicode_buffer(256)
    u32.GetClassNameW(h, buf, 256)
    return buf.value


def main():
    pids = pids_of("UnrealEditor.exe")
    print("UnrealEditor PID = %s" % pids)
    if not pids:
        print("!! 编辑器没在跑")
        return
    found = []

    def cb(hwnd, _):
        pid = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids:
            found.append(hwnd)
        return True

    u32.EnumWindows(CB(cb), 0)
    print("顶层窗口 %d 个：" % len(found))
    for h in found:
        t, c = title(h), cls(h)
        vis = bool(u32.IsWindowVisible(h))
        en = bool(u32.IsWindowEnabled(h))
        print("   hwnd=%-10s vis=%-5s enabled=%-5s  cls=%-28s  title=%s"
              % (h, vis, en, c[:28], t[:70]))

    # 模态对话框的典型特征：可见 + 类名 #32770 (Windows 对话框)
    modals = [h for h in found if bool(u32.IsWindowVisible(h)) and cls(h) == "#32770"]
    print("\n模态对话框候选（class #32770）= %d 个" % len(modals))
    for h in modals:
        print("   -> %s" % title(h))

    # 🔴 真正的判据（2026-09-19 实测）：UE 的模态框是 **Slate**，类名是 `UnrealWindow`
    #    而不是 `#32770`，靠类名抓不到。改用「可见 + 标题非空 + 标题不以 Unreal Editor 开头」。
    #    典型：崩溃后的 `Restore Packages`。
    # ⚠️ 主窗口标题是 `Fight - Unreal Editor`（工程名在前），
    #    所以**不能**只用 `startswith("Unreal Editor")` 判断 —— 那会把主窗口误判成对话框，
    #    每轮都给主窗口发一次 Esc（实测真的发生了）。改用「包含 Unreal Editor 即为非对话框」。
    blocking = [h for h in found
                if bool(u32.IsWindowVisible(h)) and title(h)
                and "Unreal Editor" not in title(h)]
    print("\n阻挡型对话框 = %d 个 %s" % (len(blocking), [title(h) for h in blocking]))

    if "--auto" in sys.argv:
        if not blocking:
            print("没有阻挡型对话框，什么都不做")
            return
        h = blocking[0]
        print("\n[auto] 关闭 hwnd=%s (%s)" % (h, title(h)[:50]))
        # ⚠️ 2026-09-19 二次实测：keybd_event 的 Esc 对部分 Slate 模态框**无效**
        #    （SetForegroundWindow 被系统的前台锁定策略拒绝时，按键会落到别的窗口）。
        #    **PostMessage WM_CLOSE 有效**——「PostMessage 对 Slate 无效」只对键盘消息成立，
        #    WM_CLOSE 是窗口消息，Slate 窗口过程照收。先 WM_CLOSE，不行再退回真实 Esc。
        u32.PostMessageW(h, WM_CLOSE, 0, 0)
        time.sleep(2.0)
        if not (bool(u32.IsWindowVisible(h)) and title(h)):
            print("[auto] WM_CLOSE 已关闭")
            return
        print("[auto] WM_CLOSE 无效，退回真实 Esc…")
        u32.ShowWindow(h, SW_RESTORE)
        u32.SetForegroundWindow(h)
        u32.BringWindowToTop(h)
        KEYEVENTF_KEYUP = 0x0002
        u32.keybd_event(VK_ESCAPE, 0, 0, 0)
        u32.keybd_event(VK_ESCAPE, 0, KEYEVENTF_KEYUP, 0)
        print("[auto] 已发送 Esc")
        return

    if "--enter" in sys.argv or "--esc" in sys.argv:
        vk = VK_ESCAPE if "--esc" in sys.argv else VK_RETURN
        target = (blocking or modals or found or [None])[0]
        if target is None:
            print("没有可发按键的窗口")
            return
        print("\n向 hwnd=%s (%s) 发送 VK=0x%02X" % (target, title(target)[:50], vk))
        u32.ShowWindow(target, SW_RESTORE)
        u32.SetForegroundWindow(target)
        u32.BringWindowToTop(target)
        # ⚠️ UE 的对话框是 **Slate**，不走 HWND 的 WM_KEYDOWN —— 实测 PostMessage
        #    对它无效。必须用 `keybd_event` 合成**真实键盘输入**，
        #    由系统投递到前台窗口的消息队列，Slate 才收得到。
        KEYEVENTF_KEYUP = 0x0002
        u32.keybd_event(vk, 0, 0, 0)
        u32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        print("已发送真实按键")


if __name__ == "__main__":
    main()
