# -*- coding: utf-8 -*-
"""修 twist —— 把「手脚绕自身轴拧了 44°~91°」这个**判据原来看不见**的缺陷补上。

## 问题
`ik_37` 的主判据 `dir(父→子)` **对「绕骨轴自转」天生免疫**（子骨沿父骨轴偏移，绕该轴转它不动）。
所以「大腿 0.01°、小腿 5.77°」看起来完美，可脚掌其实**拧了 66.6°**、左手掌**拧了 90.8°**。
用户抱怨的正是这个「拧」，而旧判据报「全过」。

新加的 twist 判据里，`膝面/肘面` 其实**是冗余的**（完全由 `dir(父→子)` 决定），
真正独立的只有**末梢方向**：`dir(foot_l→ball_l)`、`dir(hand_l→middle_01_l)`
—— 它们垂直于上游骨轴，所以上游整条链的自转都会体现在它们身上。

## 修法（解析，不用扫描）
1. 在**源**与**目标**的产物动画上各取一帧，算出同一根末梢的**方向向量**
   （`d_src` 在源组件空间，`d_tgt` 在目标组件空间）。
   `大腿L 0.01°` 说明两个组件空间对腿是**对齐**的，所以可以直接比。
2. `Q = rotation_difference(d_tgt, d_src)` —— 世界系里需要施加给**上游骨**的旋转。
   误差逐帧恒定（实测 66.64/66.64/66.64）⇒ 用一帧算出来的 `Q` 对全帧都成立。
3. 把 `Q` 折进该骨的 offset。`foot_l` / `hand_l` 在 ik36 里 offset 是**单位四元数**
   ⇒ `O_new` 就是 `Q` 本身按某种约定共轭一下，**不需要和旧值相乘**，干净。

**约定未知**（offset 到底作用在自身系 / 父系 / 世界系），所以三种都算出来，
由 `Saved/retarget_cycle.json` 的 `twist.convention` 选一种，实验回路各跑一轮比数字。

配置：
```json
{ "out_dir": "/Game/.../Anims_TP_t3",
  "twist": { "convention": "self", "apply": true, "frame": 0,
             "jobs": [["foot_l","ball_l","L_Foot","L_Toe"], ...] } }
```
`convention` ∈ `self`(自身系) / `parent`(父系) / `world`(世界系)。
"""
import json
import os
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

CFG = "E:/UE/Fight/Saved/retarget_cycle.json"
RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
IK_TGT = "/Game/Character/Darius/Retarget/IK_Darius_Target"
IK_SRC = "/Game/Character/Darius/Retarget/IK_LOL_Source"
MESH_TGT = "/Game/Character/Darius/SK_Darius_GodKing"
SRC_ANIM = "/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_idle1"
E = unreal.RetargetSourceOrTarget

# (目标骨, 目标叶, 源叶)  —— 叶 = 垂直于上游骨轴的那根，才看得见 twist
DEFAULT_JOBS = [
    ["foot_l", "ball_l", "L_Toe"],
    ["foot_r", "ball_r", "R_Toe"],
    ["hand_l", "middle_01_l", "L_Middle1"],
    ["hand_r", "middle_01_r", "R_Middle1"],
]
SRC_PARENT = {"L_Toe": "L_Foot", "R_Toe": "R_Foot",
              "L_Middle1": "L_Hand", "R_Middle1": "R_Hand"}

# 累加状态：每轮算出的偏移都并进来，下一轮 `ik_48` 还原时会带上它。
# 没有这个文件，「逐骨依次修」就做不成 —— 每轮 `ik_48` 会把上一轮的成果清掉。
POSE_EXTRA = "E:/UE/Fight/Saved/pose_extra.json"


