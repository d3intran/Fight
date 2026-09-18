"""
A/B 并排对比渲染：源 LOL 动画 vs 重定向后动画，同一相机、同一帧、同一比例
用法: blender -b -P blender_60_ab_compare.py -- <SRC_GLB> <RT_FBX> <OUTDIR> <ANIM> [frames]
"""
import bpy, bmesh, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB, RT_FBX, OUTDIR, ANIM = argv[0], argv[1], argv[2], argv[3]
FRAMES = [int(x) for x in argv[4].split(",")] if len(argv) > 4 else [0, 7, 14, 21]
os.makedirs(OUTDIR, exist_ok=True)

def imp(p, kind):
    before = set(bpy.data.objects)
    if kind == "fbx":
        bpy.ops.import_scene.fbx(filepath=p, automatic_bone_orientation=True)
    else:
        bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    return ([o for o in new if o.type == 'ARMATURE'][0], [o for o in new if o.type == 'MESH'])

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
src, src_meshes = imp(SRC_GLB, "glb")
rt, rt_meshes = imp(RT_FBX, "fbx")

# 源：剔除狼灵/王座材质
for m in src_meshes:
    slots = [s.material.name.lower() if s.material else "" for s in m.material_slots]
    kill = [i for i, n in enumerate(slots) if any(k in n for k in ("wolf", "throne", "gem"))]
    if kill:
        bm = bmesh.new(); bm.from_mesh(m.data); bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in kill], context='FACES')
        bm.to_mesh(m.data); bm.free(); m.data.update()

# 统一材质
grey = bpy.data.materials.new("G"); grey.use_nodes = True
bs = grey.node_tree.nodes["Principled BSDF"]
bs.inputs["Base Color"].default_value = (0.62, 0.64, 0.68, 1)
bs.inputs["Roughness"].default_value = 0.7
grey_src = grey.copy(); grey_src.name = "GS"
bs2 = grey_src.node_tree.nodes["Principled BSDF"]
bs2.inputs["Base Color"].default_value = (0.75, 0.55, 0.45, 1)   # 源=暖色
for m in src_meshes:
    m.data.materials.clear(); m.data.materials.append(grey_src)
for m in rt_meshes:
    m.data.materials.clear(); m.data.materials.append(grey)

# ---- 把两套骨架摆到并排、等高 ----
def bbox_of(meshes):
    mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
    dg = bpy.context.evaluated_depsgraph_get()
    for o in meshes:
        if o.hide_viewport:
            continue
        ev = o.evaluated_get(dg)
        for v in ev.data.vertices:
            w = ev.matrix_world @ v.co
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    return mn, mx

sc.frame_set(0)
bpy.context.view_layer.update()
mnS, mxS = bbox_of(src_meshes)
mnT, mxT = bbox_of(rt_meshes)
hS = mxS.z - mnS.z
hT = mxT.z - mnT.z
print(f"源高度 {hS:.2f}  目标高度 {hT:.2f}")
k = hS / hT                     # 把目标放大到与源等高
gap = hS * 0.55
# 源：底面到 z=0，中心到 x=-gap
src.location = Vector((-gap - (mnS.x + mxS.x) / 2, -(mnS.y + mxS.y) / 2, -mnS.z))
rt.scale = (k, k, k)
rt.location = Vector((gap - (mnT.x + mxT.x) / 2 * k, -(mnT.y + mxT.y) / 2 * k, -mnT.z * k))
bpy.context.view_layer.update()

# 相机 / 光照
sc.render.engine = 'CYCLES'; sc.cycles.samples = 28; sc.cycles.use_denoising = False
sc.render.resolution_x = 1000; sc.render.resolution_y = 560
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.78, 0.80, 0.84, 1.0)
ld = bpy.data.lights.new("S", type='SUN'); ld.energy = 4.0
lo = bpy.data.objects.new("S", ld); sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(52), 0, math.radians(-35))
cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'
cd.ortho_scale = hS * 2.6
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
center = Vector((0, 0, hS * 0.5))
cam.location = center + Vector((-1.0, 0.0, 0.0)).normalized() * (hS * 4)
cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()

for f in FRAMES:
    sc.frame_set(f)
    sc.render.filepath = os.path.join(OUTDIR, f"AB_{ANIM}_f{f:03d}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", sc.render.filepath)
print("=== AB DONE ===")
