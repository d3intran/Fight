"""
A/B 并排对比：左=源 LOL 动画(暖色)  右=重定向后 2XKO 动画(冷色)
用法: blender -b -P blender_61_ab.py -- <SRC_GLB> <TGT_FBX> <RT_FBX> <OUTDIR> <ANIM> [frames]
"""
import bpy, bmesh, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB, TGT_FBX, RT_FBX, OUTDIR, ANIM = argv[0], argv[1], argv[2], argv[3], argv[4]
FRAMES = [int(x) for x in argv[5].split(",")] if len(argv) > 5 else [0, 7, 14, 21]
os.makedirs(OUTDIR, exist_ok=True)

def imp(p, kind):
    before = set(bpy.data.objects)
    if kind == "fbx":
        bpy.ops.import_scene.fbx(filepath=p, automatic_bone_orientation=True)
    else:
        bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    return ([o for o in new if o.type == 'ARMATURE'][0], [o for o in new if o.type == 'MESH'],
            [o for o in new if o.type == 'ACTION'])

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
src, src_meshes, _ = imp(SRC_GLB, "glb")
tgt, tgt_meshes, _ = imp(TGT_FBX, "fbx")
rt, rt_meshes, _ = imp(RT_FBX, "fbx")
print(f"src={src.name} tgt={tgt.name}(meshes {len(tgt_meshes)}) rt={rt.name}")

# 把重定向动作挂到带网格的目标骨架上
print("全部动作:", [a.name for a in bpy.data.actions])
src_act_names = set()
if src.animation_data and src.animation_data.action:
    src_act_names.add(src.animation_data.action.name)
rt_act = rt.animation_data.action if (rt.animation_data and rt.animation_data.action) else None
if rt_act is None:
    cand = [a for a in bpy.data.actions if a.name not in src_act_names]
    rt_act = cand[-1] if cand else None
print("选中的重定向动作:", rt_act.name if rt_act else None)
if rt_act:
    if tgt.animation_data is None: tgt.animation_data_create()
    tgt.animation_data.action = rt_act
    try:
        slots = rt_act.slots
        if len(slots):
            tgt.animation_data.action_slot = slots[0]
            print("绑定 slot:", slots[0].name_display)
    except Exception as e:
        print("slot err:", e)
    print("已挂载:", tgt.animation_data.action.name, tgt.animation_data.action.frame_range)

# 源：剔除狼灵/王座
for m in src_meshes:
    slots = [s.material.name.lower() if s.material else "" for s in m.material_slots]
    kill = [i for i, n in enumerate(slots) if any(k in n for k in ("wolf", "throne", "gem"))]
    if kill:
        bm = bmesh.new(); bm.from_mesh(m.data); bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in kill], context='FACES')
        bm.to_mesh(m.data); bm.free(); m.data.update()

def mkmat(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = 0.7
    return m
mS = mkmat("MS", (0.78, 0.52, 0.42, 1))   # 源 = 暖橙
mT = mkmat("MT", (0.45, 0.58, 0.80, 1))   # 目标 = 冷蓝
for m in src_meshes: m.data.materials.clear(); m.data.materials.append(mS)
for m in tgt_meshes: m.data.materials.clear(); m.data.materials.append(mT)
for m in rt_meshes:  m.hide_viewport = True; m.hide_render = True

def bbox_of(meshes):
    mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
    dg = bpy.context.evaluated_depsgraph_get()
    for o in meshes:
        ev = o.evaluated_get(dg)
        for v in ev.data.vertices:
            w = ev.matrix_world @ v.co
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    return mn, mx

sc.frame_set(0); bpy.context.view_layer.update()
mnS, mxS = bbox_of(src_meshes)
mnT, mxT = bbox_of(tgt_meshes)
hS = mxS.z - mnS.z; hT = mxT.z - mnT.z
k = hS / hT
print(f"源高度 {hS:.2f} 目标高度 {hT:.2f} 比例 {k:.4f}")
gap = hS * 0.5
src.location = Vector((-gap - (mnS.x + mxS.x)/2, -(mnS.y + mxS.y)/2, -mnS.z))
tgt.scale = (k, k, k)
tgt.location = Vector((gap - (mnT.x + mxT.x)/2*k, -(mnT.y + mxT.y)/2*k, -mnT.z*k))
bpy.context.view_layer.update()

sc.render.engine = 'CYCLES'; sc.cycles.samples = 28; sc.cycles.use_denoising = False
sc.render.resolution_x = 1000; sc.render.resolution_y = 620
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.80, 0.82, 0.86, 1.0)
ld = bpy.data.lights.new("S", type='SUN'); ld.energy = 4.0
lo = bpy.data.objects.new("S", ld); sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(52), 0, math.radians(-35))
cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'; cd.ortho_scale = hS * 2.5
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
center = Vector((0, 0, hS * 0.5))
cam.location = center + Vector((-1.0, 0.0, 0.0)) * (hS * 4)
cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()

for f in FRAMES:
    sc.frame_set(f)
    sc.render.filepath = os.path.join(OUTDIR, f"AB_{ANIM}_f{f:03d}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", sc.render.filepath)
print("=== AB DONE ===")
