# -*- coding: utf-8 -*-
"""blender_50_finger_probe —— 只读探针：数一数 LOL 原始 GLB 里每根手指到底有几节骨（以及有没有掌骨）。

用途：判断「我们的手指不如 LoL 顺畅」是源资产本身只有 2 节，还是我们的净化白名单把第 3 节删掉了。
用法：blender -b -P <本文件> -- <GLB 路径>
"""
import sys
import bpy

argv = sys.argv
SRC = None
if "--" in argv:
    rest = argv[argv.index("--") + 1:]
    if rest:
        SRC = rest[0]
if not SRC:
    print("PROBE_ERR 需要 GLB 路径")
    raise SystemExit(1)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
if not arms:
    print("PROBE_ERR 没有骨架")
    raise SystemExit(1)
arm = arms[0]
bones = list(arm.data.bones)
print("PROBE total_bones = %d" % len(bones))

KEY = ("thumb", "index", "middle", "ring", "pinky", "finger")
fingers = [b for b in bones if any(k in b.name.lower() for k in KEY)]
print("PROBE finger_bones = %d" % len(fingers))
for b in sorted(fingers, key=lambda x: x.name.lower()):
    print("PROBE   %-28s parent=%-24s len=%.1f" % (b.name, (b.parent.name if b.parent else "-"), b.length * 100.0))

hands = [b for b in bones if "hand" in b.name.lower()]
print("PROBE hand_bones = %s" % [b.name for b in hands])
for h in hands:
    kids = [c.name for c in h.children]
    print("PROBE   %s children = %s" % (h.name, kids))

# 每根手指的节数统计
import re
stat = {}
for b in bones:
    m = re.match(r"^([LRl r]?)[_]?([A-Za-z]+?)(\d)$", b.name)
    if m and any(k in b.name.lower() for k in KEY):
        stat.setdefault(m.group(0).lower()[:2] + m.group(2).lower(), 0)
        stat[m.group(0).lower()[:2] + m.group(2).lower()] += 1
print("PROBE per_finger_counts = %s" % stat)
print("PROBE_DONE")
