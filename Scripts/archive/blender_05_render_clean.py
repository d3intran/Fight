"""
Blender 无头：剔除道具网格后渲染动画预览
用法: blender -b -P blender_05_render_clean.py -- <GLB|FBX> <OUTDIR> <LABEL> [prop_keys]
"""
import bpy
import bmesh
import sys
import os
import math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, OUT, LABEL = argv[0], argv[1], argv[2]
KEYS = (argv[3] if len(argv) > 3 else "wolf|throne|gem|piece").split("|")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
if SRC.lower().endswith((".glb", ".gltf")):
    bpy.ops.import_scene.gltf(filepath=SRC)
else:
    bpy.ops.import_scene.fbx(filepath=SRC, automatic_bone_orientation=True)

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
sc = bpy.context.scene
if arm.animation_data and arm.animation_data.action:
    a = arm.animation_data.action
    sc.frame_start, sc.frame_end = int(a.frame_range[0]), int(a.frame_range[1])
    print("action:", a.name, sc.frame_start, sc.frame_end)

# ---- 剔除道具材质对应的面 ----
for m in meshes:
    slots = [s.material.name.lower() if s.material else "" for s in m.material_slots]
    kill = [i for i, n in enumerate(slots) if any(k in n for k in KEYS)]
    print(f"mesh {m.name}: slots={slots} killing={kill}")
    if not kill:
        continue
    bm = bmesh.new()
    bm.from_mesh(m.data)
    bm.faces.ensure_lookup_table()
    dead = [f for f in bm.faces if f.material_index in kill]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(m.data)
    bm.free()
    m.data.update()

HUMAN = ["Root", "root", "Pelvis", "pelvis", "Spine1", "spine_01", "Spine2", "spine_02", "spine_03",
         "Neck", "neck_01", "Head", "head", "L_Hip", "R_Hip", "thigh_l", "thigh_r",
         "L_KneeUpper", "R_KneeUpper", "calf_l", "calf_r", "L_KneeLower", "R_KneeLower",
         "L_Foot", "R_Foot", "foot_l", "foot_r", "L_Toe", "R_Toe", "ball_l", "ball_r",
         "toe_l", "toe_r", "L_Clavicle", "R_Clavicle", "clavicle_l", "clavicle_r",
         "L_Shoulder", "R_Shoulder", "L_Elbow", "R_Elbow", "upperarm_l", "upperarm_r",
         "lowerarm_l", "lowerarm_r", "L_Hand", "R_Hand", "hand_l", "hand_r",
         "SnapWeapon", "weapon_jnt"]

def human_pts(f):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    out = []
    for n in HUMAN:
        pb = arm.pose.bones.get(n)
        if pb:
            out.append(arm.matrix_world @ pb.head)
    return out

f0, f1 = int(sc.frame_start), int(sc.frame_end)
span = max(1, f1 - f0)
frames = [f0 + int(round(span * t)) for t in (0.0, 0.2, 0.4, 0.6, 0.8)]
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for f in frames:
    for p in human_pts(f):
        for i in range(3):
            mn[i] = min(mn[i], p[i]); mx[i] = max(mx[i], p[i])
size = Vector((mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]))
center = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, (mn.z + mx.z) / 2))
print("humanoid size:", tuple(round(v, 2) for v in size), "center:", tuple(round(v, 2) for v in center))

mat = bpy.data.materials.new("PreviewGrey")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.6, 0.62, 0.66, 1)
b.inputs["Roughness"].default_value = 0.7
for m in meshes:
    m.data.materials.clear()
    m.data.materials.append(mat)

sc.render.engine = 'CYCLES'
sc.cycles.samples = 20
sc.cycles.use_denoising = False
sc.render.resolution_x = 420
sc.render.resolution_y = 560
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.74, 0.77, 0.82, 1.0)
ld = bpy.data.lights.new("Sun", type='SUN'); ld.energy = 4.0
lo = bpy.data.objects.new("Sun", ld); sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(50), 0, math.radians(-35))
cd = bpy.data.cameras.new("Cam"); cd.type = 'ORTHO'
cd.ortho_scale = max(size.z * 1.25, 1.0)
cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam

def render_view(tag, dirv):
    d = Vector(dirv).normalized()
    cam.location = center + d * max(size.length, 1.0) * 2.0
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for i, f in enumerate(frames):
        sc.frame_set(f)
        sc.render.filepath = os.path.join(OUT, f"{LABEL}_{tag}_{i}_f{f:03d}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", sc.render.filepath)

render_view("side", (-1.0, 0.0, 0.0))
render_view("front34", (-0.8, -1.0, 0.12))
print("=== BLENDER DONE ===")
