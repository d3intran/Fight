"""同机位分别渲染：源(暖) / 目标(冷)，用于逐帧对比"""
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
    return ([o for o in new if o.type == 'ARMATURE'][0], [o for o in new if o.type == 'MESH'])

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30
src, src_meshes = imp(SRC_GLB, "glb")
tgt, tgt_meshes = imp(TGT_FBX, "fbx")
rt, rt_meshes = imp(RT_FBX, "fbx")

src_names = {src.animation_data.action.name} if (src.animation_data and src.animation_data.action) else set()
cand = [a for a in bpy.data.actions if a.name not in src_names]
rt_act = (rt.animation_data.action if (rt.animation_data and rt.animation_data.action) else (cand[-1] if cand else None))
print("重定向动作:", rt_act.name if rt_act else None)
if rt_act:
    if tgt.animation_data is None: tgt.animation_data_create()
    tgt.animation_data.action = rt_act
    try:
        if len(rt_act.slots): tgt.animation_data.action_slot = rt_act.slots[0]
    except Exception: pass

for m in src_meshes:
    slots = [s.material.name.lower() if s.material else "" for s in m.material_slots]
    kill = [i for i, n in enumerate(slots) if any(k in n for k in ("wolf", "throne", "gem"))]
    if kill:
        bm = bmesh.new(); bm.from_mesh(m.data); bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in kill], context='FACES')
        bm.to_mesh(m.data); bm.free(); m.data.update()

def mkmat(n, c):
    m = bpy.data.materials.new(n); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = c; b.inputs["Roughness"].default_value = 0.7
    return m
mS = mkmat("MS", (0.80, 0.50, 0.40, 1)); mT = mkmat("MT", (0.42, 0.56, 0.82, 1))
for m in src_meshes: m.data.materials.clear(); m.data.materials.append(mS)
for m in tgt_meshes: m.data.materials.clear(); m.data.materials.append(mT)

# 把两套都归一到：脚底 z=0、水平居中、目标按比例放大到与源等高
def bbox(ms):
    mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
    dg = bpy.context.evaluated_depsgraph_get()
    for o in ms:
        ev = o.evaluated_get(dg)
        for v in ev.data.vertices:
            w = ev.matrix_world @ v.co
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    return mn, mx

sc.frame_set(0); bpy.context.view_layer.update()
mnS, mxS = bbox(src_meshes); mnT, mxT = bbox(tgt_meshes)
hS, hT = mxS.z - mnS.z, mxT.z - mnT.z
k = hS / hT
src.location = Vector((-(mnS.x+mxS.x)/2, -(mnS.y+mxS.y)/2, -mnS.z))
tgt.scale = (k, k, k)
tgt.location = Vector((-(mnT.x+mxT.x)/2*k, -(mnT.y+mxT.y)/2*k, -mnT.z*k))
bpy.context.view_layer.update()
print(f"源高 {hS:.1f} 目标高 {hT:.2f} k={k:.3f}")

sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = False
sc.render.resolution_x = 560; sc.render.resolution_y = 640
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.82, 0.84, 0.87, 1.0)
ld = bpy.data.lights.new("S", type='SUN'); ld.energy = 4.0
lo = bpy.data.objects.new("S", ld); sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(52), 0, math.radians(-35))
cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'; cd.ortho_scale = hS * 1.35
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam

# 角色面朝 -Y；侧视机位在 -X
center = Vector((0, 0, hS * 0.5))
cam.location = center + Vector((-1, 0, 0)) * (hS * 4)
cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()

def vis(ms, on):
    for o in ms:
        o.hide_render = not on

for f in FRAMES:
    sc.frame_set(f)
    vis(src_meshes, True); vis(tgt_meshes, False)
    sc.render.filepath = os.path.join(OUTDIR, f"CMP_{ANIM}_f{f:03d}_SRC.png")
    bpy.ops.render.render(write_still=True)
    vis(src_meshes, False); vis(tgt_meshes, True)
    sc.render.filepath = os.path.join(OUTDIR, f"CMP_{ANIM}_f{f:03d}_TGT.png")
    bpy.ops.render.render(write_still=True)
    print("frame", f, "done")
print("=== DONE ===")
