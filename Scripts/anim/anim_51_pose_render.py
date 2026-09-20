# -*- coding: utf-8 -*-
"""不依赖世界 tick 的按帧渲染器 —— 用 `PoseableMeshComponent` 直接写骨骼变换。

## 为什么必须绕开动画系统
`anim_40` 走的是「`set_animation` + `set_position` + 等世界 tick」。
但实测（2026-09-19）编辑器世界**只在极少数时刻 tick**：
一次 `anim_40` 里 5 秒轮询全部超时（帧间耗时 30 s ≈ 6 次超时），
于是 8 个采样点的姿势指纹**完全相同** ⇒ 拍到的还是参考姿势，图不可信。

⇒ 换一条路：**自己算姿势，自己写进组件**。
  - 姿势来源：`AnimationLibrary.get_bone_pose_for_frame(anim, bone, frame, False)`
    —— 这是**纯数据读取**，不需要世界 tick（`ik_37` 一直靠它，稳定）。
  - 写入：`UPoseableMeshComponent.set_bone_transform_by_name(..., BONE_SPACE_COMPONENT)`
    —— 直接把每根骨在**组件空间**的变换写进去，绕开 `TickPose`。
  - 渲染：`SceneCapture2D.capture_scene()` 是**显式**渲染请求，照常出图。

## 顺带解决「判据靠不靠得住」
把**源**与**目标**放进**同一个场景**、同一台相机、同一帧号一起拍，
就能一眼看出「是动画本身如此，还是重定向歪了」——这正是 `HANDOFF §4` 第 2 步要的答案。

配置：`Saved/pose_render.json`（不存在则用文件末尾的默认值）。
用法：`uv run --no-project python Scripts/ue_remote.py Scripts/anim/anim_51_pose_render.py`
"""
import json
import os
import time
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

CFG = "E:/UE/Fight/Saved/pose_render.json"

# 默认**只拍目标**。
# ⚠️ 源（LOL）网格**不能**靠「动画 FK 包围盒」归一化：它的动画局部平移（≈19564）
#    与网格自身 bind pose 的量纲不一致，按 FK 归一化会把网格拉成一块填满画面的黑墙
#    （2026-09-19 实测，看着像「模型被放大了」，其实是脚本归一化用错了基准）。
#    要拍源，得改用**网格 ref pose** 当基准 —— 那是另一件事，先不做。
DEFAULT = {
    "out": "E:/UE/Fight/Saved/Shots/PoseRender",
    "frames": [0, 20],
    "views": [["front", [0.0, -420.0, 105.0], 0.0, 90.0],
              ["q34", [-300.0, -330.0, 150.0], -8.0, 42.0]],
    "figures": [
        {"tag": "TGT", "x": 0.0,
         "mesh": "/Game/Character/Darius/SK_Darius_GodKing",
         "anim": "/Game/Character/Darius/Anims_TP_t3/A_Darius_idle1"},
    ],
}

cfg = dict(DEFAULT)
if os.path.isfile(CFG):
    try:
        with open(CFG, encoding="utf-8") as fh:
            cfg.update(json.load(fh))
        L("配置读自 %s" % CFG)
    except Exception as ex:
        LW("读配置失败，用默认: %s" % ex)
OUT = cfg["out"]
os.makedirs(OUT, exist_ok=True)

WORLD = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
CLEAN_PREFIX = ("PoseRnd_", "SceneCapture2D_Pose")


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qrot(q, v):
    x, y, z, w = q
    vx, vy, vz = v
    # v' = v + 2w(q×v) + 2(q×(q×v))
    cx = y * vz - z * vy
    cy = z * vx - x * vz
    cz = x * vy - y * vx
    c2x = y * cz - z * cy
    c2y = z * cx - x * cz
    c2z = x * cy - y * cx
    return (vx + 2.0 * (w * cx + c2x),
            vy + 2.0 * (w * cy + c2y),
            vz + 2.0 * (w * cz + c2z))


