"""
剥离描边壳里的「披风几何副本」。

背景：材质槽 0「描边壳」是整模的反向外扩副本，里面含一份披风 —— 披风一旦走顶点级布料，
这份副本不会跟着动，画面上会出现僵硬的鬼影披风。本脚本把它删掉。

判据：外壳顶点上 `cape_chain_*` 权重之和（权重由骨架保证，比空间距离可靠；
空间距离只用来【报告】潜在漏删，不参与删除）。

用法: blender -b -P <本文件> -- <IN_FBX> <OUT_FBX> <OUTDIR>
"""
import os
import sys
import bmesh
import bpy
import math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
IN_FBX, OUT_FBX, OUTDIR = argv[0], argv[1], argv[2]
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)
W_THRESH = 0.25
FACE_RATIO = 0.6

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=IN_FBX, automatic_bone_orientation=True)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = [o for o in bpy.data.objects if o.type == 'MESH']


def mats(o):
    return " ".join(s.material.name for s in o.material_slots if s.material)


cape_obj = next((o for o in meshes if "Cape" in mats(o)), None)
shell_obj = next((o for o in meshes if "Outline" in mats(o)), None)
print("### 披风网格: %s  描边壳: %s" % (cape_obj.name if cape_obj else None,
                                        shell_obj.name if shell_obj else None))
assert cape_obj and shell_obj


def arm_space(o):
    return arm.matrix_world.inverted() @ o.matrix_world


def pts_of(o):
    m = arm_space(o)
    return np.asarray([[*(m @ v.co)] for v in o.data.vertices], dtype=np.float32)


def nn_dist(src, dst, chunk=256):
    out = np.empty(len(src), dtype=np.float32)
    for s in range(0, len(src), chunk):
        e = min(s + chunk, len(src))
        d2 = ((src[s:e, None, :] - dst[None, :, :]) ** 2).sum(axis=2)
        out[s:e] = np.sqrt(d2.min(axis=1))
    return out


CAP = pts_of(cape_obj)
cape_group_idx = [g.index for g in shell_obj.vertex_groups if "cape_chain" in g.name.lower()]
print("### 描边壳顶点=%d 面=%d  其中 cape 顶点组=%d 个" % (
    len(shell_obj.data.vertices), len(shell_obj.data.polygons), len(cape_group_idx)))

wsum = np.zeros(len(shell_obj.data.vertices), dtype=np.float32)
for v in shell_obj.data.vertices:
    wsum[v.index] = sum(g.weight for g in v.groups if g.group in cape_group_idx)
hist = [int((wsum > t).sum()) for t in (0.1, 0.25, 0.5, 0.75, 0.99)]
print("### 壳上 cape 权重和 > [0.1,0.25,0.5,0.75,0.99] 的顶点数: %s / %d" % (hist, len(wsum)))

SHELL = pts_of(shell_obj)
d_before = nn_dist(SHELL, CAP)
print("### 剥离前：壳上到披风 <=2cm 的顶点 = %d，其中权重和<=%.2f 的（潜在漏删）= %d" % (
    int((d_before <= 0.02).sum()), W_THRESH,
    int(((d_before <= 0.02) & (wsum <= W_THRESH)).sum())))

# ---------------------------------------------------------------- 渲染设置
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 16
sc.cycles.use_denoising = False
sc.render.resolution_x = 640
sc.render.resolution_y = 720
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.72, 0.75, 0.80, 1.0)
ld = bpy.data.lights.new("S", type='SUN')
ld.energy = 4.0
lo = bpy.data.objects.new("S", ld)
sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(52), 0, math.radians(-30))
cd = bpy.data.cameras.new("C")
cd.type = 'ORTHO'
cd.ortho_scale = 2.3
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam
target = Vector((0.0, 0.0, 1.05))
VIEWS = [("back", (0.0, 3.0, 0.15)), ("q34", (-2.0, 2.0, 0.35))]


def shoot(suffix, only=()):
    for o in meshes:
        o.hide_render = bool(only) and o not in only
    for tag, dv in VIEWS:
        d = Vector(dv).normalized()
        cam.location = target + d * 5.0
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUTDIR, "CAPE_%s_%s.png" % (tag, suffix))
        bpy.ops.render.render(write_still=True)
        print("### rendered %s" % sc.render.filepath)


shoot("shellonly_before", only=(shell_obj, cape_obj))
shoot("all_before")

# ---------------------------------------------------------------- 删除
bm = bmesh.new()
bm.from_mesh(shell_obj.data)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
mark = {i for i in range(len(wsum)) if wsum[i] > W_THRESH}
dead = [f for f in bm.faces if sum(1 for v in f.verts if v.index in mark) >= len(f.verts) * FACE_RATIO]
print("### 标记顶点 %d，删除面 %d / %d" % (len(mark), len(dead), len(bm.faces)))
bmesh.ops.delete(bm, geom=dead, context='FACES')
bm.to_mesh(shell_obj.data)
bm.free()
shell_obj.data.update()
print("### 剥离后：顶点 %d 面 %d（原 %d / %d）" % (
    len(shell_obj.data.vertices), len(shell_obj.data.polygons),
    len(SHELL), len(shell_obj.data.polygons) + len(dead)))

SHELL2 = pts_of(shell_obj)
d_after = nn_dist(SHELL2, CAP)
print("### 剥离后：壳上到披风 <=2cm 的顶点 = %d（剥离前 %d）" % (
    int((d_after <= 0.02).sum()), int((d_before <= 0.02).sum())))

shoot("shellonly_after", only=(shell_obj, cape_obj))
shoot("all_after")

# ---------------------------------------------------------------- 导出
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
for o in meshes:
    o.select_set(True)
bpy.ops.export_scene.fbx(
    filepath=OUT_FBX, use_selection=True, add_leaf_bones=False,
    primary_bone_axis='Y', secondary_bone_axis='X', apply_unit_scale=True,
    global_scale=1.0, mesh_smooth_type='FACE', armature_nodetype='NULL', bake_anim=False)
print("### 导出: %s" % OUT_FBX)
print("### DONE")
