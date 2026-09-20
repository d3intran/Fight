"""
把连续帧 PNG 序列合成为 MP4（ffmpeg concat 列表，避免双数字文件名无法用 %0Nd 模式）。
用法: uv run python Scripts/anim/anim_78_make_videos.py
依赖: C:\\ffmpeg\\bin\\ffmpeg.exe
"""
import os, glob, subprocess, sys

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
BASE = r"E:\UE\Fight\Saved\Preview"
VIDEO = os.path.join(BASE, "video")
os.makedirs(VIDEO, exist_ok=True)

# (帧目录, 标签, 帧率)
JOBS = [
    (os.path.join(BASE, "walkfwd"), "walkfwd", 24),
    (os.path.join(BASE, "walkbwd"), "walkbwd", 24),
]

for d, label, fps in JOBS:
    pngs = sorted(glob.glob(os.path.join(d, f"{label}_*.png")))
    # 按各自视角的 fXXX 帧号排序（文件名已零填充，按名排序即正确顺序）
    for view in ("front34", "side"):
        grp = sorted([p for p in pngs if f"_{view}_" in os.path.basename(p)])
        if not grp:
            print("skip", label, view, "(no frames)")
            continue
        # 因为 i 索引与帧号单调对应，按文件名排序即可
        listpath = os.path.join(d, f"_list_{view}.txt")
        with open(listpath, "w") as f:
            for p in grp:
                f.write(f"file '{p.replace(chr(92), '/')}'\n")
        out = os.path.join(VIDEO, f"{label}_{view}.mp4")
        cmd = [
            FFMPEG, "-y", "-f", "concat", "-safe", "0", "-r", str(fps),
            "-i", listpath, "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-r", str(fps), out,
        ]
        print("RUN", " ".join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print("!!! ffmpeg failed", label, view)
            print(r.stderr[-1500:])
            sys.exit(1)
        print("OK ->", out, f"({len(grp)} frames)")
print("=== ALL VIDEOS DONE ===")
