# -*- coding: utf-8 -*-
"""离线：从 UE 导出的逐帧骨位 JSON 里量「步态相位」，判断
   (1) 两个源是不是各自一个完整周期；
   (2) 合并后手臂摆动与腿是否还反相（对侧摆臂）。
"""
import json
import math
import os

D = r"E:/UE/Fight/Saved/Preview/AxwExport"


def load(tag):
    with open(os.path.join(D, "bones_%s.json" % tag), encoding="utf-8") as f:
        return json.load(f)["frames"]


def series(frames, bone, axis):
    return [fr[bone][axis] for fr in frames]


def harmonic(sig):
    """返回 (一阶谐波幅值, 相位(度), 一阶能量占比)。"""
    n = len(sig)
    if n < 4:
        return 0.0, 0.0, 0.0
    m = sum(sig) / n
    c = sum((sig[i] - m) * math.cos(2 * math.pi * i / n) for i in range(n))
    s = sum((sig[i] - m) * math.sin(2 * math.pi * i / n) for i in range(n))
    a1 = math.hypot(c, s) * 2.0 / n
    ph = math.degrees(math.atan2(s, c)) % 360.0
    tot = sum((v - m) ** 2 for v in sig) / n
    return a1, ph, (a1 * a1 / 2.0) / tot if tot > 1e-12 else 0.0


def stride(sig):
    return sig.index(max(sig)), sig.index(min(sig)), max(sig) - min(sig)


def phase_diff(p1, p2):
    d = (p1 - p2) % 360.0
    return d - 360.0 if d > 180.0 else d


merged = load("merged")
low = load("low")
up = load("up")
print("frames: merged=%d low=%d up=%d" % (len(merged), len(low), len(up)))

print("\n=== 1. 各自是不是「一个完整周期」（一阶谐波能量占比，越接近 1 越纯） ===")
print("   %-10s %-24s %8s %10s" % ("anim", "signal", "amp", "h1_ratio"))
SIGS = [("leg_diff", lambda fr: fr["foot_l"][1] - fr["foot_r"][1]),
        ("arm_diff", lambda fr: fr["hand_l"][1] - fr["hand_r"][1]),
        ("hip_z", lambda fr: fr["pelvis"][2]),
        ("pelvis_y", lambda fr: fr["pelvis"][1])]
for tag, frames in (("merged", merged), ("low", low), ("up", up)):
    for nm, fn in SIGS:
        sig = [fn(fr) for fr in frames]
        a1, ph, r = harmonic(sig)
        print("   %-10s %-24s %8.2f %10.3f" % (tag, nm, a1, r))

print("\n=== 2. 相位（度，0=序列起点） ===")
print("   %-10s %-24s %10s %10s" % ("anim", "signal", "phase", "peak_key"))
for tag, frames in (("merged", merged), ("low", low), ("up", up)):
    for nm, fn in SIGS:
        sig = [fn(fr) for fr in frames]
        a1, ph, r = harmonic(sig)
        pk, tr, rng = stride(sig)
        print("   %-10s %-24s %10.1f %10d" % (tag, nm, ph, pk))

print("\n=== 3. 合并后 腿 vs 臂 相位差（自然走路应≈180°，即对侧摆臂） ===")
for tag, frames in (("merged", merged), ("low", low), ("up", up)):
    leg = [fr["foot_l"][1] - fr["foot_r"][1] for fr in frames]
    arm = [fr["hand_l"][1] - fr["hand_r"][1] for fr in frames]
    _, pl, _ = harmonic(leg)
    _, pa, _ = harmonic(arm)
    print("   %-10s leg_phase=%6.1f  arm_phase=%6.1f  diff=%7.1f°" % (tag, pl, pa, phase_diff(pa, pl)))

print("\n=== 4. 合并 vs 各源：逐帧信号最大偏差（cm） ===")
for nm, fn in SIGS:
    m = [fn(fr) for fr in merged]
    l = [fn(fr) for fr in low]
    u = [fn(fr) for fr in up]
    # 合并 key i ↔ low key i（等长）；合并 key i ↔ up key round(i*40/50)
    dl = max(abs(m[i] - l[i]) for i in range(min(len(m), len(l)))) * 100
    du = max(abs(m[i] - u[min(len(u) - 1, round(i * (len(u) - 1) / (len(m) - 1)))])
             for i in range(len(m))) * 100
    print("   %-10s vs low = %7.2f   vs up = %7.2f" % (nm, dl, du))

print("\n=== 5. 循环接缝（首 key vs 末 key 的 component-space 距离，cm） ===")
for tag, frames in (("merged", merged), ("low", low), ("up", up)):
    a, b = frames[0], frames[-1]
    worst = []
    for k in a:
        d = math.dist(a[k], b[k]) * 100
        worst.append((d, k))
    worst.sort(reverse=True)
    print("   %-10s 最大 %7.2f cm (%s)   中位 %5.2f cm" % (
        tag, worst[0][0], worst[0][1], worst[len(worst) // 2][0]))

print("\n=== 6. 合并后 脚/趾 最低 z 与 髋高 逐 key ===")
zs = [(min(fr["foot_l"][2], fr["foot_r"][2], fr["ball_l"][2], fr["ball_r"][2],
           fr["toe_l"][2], fr["toe_r"][2]), i) for i, fr in enumerate(merged)]
print("   最低 = %.2f cm @ key %d ；最高 = %.2f cm @ key %d" % (
    min(zs)[0], min(zs)[1], max(zs)[0], max(zs)[1]))
hz = [fr["pelvis"][2] for fr in merged]
print("   pelvis z: %.2f ~ %.2f cm（起伏 %.2f cm）" % (min(hz), max(hz), max(hz) - min(hz)))
hz2 = [fr["pelvis"][2] for fr in low]
print("   LOW pelvis z: %.2f ~ %.2f cm（起伏 %.2f cm）" % (min(hz2), max(hz2), max(hz2) - min(hz2)))
