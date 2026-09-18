"""
Blender 无头：渲染动画预览（自动以人形骨骼定框，屏蔽王座/狼灵/宝石等道具）
用法: blender -b -P blender_02_render_anim.py -- <GLB|FBX> <OUTDIR> <LABEL> [hide_props:0|1]
"""
import bpy
import sys
import os
import math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = argv[0]
OUT = argv[1]
LABEL = argv[2] if len(argv) > 2 else "anim"
HIDE_PROPS = (argv[3] != "0") if len(argv) > 3 else True
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
print("=== IMPORT ===", SRC)
if SRC.lower().endswith(".glb") or SRC.lower().endswith(".gltf"):
    bpy.ops.import_scene.gltf(filepath=SRC)
else:
    bpy.ops.import_scene.fbx(filepath=SRC, automatic_bone_orientation=True)

arm = None
meshes = []
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        arm = o
    elif o.type == 'MESH':
        meshes.append(o)
print("armature:", arm.name if arm else None, "meshes:", [m.name for m in meshes])

PROP_KEYS = ["throne", "gem", "piece", "lion", "wolf", "backpack"]
if HIDE_PROPS:
    for m in meshes:
        if any(k in m.name.lower() for k in PROP_KEYS):
            print("  hiding prop mesh:", m.name)
            m.hide_render = True
            m.hide_viewport = True

# 用骨骼名过滤出"人形骨骼"用于定框
HUMAN_KEYS = ("pelvis", "spine", "neck", "head", "hip", "knee", "foot", "toe", "clavicle",
              "shoulder", "elbow", "hand", "upperarm", "lowerarm", "thigh", "calf", "ball")
human_bones = []
if arm:
    for b in arm.data.bones:
        n = b.name.lower()
        if any(k in n for k in HUMAN_KEYS) and "lion" not in n and "throne" not in n:
            human_bones.append(b)
print("human bones used for framing:", len(human_bones))

sc = bpy.context.scene
if arm and arm.animation_data and arm.animation_data.action:
    act = arm.animation_data.action
    sc.frame_start = int(act.frame_range[0])
    sc.frame_end = int(act.frame_range[1])
    print("action:", act.name, sc.frame_start, sc.frame_end)

def bounds_at_frame(f):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for b in human_bones:
        for p in (b.head_local, b.tail_local):
            w = arm.matrix_world @ p
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
    return mn, mx

f0, f1 = int(sc.frame_start), int(sc.frame_end)
span = max(1, f1 - f0)
frames = [f0 + int(round(span * t)) for t in (0.0, 0.2, 0.4, 0.6, 0.8)]
mn = Vector((1e9, 1e9, 1e9)); mx = Vector((-1e9, -1e9, -1e9))
for f in frames:
    a, b = bounds_at_frame(f)
    for i in range(3):
        mn[i] = min(mn[i], a[i]); mx[i] = max(mx[i], b[i])
size = Vector((mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2]))
center = Vector(((mn.x+mx.x)/2, (mn.y+mx.y)/2, (mn.z+mx.z)/2))
print("humanoid bounds min:", tuple(round(v,3) for v in mn), "max:", tuple(round(v,3) for v in mx))
print("humanoid size:", tuple(round(v,3) for v in size))

# 材质：统一哑光灰
mat = bpy.data.materials.new("PreviewGrey")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.55, 0.57, 0.6, 1)
bsdf.inputs["Roughness"].default_value = 0.65
for m in meshes:
    if m.hide_render:
        continue
    m.data.materials.clear()
    m.data.materials.append(mat)

sc.render.engine = 'CYCLES'
sc.cycles.samples = 24
sc.cycles.use_denoising = False
sc.render.resolution_x = 400
sc.render.resolution_y = 560
world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.72, 0.75, 0.80, 1.0)

ld = bpy.data.lights.new("Sun", type='SUN'); ld.energy = 3.5
lo = bpy.data.objects.new("Sun", ld); sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(55), 0, math.radians(35))

cd = bpy.data.cameras.new("Cam"); cd.type = 'ORTHO'
cd.ortho_scale = max(size.z * 1.25, size.x * 1.6, 1.0)
cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam

def render_view(tag, offset, extra_rot_z=0.0):
    cam.location = center + Vector(offset)
    d = (center - cam.location)
    yaw = math.degrees(math.atan2(d.y, d.x))
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, d.z / max(1e-6, d.length)))))
    cam.rotation_euler = (math.radians(90 - pitch), 0, math.radians(yaw + 90 + extra_rot_z))
    for i, f in enumerate(frames):
        sc.frame_set(f)
        sc.render.filepath = os.path.join(OUT, f"{LABEL}_{tag}_{i}_f{f:03d}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", sc.render.filepath)

D = max(size.length, 1.0)
render_view("side", (-D * 2.2, 0.0, 0.0))
render_view("front34", (-D * 1.6, -D * 1.6, size.z * 0.15))
print("=== BLENDER DONE ===")
