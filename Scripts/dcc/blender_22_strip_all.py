"""
彻底剔除 2XKO 骨骼网格体上的「插地待机斧」：
  1) 描边壳 darius_godking_mesh_LOD0 中复制的斧头多边形（KDTree 匹配）
  2) 斧头本体网格对象 darius_godking_mesh_LOD0.007（整对象删除）
并渲染清理前后的脚部特写做验证
用法: blender -b -P blender_22_strip_all.py -- <IN_FBX> <OUT_FBX> <OUTDIR> [threshold]
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
axe_obj = outline_obj = None
for name, o in meshes.items():
    mats = " ".join([s.material.name if s.material else "" for s in o.material_slots])
    if "axe" in mats.lower():
        axe_obj = o
    if "Outline" in mats:
        outline_obj = o
print("outline:", outline_obj.name, "| axe:", axe_obj.name)

# ---------- 1) 描边壳剔除斧头 ----------
axe_pts = [axe_obj.matrix_world @ v.co for v in axe_obj.data.vertices]
kd = kdtree.KDTree(len(axe_pts))
for i, p in enumerate(axe_pts):
    kd.insert(p, i)
kd.balance()

bm = bmesh.new(); bm.from_mesh(outline_obj.data)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
mw = outline_obj.matrix_world
mark = set()
for i, v in enumerate(bm.verts):
    co, idx, d = kd.find(mw @ v.co)
    if d < THRESH:
        mark.add(i)
dead = [f for f in bm.faces if sum(1 for v in f.verts if v.index in mark) >= len(f.verts) * 0.6]
print(f"描边壳：命中顶点 {len(mark)}，删除面 {len(dead)} / {len(bm.faces)}")
bmesh.ops.delete(bm, geom=dead, context='FACES')
bm.to_mesh(outline_obj.data); bm.free(); outline_obj.data.update()
print("描边壳清理后：顶点", len(outline_obj.data.vertices), "面", len(outline_obj.data.polygons))

# ---------- 2) 删除斧头本体网格对象 ----------
axe_name = axe_obj.name
axe_mats = [s.material.name if s.material else None for s in axe_obj.material_slots]
bpy.data.objects.remove(axe_obj, do_unlink=True)
del meshes[axe_name]
print(f"已删除斧头网格对象 {axe_name}（材质 {axe_mats}）")

# ---------- 统计 ----------
for o in meshes.values():
    n_below = sum(1 for v in o.data.vertices if (o.matrix_world @ v.co).z < -0.02)
    if n_below:
        print(f"  !! {o.name} 仍有地面以下顶点 {n_below}")
print("全部网格地面以下顶点数:", sum(1 for o in meshes.values() for v in o.data.vertices if (o.matrix_world @ v.co).z < -0.02))

# ---------- 3) 渲染脚部特写 ----------
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = False
sc.render.resolution_x = 480; sc.render.resolution_y = 420
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.72, 0.75, 0.80, 1.0)
ld = bpy.data.lights.new("S", type='SUN'); ld.energy = 4.0
lo = bpy.data.objects.new("S", ld); sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(52), 0, math.radians(-30))
cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'; cd.ortho_scale = 1.6
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
target = Vector((0.0, 0.0, 0.35))
for tag, dirv in [("feet34", (-1.0, -1.0, 0.35)), ("feetside", (-1.0, 0.0, 0.25))]:
    d = Vector(dirv).normalized()
    cam.location = target + d * 5.0
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUTDIR, f"CLEAN_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", sc.render.filepath)

# ---------- 4) 导出 ----------
bpy.ops.object.select_all(action='DESELECT')
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
arm.select_set(True); bpy.context.view_layer.objects.active = arm
for o in meshes.values():
    o.select_set(True)
bpy.ops.export_scene.fbx(
    filepath=OUT_FBX, use_selection=True, add_leaf_bones=False,
    primary_bone_axis='Y', secondary_bone_axis='X', apply_unit_scale=True,
    global_scale=1.0, mesh_smooth_type='FACE', armature_nodetype='NULL', bake_anim=False)
print("导出:", OUT_FBX)
print("=== DONE ===")
