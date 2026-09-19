# -*- coding: utf-8 -*-
"""从 `Saved/exp_logs/*.log` 里把各轮 `ik_37` 的表格重新解析出来并汇总。

存在的理由：`ue_remote.py` 会给 UE 侧每一行日志加 `[Info] ` / `[Warning] ` 前缀，
第一次写的解析器没剥前缀，导致汇总全空 —— 数据其实都在日志里，不必重跑实验。
"""
import glob
import os
import re
import sys

ROOT = "E:/UE/Fight"
ROW = re.compile(r"^\s*(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)")
PREFIX = re.compile(r"^\[(?:Info|Warning|Error|Verbose|Display)\]\s?")
HDR = re.compile(r"^=+\s*(ik_\S+?\.py)\s+\(([\d.]+)s\)")
TAG = re.compile(r"^#+\s*([a-z0-9_]+)\s")
ORDER = ["大腿L", "小腿L", "大腿R", "小腿R", "大臂L", "小臂L", "大臂R", "小臂R",
         "锁骨L", "锁骨R", "躯干", "颈", "头",
         # twist 组（原判据看不见的那些）
         "膝面L", "膝面R", "肘面L", "肘面R", "颈面",
         "脚L", "脚R", "手L", "手R"]


def parse(path):
    """返回 {tag: {anim: {段: (均值, 最大)}}}。"""
    out, tag, script, anim = {}, None, None, None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            ln = PREFIX.sub("", raw.rstrip("\n"))
            m = HDR.match(ln)
            if m:
                script = m.group(1)
                continue
            if ln.startswith("############"):
                # 轮次 tag 行：`############ e3  LOCAL_ROTATION_AXES 全量（…）`
                #   → tag 后跟**空白**（两空格），故 `(?=\s|$)` 能把它和动画名行区分开
                # 动画名行：`################ idle1（65 帧，抽样 13 帧）`
                #   → 名字后**紧跟** `（`，不满足 `(?=\s|$)`
                # 二者靠这个前瞻区分，不能依赖 `script` 变量（它是**跨轮残留**的）
                mt = re.match(r"^#{4,}\s+([a-z][a-z0-9_]*)(?=\s|$)", ln)
                ma = re.match(r"^#{4,}\s+([A-Za-z0-9_]+)（", ln)
                if mt:
                    tag = mt.group(1)
                elif ma and script == "ik_37_verify_orientation.py":
                    anim = ma.group(1)
                    out.setdefault(tag, {}).setdefault(anim, {})
                continue
            if script == "ik_37_verify_orientation.py" and anim:
                r = ROW.match(ln)
                if r:
                    out.setdefault(tag, {}).setdefault(anim, {})[r.group(1)] = (
                        float(r.group(2)), float(r.group(3)))
    return out


def show(path):
    data = parse(path)
    print("日志：%s" % path)
    print("解析到 %d 轮实验：%s\n" % (len(data), list(data)))
    for anim in ("idle1", "run"):
        rows = [(t, d[anim]) for t, d in data.items() if anim in d]
        if not rows:
            continue
        print("================ %s（均值 / 最大）================" % anim)
        hdr = "%-8s" % "段"
        for t, _ in rows:
            hdr += "| %-15s" % t
        print(hdr)
        for seg in ORDER:
            line = "%-8s" % seg
            for t, d in rows:
                v = d.get(seg)
                line += "| %-15s" % ("%6.2f/%6.2f" % v if v else "   -/-   ")
            print(line)
        print("超门限段（均值>8 或 最大>35）：")
        for t, d in rows:
            bad = [s for s, (m, x) in d.items() if m > 8.0 or x > 35.0]
            print("   %-8s %2d 段  %s" % (t, len(bad), ", ".join(bad) if bad else "全过 ✅"))
        print()


if __name__ == "__main__":
    args = sys.argv[1:]
    paths = args or sorted(glob.glob(ROOT + "/Saved/exp_logs/*.log"))
    for p in paths:
        show(p)
