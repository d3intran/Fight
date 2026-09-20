# -*- coding: utf-8 -*-
"""拍重定向产物：把角色摆在训练场里，逐姿势离屏渲染，供肉眼判断手脚朝向是否正常。

复用 `Scripts/anim/axe_14_scene_capture_char.py` 的成熟做法（SceneCapture2D + export_render_target，
capture_source 用 SCS_FINAL_COLOR_LDR ⇒ 直出就能看，无需 ffmpeg 转码）。

⚠️ 用裸 `SkeletalMeshActor` 而不是 `BP_DariusCharacter`：
   BP 上挂着 AnimBlueprint，会覆盖 `set_animation` 的结果。

🔴 2026-09-19 修掉的两个 bug（都是「静默假帧」，害我白看了一轮图）：
  1. **组件在编辑器里不求值动画**：spawn 出来的 SkeletalMeshComponent
     `update_animation_in_editor = False` ⇒ `set_position()` 设了也不生效，
     姿势永远停在第 1 帧。**必须先 `set_update_animation_in_editor(True)`。**
     这不是「采集冻结」，是**动画本身没动** —— 症状一模一样（md5 全同），极难区分。
  2. **清理前缀写错**：spawn 出来的 actor `get_name()` 是 `SkeletalMeshActor_1`，
     原来写的 `"SkelMeshAct_"` 匹配不上 ⇒ 每跑一次残留一个 actor。
     现在统一用 `SkeletalMeshAct`（同时覆盖 name 与 label）。

本脚本自带**假帧自检**：每换一帧读一次组件实际骨骼变换，全同就报 `!! 假帧`。
拍完必须销毁临时 actor，关卡基线只有 7 个。
"""
import unreal
import os
import time

L = unreal.log
LW = unreal.log_warning

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

if les.is_in_play_in_editor():
    LW("!! PIE 运行中，先退出")
    raise SystemExit(1)

MESH = "/Game/Character/Darius/SK_Darius_GodKing"
CLEAN_PREFIX = ("AnimChk_", "Probe_", "SceneCapture2D_", "SkeletalMeshAct")

# 对比拍摄：同一相机、同一帧号，**只换 retarget pose 的产物**。
#   t3  = 写回 `ik36` 偏移表 ⇒ 目前最好的姿势（腿 0.01°，上半身 9 段超门限）
#   z02 = 纯零基线（未标定）⇒ 13 段全超门限
# 两张图放一起看，就能直接判断「标定到底改了什么、剩下的错在哪」。
SHOTS = [
    ("t3_idle1",  "/Game/Character/Darius/Anims_TP_t3/A_Darius_idle1",  [0, 20, 40]),
    ("z02_idle1", "/Game/Character/Darius/Anims_TP_z02/A_Darius_idle1", [0, 20, 40]),
    ("t3_run",    "/Game/Character/Darius/Anims_TP_t3/A_Darius_run",    [0, 9, 18]),
]

OUT = "E:/UE/Fight/Saved/Shots/AnimCheck"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- 0. 探明 enum 名
SPACES = []
for nm in ("RelativeTransformSpace", "TransformSpace", "BoneTransformSpace"):
    e = getattr(unreal, nm, None)
    if e is None:
        continue
    for v in ("RTS_Component", "RTS_COMPONENT", "Component"):
        if hasattr(e, v):
            SPACES.append(getattr(e, v))
            break
L("可用的 transform space = %s" % (SPACES or "无（改用资产侧自检）"))

# ---------------------------------------------------------------- 1. 清理遗留
killed = []
for a in actor_sub.get_all_level_actors():
    n, lb = a.get_name(), a.get_actor_label()
    if n.startswith(CLEAN_PREFIX) or lb.startswith(CLEAN_PREFIX):
        killed.append("%s/%s" % (n, lb))
        actor_sub.destroy_actor(a)
L("清理遗留: %s" % killed)

# ---------------------------------------------------------------- 2. 造渲染目标
if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Temp"):
    unreal.EditorAssetLibrary.make_directory("/Game/Temp")
rt = unreal.load_asset("/Game/Temp/RT_AnimCheck")
if rt is None:
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RT_AnimCheck", "/Game/Temp", unreal.TextureRenderTarget2D,
        unreal.TextureRenderTargetFactoryNew())
rt.set_editor_property("size_x", 900)
rt.set_editor_property("size_y", 900)

# ---------------------------------------------------------------- 3. 角色
sm = unreal.load_asset(MESH)
L("mesh = %s" % (sm.get_name() if sm else "NOT FOUND"))
if sm is None:
    raise SystemExit(1)
actor = actor_sub.spawn_actor_from_class(unreal.SkeletalMeshActor,
                                         unreal.Vector(0.0, 0.0, 0.0),
                                         unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
actor.set_actor_label("AnimChk_Darius")
comp = actor.get_editor_property("skeletal_mesh_component")
try:
    comp.set_skinned_asset_and_update(sm)
except Exception:
    comp.set_skeletal_mesh(sm)

# 🔴 关键：打开编辑器内动画求值，否则 set_position 不生效（姿势恒为第 1 帧）
turned = False
for fn_name in ("set_update_animation_in_editor",):
    fn = getattr(comp, fn_name, None)
    if fn is None:
        continue
    try:
        fn(True)
        turned = True
        L("  %s(True) OK" % fn_name)
    except Exception as ex:
        LW("  %s(True) 失败: %s" % (fn_name, str(ex)[:100]))
if not turned:
    for p in ("update_animation_in_editor", "b_update_animation_in_editor"):
        try:
            comp.set_editor_property(p, True)
            turned = True
            L("  set_editor_property(%s, True) OK" % p)
        except Exception:
            pass
try:
    L("  回读 update_animation_in_editor = %s"
      % comp.get_editor_property("update_animation_in_editor"))
except Exception as ex:
    LW("  回读失败: %s" % str(ex)[:80])
if not turned:
    LW("!! 未能打开编辑器内动画求值 —— 大概率会拍到假帧")

try:
    comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
except Exception as ex:
    LW("set_animation_mode: %s" % str(ex)[:90])
L("角色已放置: %s / label=%s" % (actor.get_name(), actor.get_actor_label()))

# ---------------------------------------------------------------- 4. 相机
sc_class = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
cap_actor = actor_sub.spawn_actor_from_class(sc_class, unreal.Vector(0.0, -450.0, 110.0),
                                             unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0))