def parse_job(j):
    """支持两种写法：

    - 3 元组 `[目标骨, 目标叶, 源叶]` —— **twist 作业**（父骨就是自己）
    - 5 元组 `[目标骨, 目标父, 目标叶, 源父, 源叶]` —— **方向作业**（修某一段的朝向）
    """
    if len(j) == 3:
        tb, tl, sl = j
        return tb, tb, tl, SRC_PARENT.get(sl), sl
    if len(j) == 5:
        return j[0], j[1], j[2], j[3], j[4]
    raise ValueError("job 长度必须是 3 或 5：%r" % (j,))

cfg = {}
if os.path.isfile(CFG):
    with open(CFG, encoding="utf-8") as fh:
        cfg = json.load(fh)
tw = cfg.get("twist") or {}
conv = tw.get("convention", "self")
apply_it = bool(tw.get("apply", True))
frame = int(tw.get("frame", 0))
jobs = tw.get("jobs") or DEFAULT_JOBS
out_dir = cfg.get("out_dir") or "/Game/Character/Darius/Anims_TP_t3"
# ⚠️ 算修正量要读的是**当前姿势已经导出的那一批**，不是本轮的新目录（它还没建出来）。
#    ik_47 就是踩了这个坑才「写了 0 根骨还报存盘成功」。
pose_dir = tw.get("anim_dir") or out_dir
L("约定 = %s ；施加 = %s ；帧 = %d" % (conv, apply_it, frame))
L("读姿势用 = %s ；本轮输出 = %s" % (pose_dir, out_dir))


# ---------------------------------------------------------------- 数学
def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qconj(q):
    return (-q[0], -q[1], -q[2], q[3])


def qnorm(q):
    n = (q[0] ** 2 + q[1] ** 2 + q[2] ** 2 + q[3] ** 2) ** 0.5
    return tuple(c / n for c in q) if n > 1e-12 else (0.0, 0.0, 0.0, 1.0)


def qrot(q, v):
    x, y, z, w = q
    vx, vy, vz = v
    cx, cy, cz = y * vz - z * vy, z * vx - x * vz, x * vy - y * vx
    c2x, c2y, c2z = y * cz - z * cy, z * cx - x * cz, x * cy - y * cx
    return (vx + 2.0 * (w * cx + c2x), vy + 2.0 * (w * cy + c2y),
            vz + 2.0 * (w * cz + c2z))


def rot_diff(a, b):
    """把单位向量 a 转到 b 的**最短弧**旋转（单位四元数）。

    ⚠️ `unreal.Vector` **没有** `rotation_difference`（实测 AttributeError），
    而 `MathLibrary.find_look_at_rotation` 会引入自己的 roll 约定 ——
    那正是本次要修的 twist 自由度，不能用。所以这里直接写最短弧公式（5 行，无歧义）。
    """
    d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
    cr = (a[1] * b[2] - a[2] * b[1],
          a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0])
    if d < -0.999999:
        ax = (1.0, 0.0, 0.0) if abs(a[0]) < 0.9 else (0.0, 1.0, 0.0)
        c = (a[1] * ax[2] - a[2] * ax[1],
             a[2] * ax[0] - a[0] * ax[2],
             a[0] * ax[1] - a[1] * ax[0])
        n = (c[0] ** 2 + c[1] ** 2 + c[2] ** 2) ** 0.5
        return (c[0] / n, c[1] / n, c[2] / n, 0.0)
    return qnorm((cr[0], cr[1], cr[2], 1.0 + d))


def q_of(q):
    return unreal.Quat(q[0], q[1], q[2], q[3])


