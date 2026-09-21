"""对照组：把目标 FBX 原样「导入 → 立刻导出」，检验导出/导入往返本身是否破坏蒙皮。

用法: blender -b -P Scripts/anim/atk_07_roundtrip.py -- <IN_FBX> <OUT_FBX> <use_bake:0|1>
"""
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
IN_FBX, OUT_FBX = argv[0], argv[1]
BAKE = (argv[2] == "1") if len(argv) > 2 else True

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=IN_FBX)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
print("导入 %s：骨数=%d 网格=%d 动作=%s" % (
    IN_FBX, len(arm.data.bones), len([o for o in bpy.data.objects if o.type == "MESH"]),
    arm.animation_data.action.name if (arm.animation_data and arm.animation_data.action) else None))
print("骨架 scale = %s  location = %s" % (tuple(arm.scale), tuple(arm.location)))
for b in list(arm.data.bones)[:3]:
    print("  骨 %s scale=%s" % (b.name, tuple(round(s, 4) for s in b.matrix_local.to_scale())))

bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
kw = dict(filepath=OUT_FBX, use_selection=False, add_leaf_bones=False,
          apply_unit_scale=True, global_scale=1.0)
if BAKE:
    kw.update(bake_anim=True, bake_anim_use_all_actions=False,
              bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True)
bpy.ops.export_scene.fbx(**kw)
print("已导出（bake=%s）: %s" % (BAKE, OUT_FBX))