cap_actor.set_actor_label("SceneCapture2D_AnimChk")
cap = cap_actor.capture_component2d
cap.set_editor_property("texture_target", rt)
cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("fov_angle", 40.0)
cap.set_editor_property("capture_every_frame", False)

VIEWS = [
    ("front", (0.0, -450.0, 110.0), 0.0, 90.0),
    ("q34",   (-320.0, -330.0, 130.0), -6.0, 46.0),
]

PROBE_BONES = ["thigh_l", "lowerarm_l", "hand_l", "foot_l"]


def pose_fingerprint():
    """读组件实际求值出的骨骼变换；全同 ⇒ 假帧。"""
    vals = []
    for b in PROBE_BONES:
        got = None
        for sp in SPACES:
            try:
                tr = comp.get_bone_transform(b, sp)
                r = tr.rotation
                got = "%.4f,%.4f,%.4f,%.4f" % (r.x, r.y, r.z, r.w)
                break
            except Exception:
                continue
        vals.append(got or "?")
    return "|".join(vals)


# ---------------------------------------------------------------- 4.5 等世界真的推进一帧
# 🔴 2026-09-19 实测：编辑器世界**不是连续 tick 的**（1.2 s 采样里 Δ=0，但两次运行之间
#    game_time 从 269.59 走到 280.32）。固定 `sleep(0.5)` 因此会拍到**没求值过的假帧**。
#    改成「**轮询等世界时间前进**」，只要它偶尔 tick，就能拿到真帧。
WORLD = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
_tick_stat = {"waits": 0, "timeouts": 0}


def world_time():
    return unreal.SystemLibrary.get_game_time_in_seconds(WORLD)


def wait_tick(timeout=5.0):
    """等世界时间前进；返回推进量（0.0 = 超时没等到）。"""
    t0 = world_time()
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(0.05)
        t1 = world_time()
        if t1 > t0 + 1e-9:
            _tick_stat["waits"] += 1
            return t1 - t0
    _tick_stat["timeouts"] += 1
    return 0.0


L("")
L("等 tick 自检：")
d = wait_tick(5.0)
L("   一次等待拿到 Δ=%.4f s  %s" % (d, "OK" if d > 0 else "!! 5 秒内世界没动"))

# ---------------------------------------------------------------- 5. 逐姿势渲染
n_shot = 0
fingerprints = {}
for tag, anim_path, frames in SHOTS:
    anim = unreal.load_asset(anim_path)
    if anim is None:
        LW("  %s 加载失败" % anim_path)
        continue
    comp.set_animation(anim)
    try:
        comp.play(False)
    except Exception:
        pass
    for f in frames:
        t = f / 30.0
        try:
            comp.set_position(t, False)
        except Exception as ex:
            LW("  set_position(%s) 失败: %s" % (t, str(ex)[:80]))
        try:
            les.editor_invalidate_viewports()
        except Exception:
            pass
        wait_tick()
        fp = pose_fingerprint()
        fingerprints["%s_f%02d" % (tag, f)] = fp
        for vname, loc, pitch, yaw in VIEWS:
            cap_actor.set_actor_location(unreal.Vector(*loc), False, False)
            cap_actor.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), False)
            wait_tick()
            cap.capture_scene()
            wait_tick()
            name = "%s_f%02d_%s" % (tag, f, vname)
            try:
                unreal.RenderingLibrary.export_render_target(
                    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),
                    rt, OUT, name)
                n_shot += 1
            except Exception as ex:
                LW("  export 失败 %s: %s" % (name, str(ex)[:90]))
        L("  拍完 %s 第 %d 帧  姿势指纹=%s" % (tag, f, fp))

L("")
L("共导出 %d 张 -> %s   （等 tick：成功 %d / 超时 %d）"
  % (n_shot, OUT, _tick_stat["waits"], _tick_stat["timeouts"]))

# ---------------------------------------------------------------- 5.5 假帧自检
uniq = set(v for v in fingerprints.values() if v != "?")
L("")
if "?" in fingerprints.values():
    LW("!! 读不到骨骼变换，本脚本无法自检假帧 —— 请用 md5 手动核对")
elif len(uniq) <= 1:
    LW("!! 假帧：%d 个采样点姿势指纹全同 ⇒ 动画没在动，图不可信" % len(fingerprints))
else:
    L("假帧自检通过：%d 个采样点有 %d 种不同姿势" % (len(fingerprints), len(uniq)))

# ---------------------------------------------------------------- 6. 清理临时 actor
killed2 = []
for a in actor_sub.get_all_level_actors():
    n, lb = a.get_name(), a.get_actor_label()
    if n.startswith(CLEAN_PREFIX) or lb.startswith(CLEAN_PREFIX):
        killed2.append("%s/%s" % (n, lb))
        actor_sub.destroy_actor(a)
L("已销毁: %s" % killed2)
L("剩余 actor: %s" % sorted([a.get_actor_label() for a in actor_sub.get_all_level_actors()]))
L("=== DONE ===")