# ---------------------------------------------------------------- 骨架信息
def bone_table(mesh):
    a = actor_sub.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
    a.set_actor_label("Probe_Twist")
    c = a.get_editor_property("skeletal_mesh_component")
    try:
        c.set_skinned_asset_and_update(mesh)
    except Exception:
        c.set_skeletal_mesh(mesh)
    n = int(c.get_num_bones())
    names = [str(c.get_bone_name(i)) for i in range(n)]
    idx = {nm: i for i, nm in enumerate(names)}
    parents = []
    for nm in names:
        pi = -1
        try:
            p = c.get_parent_bone(nm)
            ps = str(p) if p is not None else ""
            if ps and ps != "None" and ps in idx:
                pi = idx[ps]
        except Exception:
            pass
        parents.append(pi)
    # ref pose 的**世界旋转**（逐级 FK）—— 约定 self/parent 要用它
    wq = [None] * n
    for i, nm in enumerate(names):
        try:
            t = c.get_ref_pose_transform(i)
            lq = (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w)
        except Exception:
            lq = (0.0, 0.0, 0.0, 1.0)
        pi = parents[i]
        wq[i] = lq if (pi < 0 or wq[pi] is None) else qmul(wq[pi], lq)
    actor_sub.destroy_actor(a)
    return names, parents, wq


