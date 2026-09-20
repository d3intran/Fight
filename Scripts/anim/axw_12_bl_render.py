# -*- coding: utf-8 -*-
"""把「合并后的动作 FBX」套到 Darius 网格上渲染（网格来自 Darius_Walk_Layered.fbx）。
用法: blender -b -P <本脚本> -- <MESH_FBX> <ANIM_FBX> <OUTDIR> <LABEL> <NFRAMES>
"""
import bpy
import sys
import os
import math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MESH_FBX, ANIM_FBX, OUT, LABEL = argv[0], argv[1], argv[2], argv[3]
NFR = int(argv[4]) if len(argv) > 4 else 7
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1) 网格 + 骨架 + 原动作
bpy.ops.import_scene.fbx(filepath=MESH_FBX)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
orig_action = arm.animation_data.action if arm.animation_data else None
print("mesh armature=%s meshes=%d orig_action=%s" % (arm.name, len(meshes),
                                                     orig_action.name if orig_action else None))

# 2) 目标动作
before = set(a.name for a in bpy.data.actions)
bpy.ops.import_scene.fbx(filepath=ANIM_FBX)
new_actions = [a for a in bpy.data.actions if a.name not in before]
print("new actions = %s" % [(a.name, tuple(round(x) for x in a.frame_range)) for a in new_actions])
if not new_actions:
    print("!! 没拿到新动作")
    sys.exit(1)
target = new_actions[0]
print("chosen action = %s range %s" % (target.name, tuple(round(x) for x in target.frame_range)))

# 3) 删掉第二次导入的骨架/网格，只保留动作
keep = {arm} | set(meshes)
for o in list(bpy.data.objects):
    if o not in keep:
        bpy.data.objects.remove(o, do_unlink=True)

# 4) 把目标动作套到原骨架上
if not arm.animation_data:
    arm.animation_data_create()
arm.animation_data.action = target

sc = bpy.context.scene
f0, f1 = int(target.frame_range[0]), int(target.frame_range[1])
sc.frame_start, sc.frame_end = f0, f1
span = max(1, f1 - f0)
frames = [f0 + int(round(span * i / (NFR - 1))) for i in range(NFR)]
print("frames = %s  (range %d..%d)" % (frames, f0, f1))

# 5) 骨骼定框
HUMAN = ["root", "pelvis", "spine_01", "spine_03", "neck_01", "head",
         "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r",
         "hand_l", "hand_r", "thigh_l", "thigh_r", "calf_l", "calf_r",
         "foot_l", "foot_r", "ball_l", "ball_r", "toe_l", "toe_r", "weapon_jnt"]


def pts(f):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    out = []
    for n in HUMAN:
        pb = arm.pose.bones.get(n)
        if pb:
            out.append(arm.matrix_world @ pb.head)
    return out


mn = Vector((1e9,) * 3)
mx = Vector((-1e9,) * 3)
for f in frames:
    for p in pts(f):
        for i in range(3):
            mn[i] = min(mn[i], p[i])
            mx[i] = max(mx[i], p[i])
size = Vector((mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]))
center = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, (mn.z + mx.z) / 2))
print("bbox min=%s max=%s size=%s" % (tuple(round(v, 2) for v in mn),
                                      tuple(round(v, 2) for v in mx),
                                      tuple(round(v, 2) for v in size)))

# 6) 材质 / 灯光 / 相机
mat = bpy.data.materials.new("PreviewGrey")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.55, 0.57, 0.62, 1)
b.inputs["Roughness"].default_value = 0.7
for m in meshes:
    m.data.materials.clear()
    m.data.materials.append(mat)

# 地面板（便于判断是否穿地）
bpy.ops.mesh.primitive_plane_add(size=6.0, location=(0, 0, 0))
floor = bpy.context.active_object
fmat = bpy.data.materials.new("Floor")
fmat.use_nodes = True
fmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.36, 0.4, 1)
floor.data.materials.append(fmat)

sc.render.engine = 'BLENDER_EEVEE'
try:
    sc.eevee.taa_render_samples = 16
except AttributeError:
    pass
sc.render.resolution_x = 480
sc.render.resolution_y = 620
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.74, 0.77, 0.82, 1.0)

ld = bpy.data.lights.new("Sun", type='SUN')
ld.energy = 4.0
lo = bpy.data.objects.new("Sun", ld)
sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(50), 0, math.radians(-35))

cd = bpy.data.cameras.new("Cam")
cd.type = 'ORTHO'
cd.ortho_scale = max(size.z * 1.35, 1.0)
cam = bpy.data.objects.new("Cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam


def mesh_bbox(f):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for m in meshes:
        me = m.evaluated_get(dg)
        try:
            ms = me.to_mesh()
            for v in ms.vertices:
                w = m.matrix_world @ v.co
                for i in range(3):
                    lo[i] = min(lo[i], w[i])
                    hi[i] = max(hi[i], w[i])
            me.to_mesh_clear()
        except Exception as ex:
            print("   eval fail %s" % ex)
    return lo, hi


print("--- 逐帧网格包围盒（地面 = 0）---")
for f in frames:
    lo, hi = mesh_bbox(f)
    print("   f%-4d min=%s  max=%s" % (f, [round(v, 3) for v in lo], [round(v, 3) for v in hi]))


def render_view(tag, dvec):
    d = Vector(dvec).normalized()
    dist = max(size.length, 1.0) * 2.0
    cam.location = center + d * dist
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for i, f in enumerate(frames):
        sc.frame_set(f)
        sc.render.filepath = os.path.join(OUT, "%s_%s_%02d_f%03d.png" % (LABEL, tag, i, f))
        bpy.ops.render.render(write_still=True)


for v, d in (("side", (-1.0, 0.0, 0.0)), ("front34", (-0.8, -1.0, 0.12))):
    render_view(v, d)
print("=== BLENDER DONE ===")
