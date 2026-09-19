"""
骨架棒图 A/B 对比：左=源 LOL，右=重定向结果。同一相机、同一帧、同一比例。
用法: blender -b -P blender_85_stick_ab.py -- <SRC_GLB> <TGT_FBX> <RT_FBX> <OUTDIR> <ANIM> [frames]
"""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB, TGT_FBX, RT_FBX, OUTDIR, ANIM = argv[0], argv[1], argv[2], argv[3], argv[4]
FRAMES = [int(x) for x in argv[5].split(",")] if len(argv) > 5 else [0, 7, 14, 21]
os.makedirs(OUTDIR, exist_ok=True)

def imp(p, k):
    before = set(bpy.data.objects)
    if k == "fbx": bpy.ops.import_scene.fbx(filepath=p, automatic_bone_orientation=True)
    else: bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == 'ARMATURE'][0]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30
src = imp(SRC_GLB, "glb"); tgt = imp(TGT_FBX, "fbx"); rt = imp(RT_FBX, "fbx")
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = True; o.hide_viewport = True
sn = {src.animation_data.action.name} if (src.animation_data and src.animation_data.action) else set()
cand = [a for a in bpy.data.actions if a.name not in sn]
if cand and rt.animation_data: rt.animation_data.action = cand[-1]
print("重定向动作:", rt.animation_data.action.name if rt.animation_data else None)

# 骨架关节（源名, 目标名）—— 仅画人体主干，保证可读
JOINTS = [("Pelvis","pelvis"),("Spine1","spine_01"),("Spine2","spine_02"),("Neck","neck_01"),("Head","head"),
          ("L_Clavicle","clavicle_l"),("L_Shoulder","upperarm_l"),("L_Elbow","lowerarm_l"),("L_Hand","hand_l"),
          ("R_Clavicle","clavicle_r"),("R_Shoulder","upperarm_r"),("R_Elbow","lowerarm_r"),("R_Hand","hand_r"),
          ("L_Hip","thigh_l"),("L_KneeLower","calf_l"),("L_Foot","foot_l"),("L_Toe","toe_l"),
          ("R_Hip","thigh_r"),("R_KneeLower","calf_r"),("R_Foot","foot_r"),("R_Toe","toe_r")]
BONES = [("Pelvis","Spine1"),("Spine1","Spine2"),("Spine2","Neck"),("Neck","Head"),
         ("Spine2","L_Clavicle"),("L_Clavicle","L_Shoulder"),("L_Shoulder","L_Elbow"),("L_Elbow","L_Hand"),
         ("Spine2","R_Clavicle"),("R_Clavicle","R_Shoulder"),("R_Shoulder","R_Elbow"),("R_Elbow","R_Hand"),
         ("Pelvis","L_Hip"),("L_Hip","L_KneeLower"),("L_KneeLower","L_Foot"),("L_Foot","L_Toe"),
         ("Pelvis","R_Hip"),("R_Hip","R_KneeLower"),("R_KneeLower","R_Foot"),("R_Foot","R_Toe")]

def wp(arm, n):
    pb = arm.pose.bones.get(n)
    return (arm.matrix_world @ pb.matrix).translation if pb else None

def build_stick(prefix, arm, joints, scale, offset, color):
    objs = []
    mat = bpy.data.materials.new(prefix+"M"); mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = 0.6
    for sn_, tn in joints:
        o = bpy.data.objects.get(prefix+"J_"+sn_)
        if o is None:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=1.0, location=(0,0,0))
            o = bpy.context.active_object; o.name = prefix+"J_"+sn_
            o.data.materials.clear(); o.data.materials.append(mat)
        o.scale = (scale, scale, scale)
        objs.append(o)
    for i, (a, b_) in enumerate(BONES):
        o = bpy.data.objects.get(prefix+"B_%d" % i)
        if o is None:
            bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=1.0, depth=1.0, location=(0,0,0))
            o = bpy.context.active_object; o.name = prefix+"B_%d" % i
            o.data.materials.clear(); o.data.materials.append(mat)
        objs.append(o)
    return objs

# 用源的高度做基准
sc.frame_set(0); bpy.context.view_layer.update()
def h_of(arm, joint_names):
    zs = []
    for n in joint_names:
        p = wp(arm, n)
        if p: zs.append(p.z)
    return max(zs) - min(zs) if zs else 1.0
src_h = h_of(src, [t for _, t in JOINTS] if False else [s for s, _ in JOINTS])
tgt_h = h_of(tgt, [t for _, t in JOINTS])
k = src_h / tgt_h
print(f"源骨架高 {src_h:.1f} 目标骨架高 {tgt_h:.3f} 比例 {k:.2f}")

stickS = build_stick("S_", src, JOINTS, src_h*0.018, None, (0.85, 0.45, 0.32, 1))
stickT = build_stick("T_", tgt, JOINTS, src_h*0.018/k, None, (0.35, 0.55, 0.85, 1))

def place(prefix, arm, objs, scale, xoff, origin):
    def T(p):
        return Vector(((p.x-origin.x)*scale + xoff, (p.y-origin.y)*scale, (p.z-origin.z)*scale))
    for i, (sn_, tn) in enumerate(JOINTS):
        p = wp(arm, tn)
        if p is None: continue
        objs[i].location = T(p)
    for i, (a, b_) in enumerate(BONES):
        pa, pb_ = wp(arm, a), wp(arm, b_)
        o = objs[len(JOINTS)+i]
        if pa is None or pb_ is None: continue
        va = T(pa); vb = T(pb_)
        d = vb - va
        if d.length < 1e-6: continue
        o.location = (va + vb) * 0.5
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = Vector((0,0,1)).rotation_difference(d.normalized())
        o.scale = (src_h*0.006, src_h*0.006, d.length)

sc.frame_set(0); bpy.context.view_layer.update()
orgS = wp(src, "Pelvis"); orgT = wp(tgt, "pelvis")
print("orgS", orgS, "orgT", orgT)
gap = src_h * 0.42
sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = False
sc.render.resolution_x = 900; sc.render.resolution_y = 620
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.90, 0.91, 0.93, 1.0)
ld = bpy.data.lights.new("S", type='SUN'); ld.energy = 5.0
lo = bpy.data.objects.new("S", ld); sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(50), 0, math.radians(-40))
cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'; cd.ortho_scale = src_h * 1.9
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
center = Vector((0, 0, src_h*0.30))
cam.location = center + Vector((-1, 0, 0)) * (src_h*4)
cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()

sact = None
for a in bpy.data.actions:
    if a.name == ANIM or a.name.endswith("_"+ANIM) or a.name.endswith(ANIM): sact = a
if sact: src.animation_data.action = sact
F0 = int(sact.frame_range[0]) if sact else 0
ract = rt.animation_data.action if rt.animation_data else None
rF0 = int(ract.frame_range[0]) if ract else 1

for f in FRAMES:
    sc.frame_set(F0 + f); bpy.context.view_layer.update()
    place("S_", src, stickS, 1.0, -gap, orgS)
    sc.frame_set(rF0 + f); bpy.context.view_layer.update()
    place("T_", rt, stickT, k, gap, orgT)
    sc.render.filepath = os.path.join(OUTDIR, f"STICK_{ANIM}_f{f:03d}.png")
    bpy.ops.render.render(write_still=True)
    print("frame", f, "done")
print("=== DONE ===")
