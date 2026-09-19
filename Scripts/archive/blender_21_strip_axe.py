"""
从 2XKO 骨骼网格体中精确剔除「插地待机斧」几何
  - 目标：描边壳 darius_godking_mesh_LOD0（材质 Darius_Godking_Outline_MI）里复制的斧头多边形
  - 方法：以斧头本体 LOD0.007 的顶点建 KDTree，把描边壳中距离 < 阈值的顶点判为斧头
  - 同时导出干净 FBX，并渲染前后对比
用法: blender -b -P blender_21_strip_axe.py -- <IN_FBX> <OUT_FBX> <OUTDIR> [threshold]
"""
import bpy, bmesh, sys, os, math
from mathutils import Vector, kdtree

argv = sys.argv[sys.argv.index("--") + 1:]
IN_FBX, OUT_FBX, OUTDIR = argv[0], argv[1], argv[2]
THRESH = float(argv[3]) if len(argv) > 3 else 0.05
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=IN_FBX, automatic_bone_orientation=True)

meshes = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
print("mesh objects:", list(meshes.keys()))

AXE_KEY = "Axe"
outline_obj = None
axe_obj = None
for name, o in meshes.items():
    mats = " ".join([s.material.name if s.material else "" for s in o.material_slots])
    if AXE_KEY.lower() in mats.lower():
        axe_obj = o
    if "Outline" in mats:
        outline_obj = o
print("outline mesh:", outline_obj.name if outline_obj else None)
print("axe mesh:", axe_obj.name if axe_obj else None)

# --- 建斧头顶点 KDTree（世界空间）---
axe_pts = [axe_obj.matrix_world @ v.co for v in axe_obj.data.vertices]
kd = kdtree.KDTree(len(axe_pts))
for i, p in enumerate(axe_pts):
    kd.insert(p, i)
kd.balance()
print(f"axe KDTree: {len(axe_pts)} points, bbox z = {min(p.z for p in axe_pts):.2f} ~ {max(p.z for p in axe_pts):.2f}")

# --- 统计描边壳顶点的最近距离分布 ---
dists = []
for v in outline_obj.data.vertices:
    w = outline_obj.matrix_world @ v.co
    co, idx, d = kd.find(w)
    dists.append(d)
dists.sort()
n = len(dists)
print("描边壳 -> 斧头 最近距离分位：")
for q in (0.0, 0.01, 0.05, 0.1, 0.2, 0.5, 0.9, 1.0):
    print(f"   p{int(q*100):3d} = {dists[min(n-1, int(q*(n-1)))]:.4f} m")
n_close = sum(1 for d in dists if d < THRESH)
print(f"阈值 {THRESH} m 下判为斧头的描边壳顶点数: {n_close} / {n}")

# --- 删除 ---
bm = bmesh.new()
bm.from_mesh(outline_obj.data)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
mw = outline_obj.matrix_world
mark = set()
for i, v in enumerate(bm.verts):
    w = mw @ v.co
    co, idx, d = kd.find(w)
    if d < THRESH:
        mark.add(i)
print("命中顶点数:", len(mark))

dead_faces = []
for f in bm.faces:
    cnt = sum(1 for v in f.verts if v.index in mark)
    if cnt >= len(f.verts) * 0.6:
        dead_faces.append(f)
print("待删除面数:", len(dead_faces), "/", len(bm.faces))
bmesh.ops.delete(bm, geom=dead_faces, context='FACES')
bm.to_mesh(outline_obj.data)
bm.free()
outline_obj.data.update()
print("清理后描边壳顶点数:", len(outline_obj.data.vertices), "面数:", len(outline_obj.data.polygons))

# 复查地面以下顶点
n_below = sum(1 for v in outline_obj.data.vertices if (outline_obj.matrix_world @ v.co).z < -0.02)
print("清理后描边壳 地面以下顶点数:", n_below)

# --- 导出 ---
bpy.ops.object.select_all(action='DESELECT')
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
for o in meshes.values():
    o.select_set(True)
bpy.ops.export_scene.fbx(
    filepath=OUT_FBX, use_selection=True,
    add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X',
    apply_unit_scale=True, global_scale=1.0, mesh_smooth_type='FACE',
    armature_nodetype='NULL', bake_anim=False,
)
print("导出完成:", OUT_FBX)
print("=== DONE ===")