# ---------------------------------------------------------------- 清理遗留
killed = []
for a in actor_sub.get_all_level_actors():
    n, lb = a.get_name(), a.get_actor_label()
    if n.startswith(CLEAN_PREFIX) or lb.startswith(CLEAN_PREFIX):
        killed.append(lb)
        actor_sub.destroy_actor(a)
L("清理遗留: %s" % killed)

# ---------------------------------------------------------------- 渲染目标
if not eal.does_directory_exist("/Game/Temp"):
    eal.make_directory("/Game/Temp")
rt = eal.load_asset("/Game/Temp/RT_PoseRender")
if rt is None:
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RT_PoseRender", "/Game/Temp", unreal.TextureRenderTarget2D,
        unreal.TextureRenderTargetFactoryNew())
rt.set_editor_property("size_x", 1100)
rt.set_editor_property("size_y", 900)

cap_actor = actor_sub.spawn_actor_from_class(
    unreal.load_class(None, "/Script/Engine.SceneCapture2D"),
    unreal.Vector(0.0, -560.0, 110.0),
    unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0))
cap_actor.set_actor_label("SceneCapture2D_PoseRnd")
cap = cap_actor.capture_component2d
cap.set_editor_property("texture_target", rt)
cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("fov_angle", 42.0)
cap.set_editor_property("capture_every_frame", False)


# ---------------------------------------------------------------- 骨名/父索引（一次）
def bone_table(mesh):
    a = actor_sub.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
    a.set_actor_label("PoseRnd_Probe")
    c = a.get_editor_property("skeletal_mesh_component")
    try:
        c.set_skinned_asset_and_update(mesh)
    except Exception:
        c.set_skeletal_mesh(mesh)
    n = int(c.get_num_bones())
    names = [str(c.get_bone_name(i)) for i in range(n)]
    # ⚠️ `get_bone_name(i)` 收**索引**，但 `get_parent_bone(...)` 收**骨名**（FName）。
    #    传 int 会 TypeError: Failed to convert parameter 'bone_name'。
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
    actor_sub.destroy_actor(a)
    return names, parents


def make_figure(fig):
    mesh = eal.load_asset(fig["mesh"])
    if mesh is None:
        LW("  mesh 不存在: %s" % fig["mesh"])
        return None
    names, parents = bone_table(mesh)

    # ⚠️ 造 PoseableMeshComponent 的三条死路（都实测过）：
    #   1. `unreal.PoseableMeshActor` **没暴露给 Python**（dir(unreal) 里没有，
    #      `load_class(None,"/Script/Engine.PoseableMeshActor")` 返回 None）
    #   2. `ActorComponent.register_component` 没暴露
    #   3. `SkeletalMeshComponent` 根本没有 `set_bone_transform_by_name`
    #      （那是 PoseableMesh 独有的，`dir(SkeletalMeshComponent)` 里查无此名）
    # ✅ 活路：`SubobjectDataSubsystem.k2_gather_subobject_data_for_instance` +
    #    `add_new_subobject` —— 可以给**关卡实例**动态加组件，且会正确注册进世界。
    host = actor_sub.spawn_actor_from_class(unreal.Actor,
                                            unreal.Vector(fig.get("x", 0.0), 0.0, 0.0))
    host.set_actor_label("PoseRnd_%s" % fig["tag"])
    pmc = None
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    sbfl = unreal.SubobjectDataBlueprintFunctionLibrary
    if sds is not None:
        try:
            handles = sds.k2_gather_subobject_data_for_instance(host)
            L("  %s 实例子对象句柄 = %d" % (fig["tag"], len(handles)))
            if handles:
                params = unreal.AddNewSubobjectParams()
                params.set_editor_property("new_class", unreal.PoseableMeshComponent)
                params.set_editor_property("parent_handle", handles[0])
                h = sds.add_new_subobject(params)
                data = sds.k2_find_subobject_data_from_handle(h)
                for fn in ("get_associated_object", "get_object"):
                    if not hasattr(sbfl, fn):
                        continue
                    try:
                        pmc = getattr(sbfl, fn)(data)
                        break
                    except Exception:
                        continue
        except Exception as ex:
            LW("  add_new_subobject 失败: %s" % str(ex)[:180])
    if pmc is None:
        comps = host.get_components_by_class(unreal.PoseableMeshComponent)
        pmc = comps[0] if comps else None
    if pmc is None:
        LW("  %s 造不出 PoseableMeshComponent，跳过" % fig["tag"])
        actor_sub.destroy_actor(host)
        return None

    ok = False
    for fn in ("set_skinned_asset_and_update", "set_skeletal_mesh", "set_skinned_asset"):
        if not hasattr(pmc, fn):
            continue
        try:
            getattr(pmc, fn)(mesh)
            ok = True
            break
        except Exception:
            continue
    L("  figure %-4s mesh=%s bones=%d mesh_ok=%s comp=%s"
      % (fig["tag"], mesh.get_name(), len(names), ok, pmc.get_name()))
    return {"tag": fig["tag"], "mesh": mesh, "names": names, "parents": parents,
            "pmc": pmc, "host": host, "anim": eal.load_asset(fig["anim"]),
            "n": len(names)}