def anim_local(anim, bone, frame):
    t = AL.get_bone_pose_for_frame(anim, bone, frame, False)
    return ((t.translation.x, t.translation.y, t.translation.z),
            (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
            (t.scale3d.x, t.scale3d.y, t.scale3d.z))


def anim_dir(anim, names, parents, parent_bone, child_bone, frame):
    """产物动画里 `parent_bone -> child_bone` 的方向（组件空间，纯 Python FK）。"""
    idx = {nm: i for i, nm in enumerate(names)}
    cache = {}

    def wpos(bn):
        if bn in cache:
            return cache[bn]
        i = idx[bn]
        l = anim_local(anim, bn, frame)
        pi = parents[i]
        if pi < 0:
            r = l                      # 根骨：局部即组件空间，返回**完整三元组**
        else:
            pl, pq, ps = wpos(names[pi])
            ll = l[0]
            off = qrot(pq, (ll[0] * ps[0], ll[1] * ps[1], ll[2] * ps[2]))
            r = ((pl[0] + off[0], pl[1] + off[1], pl[2] + off[2]),
                 qmul(pq, l[1]),
                 (l[2][0] * ps[0], l[2][1] * ps[1], l[2][2] * ps[2]))
        cache[bn] = r
        return r

    a, b = wpos(parent_bone)[0], wpos(child_bone)[0]
    v = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    m = (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5
    return (v[0] / m, v[1] / m, v[2] / m) if m > 1e-9 else (0.0, 0.0, 0.0)


# ---------------------------------------------------------------- 数据
mesh = eal.load_asset(MESH_TGT)
t_names, t_parents, t_wref = bone_table(mesh)
sm_src = eal.load_asset("/Game/Character/Darius/LOL_Source/SK_LOL_Darius")
s_names, s_parents, _ = bone_table(sm_src)

rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)


def get_off(bone):
    for args in ((bone, E.TARGET), (E.TARGET, bone)):
        try:
            return ctrl.get_rotation_offset_for_retarget_pose_bone(*args).rotator()
        except Exception:
            pass
    return None


def set_off(bone, q):
    for args in ((bone, E.TARGET, q), (E.TARGET, bone, q), (bone, q, E.TARGET)):
        try:
            ctrl.set_rotation_offset_for_retarget_pose_bone(*args)
            return True
        except Exception:
            continue
    return False


L("")
L("################ 逐骨计算 twist / 方向 修正")
results = {}
for job in jobs:
    tgt_bone, tgt_par, tgt_leaf, src_par, src_leaf = parse_job(job)
    if src_par is None or tgt_bone not in t_names or tgt_par not in t_names \
            or tgt_leaf not in t_names or src_leaf not in s_names or src_par not in s_names:
        LW("   %s: 骨名缺失（tgt %s/%s，src %s/%s），跳过"
           % (tgt_bone, tgt_par, tgt_leaf, src_par, src_leaf))
        continue
    ta = eal.load_asset(pose_dir + "/A_Darius_idle1")
    sa = eal.load_asset(SRC_ANIM)
    if ta is None or sa is None:
        LW("   %s: 动画加载失败" % tgt_bone)
        continue
    d_tgt = anim_dir(ta, t_names, t_parents, tgt_par, tgt_leaf, frame)
    d_src = anim_dir(sa, s_names, s_parents, src_par, src_leaf, frame)
    Q = rot_diff(d_tgt, d_src)
    qq = Q                      # rot_diff 直接返回 (x,y,z,w) 元组
    ang = 2.0 * __import__("math").degrees(
        __import__("math").acos(max(-1.0, min(1.0, abs(qq[3])))))
    cur = get_off(tgt_bone)
    curq = (cur.quaternion().x, cur.quaternion().y, cur.quaternion().z,
            cur.quaternion().w) if cur else (0.0, 0.0, 0.0, 1.0)
    L("   %-10s d_tgt=(%6.3f,%6.3f,%6.3f)  d_src=(%6.3f,%6.3f,%6.3f)  |Q|=%.2f°  现偏移=%s"
      % (tgt_bone, d_tgt[0], d_tgt[1], d_tgt[2], d_src[0], d_src[1], d_src[2], ang,
         ("(%.1f,%.1f,%.1f)" % (cur.roll, cur.pitch, cur.yaw)) if cur else "None"))

    if conv == "world":
        O = qq
    else:
        wi = t_names.index(tgt_bone)
        if conv == "self":
            W = t_wref[wi]
        else:  # parent
            pi = t_parents[wi]
            W = t_wref[pi] if pi >= 0 else (0.0, 0.0, 0.0, 1.0)
        O = qmul(qmul(qconj(W), qq), W)
    O = qnorm(O)
    results[tgt_bone] = O

L("")
L("################ 写入")
if not apply_it:
    L("   apply=false，只算不写")
else:
    n_ok = 0
    for b, O in results.items():
        ok = set_off(b, q_of(O))
        n_ok += 1 if ok else 0
        L("   %-10s -> %s" % (b, "OK" if ok else "失败"))
    L("   写入 %d / %d" % (n_ok, len(results)))

# ---------------------------------------------------------------- 累加状态
# 把本轮算出的偏移并进 `Saved/pose_extra.json`，下一轮 `ik_48` 还原时会带上它。
# ⚠️ 没有这一步，「逐骨依次修」根本做不成：每轮 `ik_48` 会把上一轮的成果清掉。
# 保存的是**读回的实际值**（而不是我算的四元数），避免读写约定万一有偏差时累积漂移。
extra = {}
if os.path.isfile(POSE_EXTRA):
    try:
        with open(POSE_EXTRA, encoding="utf-8") as fh:
            extra = json.load(fh)
    except Exception as ex:
        LW("   读 %s 失败: %s" % (POSE_EXTRA, ex))
for b in results:
    r = get_off(b)
    if r is not None:
        extra[b] = [round(r.roll, 4), round(r.pitch, 4), round(r.yaw, 4)]
with open(POSE_EXTRA, "w", encoding="utf-8") as fh:
    json.dump(extra, fh, ensure_ascii=False, indent=2, sort_keys=True)
L("   累加状态 %s 现含 %d 根骨: %s" % (POSE_EXTRA.split("/")[-1], len(extra), sorted(extra)))

L("")
L("################ 复核（读回）")
for b in results:
    r = get_off(b)
    L("   %-10s %s" % (b, ("(%.2f, %.2f, %.2f)" % (r.roll, r.pitch, r.yaw)) if r else "None"))

L("")
for p in (RTG, IK_TGT, IK_SRC):
    try:
        L("   save %-20s -> %s" % (p.split("/")[-1], eal.save_asset(p, only_if_is_dirty=False)))
    except Exception as ex:
        LW("   save %s 失败: %s" % (p, str(ex)[:120]))
LW("!! retarget pose 已改 ⇒ 必须重跑 ik_11 导出再验收。")
L("=== DONE ===")
