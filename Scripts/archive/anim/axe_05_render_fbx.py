"""
把战斧 FBX 三视图渲染出来，确认到底有什么几何。
用法: blender -b -P axe_05_render_fbx.py -- <FBX> <OUTDIR> <TAG>
"""
import bpy, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, TAG = argv[0], argv[1], argv[2]
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, automatic_bone_orientation=True)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in meshes:
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
size = mx - mn
ctr = (mn + mx) * 0.5
print("bbox min", mn, "max", mx, "size", size)

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_denoising = False
sc.render.resolution_x = 900; sc.render.resolution_y = 900
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.66, 0.72, 1.0)
ld = bpy.data.lights.new("S", type='SUN'); ld.energy = 4.5
lo = bpy.data.objects.new("S", ld); sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(55), 0, math.radians(-35))

cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'
cd.ortho_scale = max(size) * 1.15
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam

views = [
    ("front", Vector((0, -1, 0))),
    ("side",  Vector((-1, 0, 0))),
    ("top",   Vector((0, 0, 1))),
    ("iso",   Vector((-1, -1, 0.5))),
]
for name, d in views:
    d = d.normalized()
    cam.location = ctr + d * (max(size) * 4)
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, "%s_%s.png" % (TAG, name))
    bpy.ops.render.render(write_still=True)
    print("rendered", sc.render.filepath)
print("=== DONE ===")
