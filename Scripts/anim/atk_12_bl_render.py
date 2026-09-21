"""渲染攻击动画关键帧（灰模，正交相机，正侧两视角）—— 用于人眼验收。

两种模式：
  fbx  : 导入一个 FBX（自带骨架+网格+已烘焙动作）
  glb  : 导入 GLB 并挂上指定 clip 的动作（用于渲染「源」作对照）

用法：
  blender -b -P Scripts/anim/atk_12_bl_render.py -- \
      <fbx|glb> <输入路径> <clip 或 -> <输出目录> <标签> [帧号,逗号分隔]
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE, SRC, CLIP, OUT, LABEL = argv[0], argv[1], argv[2], argv[3], argv[4]
FRAMES = [int(x) for x in argv[5].split(",")] if len(argv) > 5 and argv[5] else None
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30

if MODE == "glb":
    bpy.ops.import_scene.gltf(filepath=SRC)
    arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
    act = bpy.data.actions.get(CLIP)
    if act is None:
        raise SystemExit("找不到动作 %s" % CLIP)
    if not arm.animation_data:
        arm.animation_data_create()
    arm.animation_data.action = act
else:
    bpy.ops.import_scene.fbx(filepath=SRC)
    arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
    act = arm.animation_data.action if arm.animation_data else (
        bpy.data.actions[0] if bpy.data.actions else None)

meshes = [o for o in bpy.data.objects if o.type == "MESH" and o.parent is arm] or \
         [o for o in bpy.data.objects if o.type == "MESH"]
print("模式=%s 骨架=%s 骨数=%d 网格=%d 动作=%s 帧=%s" % (
    MODE, arm.name, len(arm.data.bones), len(meshes),
    act.name if act else None, tuple(round(x) for x in act.frame_range) if act else None))

f0, f1 = (int(round(act.frame_range[0])), int(round(act.frame_range[1]))) if act else (0, 0)
sc.frame_start, sc.frame_end = f0, f1
if FRAMES is None:
    FRAMES = [f0, f0 + (f1 - f0) // 6, f0 + (f1 - f0) // 2, f1]
FRAMES = [max(f0, min(f1, f)) for f in FRAMES]

HUMAN = ["root", "pelvis", "spine_01", "spine_03", "neck_01", "head",
         "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r",
         "hand_l", "hand_r", "thigh_l", "thigh_r", "calf_l", "calf_r",
         "foot_l", "foot_r", "ball_l", "ball_r",
         "Root", "Pelvis", "Spine1", "Spine2", "Neck", "Head",
         "L_Clavicle", "L_Shoulder", "L_Elbow", "L_Hand",
         "R_Clavicle", "R_Shoulder", "R_Elbow", "R_Hand",
         "L_Hip", "L_KneeLower", "L_Foot", "L_Toe",
         "R_Hip", "R_KneeLower", "R_Foot", "R_Toe", "weapon_jnt"]


def pts(f):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    return [arm.matrix_world @ arm.pose.bones[n].head
            for n in HUMAN if n in arm.pose.bones]


def _h(nm):
    return arm.matrix_world @ arm.pose.bones[nm].head if nm in arm.pose.bones else None


# 取景只用「角色本体」的上下端 —— 骨架里混着 SnapWeapon/Throne 之类远点，
# 用全骨包围盒会把镜头拉飞（实测）。
tops, bots, ctrs = [], [], []
for f in FRAMES:
    sc.frame_set(f)
    bpy.context.view_layer.update()
    hd = next((_h(n) for n in ("head", "Head") if _h(n)), None)
    pel = next((_h(n) for n in ("pelvis", "Pelvis") if _h(n)), None)
    if hd:
        tops.append(hd.z)
    feet = [_h(n) for n in ("foot_l", "foot_r", "ball_l", "ball_r",
                            "L_Foot", "R_Foot", "L_Toe", "R_Toe") if _h(n)]
    if feet:
        bots.append(min(p.z for p in feet))
    if pel:
        ctrs.append(pel)
top = max(tops) if tops else 1.0
bot = min(bots) if bots else 0.0
cx = sum(p.x for p in ctrs) / len(ctrs) if ctrs else 0.0
cy = sum(p.y for p in ctrs) / len(ctrs) if ctrs else 0.0
size = Vector((0.0, 0.0, max(top - bot, 1e-3)))
center = Vector((cx, cy, (top + bot) / 2))
print("取景: 头顶=%.2f 脚底=%.2f 高=%.2f center=%s" % (
    top, bot, top - bot, tuple(round(v, 2) for v in center)))

# GLB 里混了宝座/狮子/狼等道具与变身子网格 —— 按半径 + 材质名一起剔
if MODE == "glb":
    import bmesh
    BAD = ("wolf", "lion", "throne", "gem", "piece", "monument", "tower", "flag")
    r = max(size.z * 1.6, 1e-3)
    for m in meshes:
        slots = [s.material.name if s.material else "?" for s in m.material_slots]
        print("   材质槽: %s" % slots)
        bad_idx = {i for i, n in enumerate(slots) if any(b in n.lower() for b in BAD)}
        bm = bmesh.new()
        bm.from_mesh(m.data)
        kill = [v for v in bm.verts if ((m.matrix_world @ v.co) - center).length > r]
        if bad_idx:
            bm.faces.ensure_lookup_table()
            kill += [f for f in bm.faces if f.material_index in bad_idx]
        if kill:
            bmesh.ops.delete(bm, geom=kill, context="FACES_KEEP_BOUNDARY")
            print("   剔除 %d 个元素（材质黑名单 %s）" % (len(kill), sorted(bad_idx)))
        bm.to_mesh(m.data)
        bm.free()

# 材质
mat = bpy.data.materials.new("Grey")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.55, 0.57, 0.62, 1)
bsdf.inputs["Roughness"].default_value = 0.7
for m in meshes:
    m.data.materials.clear()
    m.data.materials.append(mat)

bpy.ops.mesh.primitive_plane_add(size=max(size.length * 3, 1.0), location=(center.x, center.y, 0))
fmat = bpy.data.materials.new("Floor")
fmat.use_nodes = True
fmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.36, 0.4, 1)
bpy.context.active_object.data.materials.append(fmat)

try:
    sc.render.engine = "BLENDER_EEVEE"
except Exception:
    sc.render.engine = "BLENDER_EEVEE_NEXT"
try:
    sc.eevee.taa_render_samples = 16
except Exception:
    pass
sc.render.resolution_x, sc.render.resolution_y = 460, 600
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.74, 0.77, 0.82, 1.0)

ld = bpy.data.lights.new("Sun", type="SUN")
ld.energy = 4.0
lo = bpy.data.objects.new("Sun", ld)
sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(50), 0, math.radians(-35))

cd = bpy.data.cameras.new("Cam")
cd.type = "ORTHO"
cd.ortho_scale = max(size.z * 1.5, size.length * 0.8, 1e-3)
cam = bpy.data.objects.new("Cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam


def render_view(tag, dvec):
    d = Vector(dvec).normalized()
    cam.location = center + d * (size.length * 2.0 + 1.0)
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    for f in FRAMES:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(OUT, "%s_%s_f%03d.png" % (LABEL, tag, f))
        bpy.ops.render.render(write_still=True)


for tag, d in (("front", (0.0, -1.0, 0.05)), ("side", (-1.0, 0.0, 0.05))):
    render_view(tag, d)
print("=== RENDER DONE === %s" % OUT)