FIGS = []
for f in cfg["figures"]:
    r = make_figure(f)
    if r is not None:
        FIGS.append(r)

if not FIGS:
    raise SystemExit("没有可用 figure")


# ---------------------------------------------------------------- 姿势写入
def fk_pose(fg, frame):
    """从动画读局部变换 → Python 里做 FK → 返回每根骨在组件空间的 (loc, quat, scale)。"""
    anim = fg["anim"]
    if anim is None:
        return None
    local = {}
    for nm in fg["names"]:
        try:
            t = AL.get_bone_pose_for_frame(anim, nm, frame, False)
            local[nm] = ((t.translation.x, t.translation.y, t.translation.z),
                         (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
                         (t.scale3d.x, t.scale3d.y, t.scale3d.z))
        except Exception:
            local[nm] = None
    world = [None] * fg["n"]
    for i, nm in enumerate(fg["names"]):
        l = local.get(nm)
        if l is None:
            continue
        pi = fg["parents"][i]
        if pi < 0 or world[pi] is None:
            world[i] = l
        else:
            pl, pq, ps = world[pi]
            ll, lq, ls = l
            scaled = (ll[0] * ps[0], ll[1] * ps[1], ll[2] * ps[2])
            off = qrot(pq, scaled)
            world[i] = ((pl[0] + off[0], pl[1] + off[1], pl[2] + off[2]),
                        qmul(pq, lq),
                        (ls[0] * ps[0], ls[1] * ps[1], ls[2] * ps[2]))
    return world


def apply_pose(fg, world):
    """把 FK 结果逐骨写进组件。返回 (写入成功数, 引擎侧读回的探针位置)。"""
    n_ok = 0
    for i, nm in enumerate(fg["names"]):
        w = world[i]
        if w is None:
            continue
        tr = unreal.Transform()
        tr.translation = unreal.Vector(w[0][0], w[0][1], w[0][2])
        tr.rotation = unreal.Quat(w[1][0], w[1][1], w[1][2], w[1][3])
        tr.scale3d = unreal.Vector(w[2][0], w[2][1], w[2][2])
        # ⚠️ 枚举名是 `unreal.BoneSpaces.COMPONENT_SPACE` / `WORLD_SPACE`，
        #    **不是** `BONE_SPACE_COMPONENT`（实测 AttributeError）。
        for space in (unreal.BoneSpaces.COMPONENT_SPACE,
                      unreal.BoneSpaces.WORLD_SPACE):
            try:
                fg["pmc"].set_bone_transform_by_name(nm, tr, space)
                n_ok += 1
                break
            except Exception:
                continue
    # ★ 自检：从**引擎侧**读回探针骨的位置，证明姿势真的写进去了
    probe = None
    for cand in ("hand_l", "L_Hand", "lowerarm_l", "L_Elbow"):
        if cand in fg["names"]:
            probe = cand
            break
    back = None
    if probe:
        for space in (unreal.BoneSpaces.COMPONENT_SPACE,
                      unreal.BoneSpaces.WORLD_SPACE):
            try:
                t = fg["pmc"].get_bone_transform_by_name(probe, space)
                back = "%.2f,%.2f,%.2f" % (t.translation.x, t.translation.y,
                                           t.translation.z)
                break
            except Exception:
                continue
    return n_ok, back


# ---------------------------------------------------------------- 归一化尺度
# 🔴 2026-09-19 踩坑：源（LOL）与目标（2XKO）**单位制差约 1 万倍**。
#    直接同场对比时，源网格会把整个画面填满（实测源腕坐标 11773 vs 目标 1.25），
#    看起来像「模型被放大了」—— 其实只是我脚本没做归一化，**资产尺寸没问题**。
#    修法：先跑一次 FK，量出**关节包围盒高度**，把宿主 actor 缩放到统一身高，
#    再按统一身高把两尊分开放。
TARGET_HEIGHT_CM = 180.0
FIG_GAP = 130.0
L("")
L("归一化（统一身高 %.0f cm）：" % TARGET_HEIGHT_CM)
for idx, fg in enumerate(FIGS):
    w = fk_pose(fg, cfg["frames"][0])
    zs = [t[0][2] for t in (w or []) if t]
    if not zs:
        LW("  %s 量不到包围盒，按 1.0 处理" % fg["tag"])
        fg["norm"] = 1.0
        continue
    h = max(zs) - min(zs)
    s = TARGET_HEIGHT_CM / h if h > 1e-6 else 1.0
    fg["norm"] = s
    fg["fk0"] = w
    L("  %-4s 原始高 %.3f -> 缩放 %.6f" % (fg["tag"], h, s))

# 摆位：按归一化后的身高分左右站好
for idx, fg in enumerate(FIGS):
    x = (idx - (len(FIGS) - 1) / 2.0) * FIG_GAP
    fg["host"].set_actor_location(unreal.Vector(x, 0.0, 0.0), False, False)
    fg["host"].set_actor_scale3d(unreal.Vector(fg["norm"], fg["norm"], fg["norm"]))
    L("  %-4s 站位 x=%.1f  scale=%.6f" % (fg["tag"], x, fg["norm"]))

# ---------------------------------------------------------------- 逐帧渲染
n_shot = 0
sigs = {}
for f in cfg["frames"]:
    line = "  帧 %3d :" % f
    for fg in FIGS:
        world = fg.get("fk0") if f == cfg["frames"][0] else fk_pose(fg, f)
        if world is None:
            line += "  %s=<无动画>" % fg["tag"]
            continue
        n_ok, back = apply_pose(fg, world)
        line += "  %s(写入%d/%d, 引擎读回腕=%s)" % (fg["tag"], n_ok, fg["n"], back)
        sigs.setdefault(fg["tag"], []).append(back)
    L(line)
    for vname, loc, pitch, yaw in cfg["views"]:
        cap_actor.set_actor_location(unreal.Vector(*loc), False, False)
        cap_actor.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), False)
        cap.capture_scene()
        time.sleep(0.25)
        name = "f%03d_%s" % (f, vname)
        try:
            unreal.RenderingLibrary.export_render_target(WORLD, rt, OUT, name)
            n_shot += 1
        except Exception as ex:
            LW("  export 失败 %s: %s" % (name, str(ex)[:90]))

L("")
L("共导出 %d 张 -> %s" % (n_shot, OUT))
for tag, ss in sigs.items():
    uniq = len(set(x for x in ss if x))
    L("   %s 引擎读回腕位置 %d 种 / %d 帧  %s"
      % (tag, uniq, len(ss), "✅ 逐帧不同" if uniq > 1 else "!! 全同"))
L("=== DONE ===")
