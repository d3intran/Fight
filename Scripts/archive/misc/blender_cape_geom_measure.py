"""
Blender 无头：披风物理改造的几何依据测量。

产出三组数：
  1) 穿模量化：绑定姿势下披风顶点到身体网格最近点的距离分布（多少顶点已经陷在身体里）
  2) 锚点候选：cape_chain_01_* 的父骨，以及父骨在 armature 空间的坐标
  3) 每个「锚点骨/身体骨」→ 骨骼局部空间的胶囊参数（center/rotation/radius/length），
     直接可填进 PhysicsAssetToolset 的 SetCapsule
用法: blender -b -P 本文件 -- <FBX>
"""
import bpy
import math
import sys
import numpy as np
from collections import defaultdict
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = argv[0]
BODY_MESHES = ("BodyUpper", "BodyLower", "Head")
CAPE_MESH = "Cape"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = [o for o in bpy.data.objects if o.type == 'MESH']

print("### 网格清单: %s" % [(m.name, [s.material.name if s.material else None for s in m.material_slots])
                            for m in meshes])


def mesh_mats(me):
    return " ".join(s.material.name for s in me.material_slots if s.material)


def world_verts(pred):
    """按材质槽名谓词取网格，返回 armature 空间顶点列表 + 命中的网格名"""
    pts, objs = [], []
    for me in meshes:
        mm = mesh_mats(me)
        if any(k.lower() in mm.lower() for k in pred):
            objs.append("%s[%s]" % (me.name, mm))
            dg = arm.matrix_world.inverted() @ me.matrix_world   # Blender 行向量：先 mesh→world，再 world→armature
            for v in me.data.vertices:
                pts.append(dg @ v.co)
    return pts, objs


def to_np(P):
    return np.asarray([[p.x, p.y, p.z] for p in P], dtype=np.float32)


def nn_dist(src, dst, chunk=128):
    """src 每点到 dst 点云的最小距离（m）。分块暴力，绕开 Blender 5.2 KDTree 的异常行为。"""
    out = np.empty(len(src), dtype=np.float32)
    for s in range(0, len(src), chunk):
        e = min(s + chunk, len(src))
        d2 = ((src[s:e, None, :] - dst[None, :, :]) ** 2).sum(axis=2)
        out[s:e] = np.sqrt(d2.min(axis=1))
    return out


# ---------------------------------------------------------------- 1 穿模量化
cape_pts, cape_objs = world_verts([CAPE_MESH])
body_pts, body_objs = world_verts(BODY_MESHES)
print("### 披风网格=%s 顶点=%d" % (cape_objs, len(cape_pts)))
print("### 身体网格=%s 顶点=%d" % (body_objs, len(body_pts)))

CA = to_np(cape_pts)
BO = to_np(body_pts)
print("### bbox 披风 x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
    CA[:, 0].min(), CA[:, 0].max(), CA[:, 1].min(), CA[:, 1].max(), CA[:, 2].min(), CA[:, 2].max()))
print("### bbox 身体 x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
    BO[:, 0].min(), BO[:, 0].max(), BO[:, 1].min(), BO[:, 1].max(), BO[:, 2].min(), BO[:, 2].max()))

d = (nn_dist(CA, BO) * 100.0).tolist()      # cm
ds = sorted(d)
n = len(ds)


def pct(q):
    return ds[min(n - 1, int(q * n))]


print("### 披风顶点到身体顶点云(ply 近似表面)的最近距离 (cm): "
      "p01=%.1f p10=%.1f 中位=%.1f p90=%.1f p99=%.1f max=%.1f" % (
          pct(0.01), pct(0.10), pct(0.50), pct(0.90), pct(0.99), ds[-1]))
for thr in (0.5, 1.0, 2.0, 3.0, 5.0, 10.0):
    c = sum(1 for x in d if x <= thr)
    print("###   距离 <= %.1f cm 的披风顶点: %d / %d (%.1f%%)" % (thr, c, n, 100.0 * c / n))

# ---------------------------------------------------------------- 2 骨骼信息
pbone = {b.name: b for b in arm.data.bones}
print("### 披风链根的骨架父骨:")
for h in ("cape_chain_01_l", "cape_chain_01_m", "cape_chain_01_r"):
    b = pbone.get(h)
    par = b.parent.name if b and b.parent else None
    ch = [c.name for c in b.children] if b else []
    print("   %-16s parent=%-12s children=%s len=%.4f" % (h, par, ch, b.length if b else -1))


def bone_local(bn, p_arm):
    """把 armature 空间点变换到该骨的局部空间（UE 的 body-local 约定：以骨为原点、骨轴朝向）"""
    b = pbone[bn]
    M = arm.data.bones[bn].matrix_local
    return M.inverted() @ p_arm


print("### 关键骨（armature 空间, m）与到披风 sheet 的距离")
ANCH = [x for x in ("pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
                    "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r",
                    "thigh_l", "thigh_r", "calf_l", "calf_r") if x in pbone]
