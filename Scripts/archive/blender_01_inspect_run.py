"""
Blender 无头：检查 LOL 神王 Run 动画（骨骼 / 姿态 / 渲染预览）
用法: blender -b -P blender_01_inspect_run.py -- <GLB> <OUTDIR>
"""
import bpy
import sys
import os
import math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB = argv[0] if argv else r"E:\UE\Assets\Darius_GodKing_LOL_Original\Animations_GLB\standalone\darius_skin15_run.glb"
OUT = argv[1] if len(argv) > 1 else r"E:\UE\Fight\Saved\BlenderShots"
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
print("=== IMPORT ===", GLB)
bpy.ops.import_scene.gltf(filepath=GLB)

arm = None
meshes = []
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        arm = o
    elif o.type == 'MESH':
        meshes.append(o)
print("armature:", arm.name if arm else None, "meshes:", [m.name for m in meshes])

bones = arm.data.bones
print("bone count:", len(bones))
roots = [b.name for b in bones if b.parent is None]
print("root bones:", roots)

# 打印骨架树（前 3 层）
def walk(b, d=0, maxd=3):
    if d > maxd:
        return
    print("   " + "  " * d + f"{b.name}  head={tuple(round(v,3) for v in b.head_local)}")
    for c in b.children:
        walk(c, d + 1, maxd)
for r in [b for b in bones if b.parent is None]:
    walk(r)

# 动画信息
acts = [a.name for a in bpy.data.actions]
print("actions:", acts)
sc = bpy.context.scene
if arm.animation_data and arm.animation_data.action:
    act = arm.animation_data.action
    fr = act.frame_range
    print("action:", act.name, "frame_range:", fr)
    sc.frame_start = int(fr[0])
    sc.frame_end = int(fr[1])
else:
    print("no action bound")

# 世界空间包围盒（判断身高/朝向）
depsgraph = bpy.context.evaluated_depsgraph_get()
mn = Vector((1e9, 1e9, 1e9))
mx = Vector((-1e9, -1e9, -1e9))
for m in meshes:
    ev = m.evaluated_get(depsgraph)
    for v in ev.data.vertices:
        w = ev.matrix_world @ v.co
        for i in range(3):
            mn[i] = min(mn[i], w[i])
            mx[i] = max(mx[i], w[i])
print("mesh world bounds min:", tuple(round(v, 3) for v in mn), "max:", tuple(round(v, 3) for v in mx))
print("size:", tuple(round(mx[i] - mn[i], 3) for i in range(3)))

# ---------- 渲染设置 ----------
sc.render.engine = 'CYCLES'
sc.cycles.samples = 24
sc.cycles.use_denoising = False
sc.render.resolution_x = 420
sc.render.resolution_y = 560
sc.render.film_transparent = False

world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.78, 0.82, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

# 太阳光
light_data = bpy.data.lights.new("Sun", type='SUN')
light_data.energy = 3.0
light = bpy.data.objects.new("Sun", light_data)
sc.collection.objects.link(light)
light.rotation_euler = (math.radians(50), 0, math.radians(30))

# 相机：侧视（沿 -X 看向 +X）
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = max(2.6, (mx[2] - mn[2]) * 1.15)
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam
center = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, (mn.z + mx.z) / 2))
cam.location = center + Vector((-6.0, 0.0, 0.0))
cam.rotation_euler = (math.radians(90), 0, math.radians(-90))

f0, f1 = int(sc.frame_start), int(sc.frame_end)
span = max(1, f1 - f0)
frames = [f0 + int(round(span * t)) for t in (0.0, 0.25, 0.5, 0.75)]
print("rendering frames:", frames)
for i, f in enumerate(frames):
    sc.frame_set(f)
    sc.render.filepath = os.path.join(OUT, f"src_run_{i}_f{f:03d}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", sc.render.filepath)

print("=== BLENDER DONE ===")
