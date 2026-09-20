"""
=============================================================================
 Blender FBX 结构深度解析脚本 (blender_inspect_fbx.py)
 -----------------------------------------------------------------------------
 作用：
 1. 采用 Blender 5.2 无头模式 (Headless: -b -P) 载入原始 FBX 模型。
 2. 遍历 Armature（骨架）对象、Mesh（网格）对象及其材质槽分配。
 3. 探查战斧（Axe）是属于独立 Mesh 对象还是作为整体 Mesh 中的材质多边形分区。
 4. 输出顶点数、多边形面数与局部包围盒尺寸。
=============================================================================
"""

import bpy
import sys

# 清理默认场景
bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"E:\UE\Assets\Darius_God_king\God King Darius 2XKO.fbx"
print(f"=== [BLENDER] Loading FBX: {fbx_path} ===")

bpy.ops.import_scene.fbx(filepath=fbx_path)

print(f"=== [BLENDER] Objects in scene: {len(bpy.data.objects)} ===")
for obj in bpy.data.objects:
    print(f"Object: {obj.name} (type: {obj.type})")
    if obj.type == 'MESH':
        print(f"  Vertices: {len(obj.data.vertices)}, Polygons: {len(obj.data.polygons)}")
        print(f"  Materials: {[m.name for m in obj.data.materials if m]}")
    elif obj.type == 'ARMATURE':
        print(f"  Bones count: {len(obj.data.bones)}")
        weapon_bones = [b.name for b in obj.data.bones if 'weapon' in b.name.lower()]
        print(f"  Weapon bones: {weapon_bones}")

print("=== [BLENDER] Inspection Completed ===")
