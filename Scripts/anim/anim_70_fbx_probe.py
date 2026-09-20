# -*- coding: utf-8 -*-
"""FBX 动作探针：看清新拿到的动画是什么骨架、几个动作、**有没有根位移**。

## 判读要点
- 骨名前缀（mixamorig: / Mannequin 风格 / 自定义）决定能不能直接用
  `apply_auto_generated_retarget_definition()` 建链（只对 Mannequin 命名有效）。
- **根位移**：Mixamo 导出常带 forward 位移。带位移的动画喂给
  `CharacterMovement` 驱动的角色会「滑步」或原地踏步 —— 必须先判断是否 in-place。
  判据：髋骨的 Y 分量在首末帧是否变化（UE 里 forward = ±Y）。

用法：
    blender -b -P <本脚本> -- <FBX路径>
"""
import bpy
import sys

argv = sys.argv
if "--" not in argv:
    print("!! 需要 -- <FBX路径>")
    sys.exit(1)
path = argv[argv.index("--") + 1]

bpy.ops.wm.read_factory_settings(use_empty=True)
print("=== [FBX] %s ===" % path)
bpy.ops.import_scene.fbx(filepath=path)

print("\n--- 场景对象 ---")
for o in bpy.data.objects:
    print("  %-30s type=%-12s" % (o.name, o.type))

arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
print("\n--- 骨架 %d 个 ---" % len(arms))
for arm in arms:
    bones = list(arm.data.bones)
    print("  armature=%s   bones=%d" % (arm.name, len(bones)))
    names = [b.name for b in bones]
    print("  前 12 根骨: %s" % names[:12])
    if names:
        pref = set(n.split(":")[0] for n in names if ":" in n)
        print("  命名空间前缀: %s" % (sorted(pref) if pref else "无（无 mixamorig: 之类前缀）"))
    # 髋骨候选
    cand = [n for n in names if any(k in n.lower() for k in ("hips", "pelvis", "root"))]
    print("  髋/根候选骨: %s" % cand[:8])

print("\n--- 动作 ---")
print("  actions=%d" % len(bpy.data.actions))
for a in bpy.data.actions:
    fr = a.frame_range
    print("  %-40s frames=%d..%d (%d 帧) fps=%s"
          % (a.name, int(fr[0]), int(fr[1]), int(fr[1] - fr[0]) + 1,
             bpy.context.scene.render.fps))

# 根位移判定：取第一根髋/根候选骨，比首末帧的 location
if arms and bpy.data.actions:
    arm = arms[0]
    act = bpy.data.actions[0]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    cand = [b.name for b in arm.data.bones
            if any(k in b.name.lower() for k in ("hips", "pelvis", "root"))]
    target = cand[0] if cand else arm.data.bones[0].name
    pb = arm.pose.bones.get(target)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    vals = {}
    for f in (f0, (f0 + f1) // 2, f1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        vals[f] = tuple(round(v, 2) for v in pb.location)
    print("\n--- 根位移判定（骨 %s 的 location）---" % target)
    for f in sorted(vals):
        print("  frame %-4d %s" % (f, vals[f]))
    d = [abs(vals[f1][i] - vals[f0][i]) for i in range(3)]
    print("  首末帧位移分量: %s" % [round(x, 2) for x in d])
    print("  判定: %s" % ("带位移（非 in-place）" if max(d) > 1.0 else "in-place（原地）"))
print("\n=== DONE ===")