cape_arr = CA


def cape_nearest(p):
    v = np.asarray([p.x, p.y, p.z], dtype=np.float32)
    return float(np.sqrt(((cape_arr - v) ** 2).sum(axis=1)).min())
for bn in ANCH:
    b = pbone[bn]
    head = arm.matrix_world.inverted() @ (arm.matrix_world @ b.head_local)
    # 该骨方向上的身体半径：取骨轴中点附近 body 顶点的最大横向距离
    axis = (b.tail_local - b.head_local).normalized()
    mid = b.head_local + axis * (b.length * 0.5)
    near = [p for p in body_pts if (p - mid).length < 0.35]
    lat = [(p - mid) - ((p - mid).dot(axis)) * axis for p in near]
    rmax = max((v.length for v in lat), default=0.0) * 100
    # 前/后（沿世界 Y）与上（Z）的包体厚度，用来判断该用整圆柱还是背板
    yp = max((p.y - mid.y for p in near), default=0.0) * 100
    yn = min((p.y - mid.y for p in near), default=0.0) * 100
    cp = [p for p in cape_pts if (p - mid).length < 0.60]
    cy = (sum(p.y - mid.y for p in cp) / len(cp) * 100) if cp else 0.0
    dist = cape_nearest(mid)
    print("   %-12s len=%.3f 身体横半径=%.1fcm 体+Y=%.1f 体-Y=%.1f 披风均偏移Y=%+.1fcm 到披风最近=%.1fcm" % (
        bn, b.length, rmax, yp, yn, cy, dist * 100))

# ---------------------------------------------------------------- 2b SetCapsule 参数
print("### 可直接填进 SetCapsule 的 bone-local 参数（单位同现有 0.505 那套 = Blender 米）")
for bn in ANCH:
    if bn not in pbone:
        continue
    b = pbone[bn]
    axis = (b.tail_local - b.head_local).normalized()
    L = b.length
    mid = b.head_local + axis * (L * 0.5)
    near = [p for p in body_pts if (p - mid).length < 0.35]
    lat = [(p - mid) - ((p - mid).dot(axis)) * axis for p in near]
    rmax = max((v.length for v in lat), default=0.0)
    M = b.matrix_local
    lc = M.inverted() @ mid                      # 骨局部空间的胶囊中心
    la = (M.to_3x3().inverted() @ axis).normalized()   # 骨局部空间里的骨轴方向
    # SetCapsule: 长轴 = 施加 Rotation 后的局部 Z；用 (roll,pitch,yaw) 的欧拉把 Z 转到 la
    q = la.to_track_quat('Z', 'Y')
    eu = q.to_euler()
    print("   %-12s center=(x=%.4f,y=%.4f,z=%.4f) rot=(roll=%.2f,pitch=%.2f,yaw=%.2f) "
          "radius=%.4f length=%.4f  (骨轴局部=%s)" % (
              bn, lc.x, lc.y, lc.z,
              math.degrees(eu.x), math.degrees(eu.y), math.degrees(eu.z),
              rmax, max(0.0, L - 2 * rmax), [round(v, 3) for v in la]))

# ---------------------------------------------------------------- 3 披风链局部形状
print("### 披风链节：bone-local 空间里披风顶点的横向分布（决定球/胶囊半径）")
for side in ("l", "m", "r"):
    for i in range(1, 10):
        bn = "cape_chain_%02d_%s" % (i, side)
        if bn not in pbone:
            continue
        b = pbone[bn]
        axis = (b.tail_local - b.head_local).normalized()
        # 只看落在该节覆盖范围内的顶点（head->tail 之间）
        seg = []
        for p in cape_pts:
            t = (p - b.head_local).dot(axis) / max(b.length, 1e-6)
            if -0.15 <= t <= 1.15:
                v = p - (b.head_local + axis * t * b.length)
                seg.append((t, v.length))
        if not seg:
            print("   %-18s 无覆盖顶点" % bn)
            continue
        rs = np.sort(np.asarray([x[1] for x in seg], dtype=np.float32))
        m = len(rs)
        p10, p25, p50, p90 = (float(rs[int(m * q)]) for q in (0.10, 0.25, 0.50, 0.90))
        b2 = pbone[bn]
        M = b2.matrix_local
        axis2 = (b2.tail_local - b2.head_local).normalized()
        lc = M.inverted() @ (b2.head_local + axis2 * (b2.length * 0.5))
        # 披风是薄片：p90 是「横向铺开宽度」不是厚度，碰撞半径要用贴近骨轴的 p25
        print("   %-18s len=%.3f 覆盖=%-5d 距骨轴 p10=%.1f p25=%.1f p50=%.1f p90=%.1f cm "
              "=> SetSphere center=(%.4f,%.4f,%.4f) radius=%.4f" % (
                  bn, b.length, m, p10 * 100, p25 * 100, p50 * 100, p90 * 100,
                  lc.x, lc.y, lc.z, max(0.02, p25)))
print("### DONE")
