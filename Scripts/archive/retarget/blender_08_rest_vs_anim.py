"""
Blender：渲染源动画的「静止姿态(rest)」与「动画姿态」对比，判断 DCC 绑定姿态差异
用法: blender -b -P blender_08_rest_vs_anim.py -- <GLB> <OUTDIR>
"""
import bpy, bmesh, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
act = arm.animation_data.action if (arm.animation_data and arm.animation_data.action) else None
print("action:", act.name if act else None)

# 剔除狼灵/王座
for m in meshes:
    slots = [s.material.name.lower() if s.material else "" for s in m.material_slots]
    kill = [i for i, n in enumerate(slots) if any(k in n for k in ("wolf", "throne", "gem"))]
    if not kill:
        continue
    bm = bmesh.new(); bm.from_mesh(m.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in kill], context='FACES')
    bm.to_mesh(m.data); bm.free(); m.data.update()

mat = bpy.data.materials.new("G"); mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.6, 0.62, 0.66, 1)
b.inputs["Roughness"].default_value = 0.7
for m in meshes:
    m.data.materials.clear(); m.data.materials.append(mat)

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = False
sc.render.resolution_x = 380; sc.render.resolution_y = 520
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.78, 0.83, 1.0)
ld = bpy.data.lights.new("S", type='SUN'); ld.energy = 4.0
lo = bpy.data.objects.new("S", ld); sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(50), 0, math.radians(-35))
cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'; cd.ortho_scale = 260.0
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
center = Vector((0, 0, 100))

def shoot(tag, dirv):
    d = Vector(dirv).normalized()
    cam.location = center + d * 500
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, f"restcheck_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", sc.render.filepath)

# 1) 静止姿态
if arm.animation_data:
    arm.animation_data.action = None
sc.frame_set(0)
bpy.context.view_layer.update()
shoot("rest_side", (-1, 0, 0))
shoot("rest_front", (0, -1, 0))

# 2) 动画姿态
if act:
    arm.animation_data.action = act
sc.frame_set(0)
bpy.context.view_layer.update()
shoot("anim_side", (-1, 0, 0))
shoot("anim_front", (0, -1, 0))
print("=== DONE ===")
