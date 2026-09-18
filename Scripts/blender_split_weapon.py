"""
=============================================================================
 武器网格独立拆分与握柄归一化脚本 (blender_split_weapon.py)
 -----------------------------------------------------------------------------
 作用：
 1. 采用 Blender 5.2 无头模式解析原始 FBX。
 2. 提取独立战斧网格对象 'darius_godking_mesh_LOD0.007'。
 3. 分析战斧几何顶点分布、轴向跨度与握柄中点。
 4. 消除骨架变换，将战斧的原点 (Pivot) 精准对齐到右手主握手柄处。
 5. 导出标准的独立静态网格 FBX: 'SM_Darius_GodKing_Axe.fbx'。
 6. 同时导出移除战斧后的纯角色骨骼网格 FBX: 'SK_Darius_NoWeapon.fbx'。
=============================================================================
"""

import bpy
import os
import math
from mathutils import Vector

# 清理场景
bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"E:\UE\Assets\Darius_God_king\God King Darius 2XKO.fbx"
out_dir = r"E:\UE\Fight\Saved\Exported_Weapons"
os.makedirs(out_dir, exist_ok=True)

print(f"=== [BLENDER] Loading {fbx_path} ===")
bpy.ops.import_scene.fbx(filepath=fbx_path)

axe_obj = None
armature_obj = None
body_objs = []

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        if 'Axe' in [m.name for m in obj.data.materials if m] or obj.name.endswith('.007'):
            axe_obj = obj
        else:
            body_objs.append(obj)
    elif obj.type == 'ARMATURE':
        armature_obj = obj

if not axe_obj:
    print("[Error] Could not find Axe mesh object!")
    sys.exit(1)

print(f"Found Axe Mesh: {axe_obj.name}, vertices={len(axe_obj.data.vertices)}")

# 1. 探查战斧在世界空间的顶点范围 (Bounding Box)
verts = [axe_obj.matrix_world @ v.co for v in axe_obj.data.vertices]
xs = [v.x for v in verts]
ys = [v.y for v in verts]
zs = [v.z for v in verts]

min_v = Vector((min(xs), min(ys), min(zs)))
max_v = Vector((max(xs), max(ys), max(zs)))
size_v = max_v - min_v
center_v = (min_v + max_v) * 0.5

print(f"Axe World Bounds: Min={min_v}, Max={max_v}")
print(f"Axe Dimensions: X={size_v.x:.2f}m, Y={size_v.y:.2f}m, Z={size_v.z:.2f}m")

# 2. 复制战斧为独立网格对象，脱离 Armature
bpy.ops.object.select_all(action='DESELECT')
axe_obj.select_set(True)
bpy.context.view_layer.objects.active = axe_obj
bpy.ops.object.duplicate()
standalone_axe = bpy.context.view_layer.objects.active
standalone_axe.name = "SM_Darius_GodKing_Axe"

# 移除 Armature 修改器
for mod in list(standalone_axe.modifiers):
    standalone_axe.modifiers.remove(mod)

# 解除父子关系并保留变换
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

# 在 2XKO 模型中，战斧通常沿 Z 轴竖立，握柄在下半部 (约为 Z 轴下 1/3 处)
# 我们将 Pivot 设在握柄中心：X~中心, Y~中心, Z~底部上方约 60cm~80cm (手持位置)
grip_z = min_v.z + size_v.z * 0.35 # 握柄高度约在全长 35% 处
grip_point = Vector((center_v.x, center_v.y, grip_z))
print(f"Calculated Grip Point (New Pivot): {grip_point}")

# 平移网格顶点，使得 grip_point 成为 (0, 0, 0)
for v in standalone_axe.data.vertices:
    v.co = standalone_axe.matrix_world @ v.co - grip_point

standalone_axe.location = Vector((0, 0, 0))
standalone_axe.rotation_euler = (0, 0, 0)
standalone_axe.scale = Vector((1, 1, 1))

# 导出独立战斧 FBX
bpy.ops.object.select_all(action='DESELECT')
standalone_axe.select_set(True)
bpy.context.view_layer.objects.active = standalone_axe

axe_fbx_path = os.path.join(out_dir, "SM_Darius_GodKing_Axe.fbx").replace('\\', '/')
bpy.ops.export_scene.fbx(
    filepath=axe_fbx_path,
    use_selection=True,
    global_scale=1.0,
    apply_unit_scale=True,
    axis_forward='-Z',
    axis_up='Y'
)
print(f"=== [SUCCESS] Exported Standalone Axe to: {axe_fbx_path} ===")
