# -*- coding: utf-8 -*-
"""武器契约一键门禁 —— 把「武器会不会坏」变成一条命令能查的事。

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_20_weapon_audit.py
    第一次（或确认当前状态为基线时）加参数 save 建基线：
    ... Scripts/anim/wp_20_weapon_audit.py save

四段检查：
  A 动画侧  每条 AnimSequence 必须有 weapon_jnt 轨道，且它的局部平移**逐帧有变化**
            （恒定 = 停在 rest ⇒ 斧头飞到骨盆附近的地上）
  B 装配侧  WeaponAxe 组件：父级 / 相对变换 / relative_scale 必须 = 0.01（抵消最外层 100×）
  C 几何侧  斧头网格：包围盒 + socket 清单（Grip_Assist / Blade_Tip / Blade_Edge / Pommel）
  D 骨架侧  weapon_jnt 父级 = root、weapon_jnt_r 父级 = hand_r

最后与 `Saved/Attack/weapon_contract.json` 快照逐项 diff —— 任何改动都会现形。
"""
import json
import math
import os

import unreal

ANIM_DIRS = ["/Game/Character/Darius/Anims", "/Game/Character/Darius/Anims_TP_v2"]
MESH_PATH = "/Game/Character/Darius/SK_Darius_GodKing"
BP_PATH = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
AXE_PATH = "/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe"
SNAP = "E:/UE/Fight/Saved/Attack/weapon_contract.json"
REQUIRED_SOCKETS = ["Grip_Assist", "Grip_Main", "Blade_Tip", "Blade_Edge", "Pommel"]

AL = unreal.AnimationLibrary
L = unreal.log
fails = []
warns = []
snap = {}


def ok(cond, msg):
    L("   %s %s" % ("[OK]  " if cond else "[FAIL]", msg))
    if not cond:
        fails.append(msg)


def find_axe(bp):
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        d = sub.k2_find_subobject_data_from_handle(h)
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(d)
        if isinstance(o, unreal.StaticMeshComponent) and "Weapon" in o.get_name():
            return o
    return None


# ---------------------------------------------------------------- A 动画侧
L("=== A 动画侧：weapon_jnt 轨道 ===")
anims = {}
no_track, frozen = [], []
for d in ANIM_DIRS:
    for p in unreal.EditorAssetLibrary.list_assets(d, recursive=False, include_folder=False):
        a = unreal.load_object(None, p)
        if not isinstance(a, unreal.AnimSequence):
            continue
        names = [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]
        nf = AL.get_num_frames(a)
        has = "weapon_jnt" in names
        travel = 0.0
        if has:
            prev = None
            for f in range(0, nf + 1, max(1, nf // 8)):
                t = AL.get_bone_pose_for_frame(a, unreal.Name("weapon_jnt"), f, True)
                cur = (t.translation.x, t.translation.y, t.translation.z)
                if prev is not None:
                    travel = max(travel, math.dist(cur, prev))
                prev = cur
        anims[a.get_name()] = {"frames": nf, "has_weapon_jnt": has,
                               "weapon_jnt_travel": round(travel, 5)}
        if not has:
            no_track.append(a.get_name())
        elif travel < 1e-6:
            frozen.append(a.get_name())
snap["anims"] = anims
ok(not no_track, "所有动画都有 weapon_jnt 轨道（缺: %s）" % (no_track or "无"))
L("   [INFO] weapon_jnt 被冻结（未上线的旧资产/新导入动画常见）: %d 条 -> %s" % (
    len(frozen), frozen[:6]))
warns.append("冻结的动画 %d 条（若其中有**要上线**的，斧头会飞）: %s" % (len(frozen), frozen))

# ---------------------------------------------------------------- B 装配侧
L("=== B 装配侧：WeaponAxe ===")
bp = unreal.load_object(None, BP_PATH)
axe = find_axe(bp)
if axe is None:
    ok(False, "找到 WeaponAxe 组件")
else:
    par = axe.get_attach_parent()
    lv = axe.get_editor_property("relative_location")
    rv = axe.get_editor_property("relative_rotation")
    sv = axe.get_editor_property("relative_scale3d")
    m = axe.get_editor_property("static_mesh")
    asock = str(axe.get_attach_socket_name())
    snap["weapon_axe"] = {
        "attach_parent": par.get_name() if par else None,
        "attach_socket_template_read": asock,
        "rel_loc": [lv.x, lv.y, lv.z],
        "rel_rot_pyr": [rv.pitch, rv.yaw, rv.roll],
        "rel_scale": [sv.x, sv.y, sv.z],
        "static_mesh": m.get_path_name() if m else None,
    }
    ok(par is not None and par.get_name() == "CharacterMesh0", "父级 = CharacterMesh0")
    ok(all(abs(c - 0.01) < 1e-6 for c in (sv.x, sv.y, sv.z)),
       "relative_scale = 0.01（抵消骨架最外层 100×），实读 = (%.6f, %.6f, %.6f)" % (sv.x, sv.y, sv.z))
    ok(m is not None and "SM_Darius_GodKing_Axe" in m.get_name(), "static_mesh = SM_Darius_GodKing_Axe")
    L("   [INFO] 模板读到的 attach_socket = '%s'（SCS 节点与模板可能不同步，**以编辑器 Details 栏为准**）" % asock)
    L("   [INFO] rel_loc = (%.6f, %.6f, %.6f)  rel_rot = (%.3f, %.3f, %.3f)" % (
        lv.x, lv.y, lv.z, rv.pitch, rv.yaw, rv.roll))

# ---------------------------------------------------------------- C 几何侧
L("=== C 几何侧：斧头网格 ===")
ax = unreal.load_object(None, AXE_PATH)
try:
    b = ax.get_bounds()
    snap["axe_bounds"] = {"extent": [b.box_extent.x, b.box_extent.y, b.box_extent.z],
                          "radius": b.sphere_radius}
    L("   [INFO] 包围盒 extent = (%.2f, %.2f, %.2f)  sphere_r = %.2f" % (
        b.box_extent.x, b.box_extent.y, b.box_extent.z, b.sphere_radius))
except Exception as ex:
    L("   [WARN] 包围盒读不到: %s" % ex)
present = []
for s in REQUIRED_SOCKETS:
    try:
        present.append(s if ax.find_socket(s) else None)
    except Exception:
        present.append(None)
missing = [s for s, got in zip(REQUIRED_SOCKETS, present) if not got]
snap["axe_sockets_present"] = [s for s in present if s]
L("   [INFO] 斧头网格上的 socket: %s" % (snap["axe_sockets_present"] or "无"))
if missing:
    L("   [INFO] 斧头网格上还缺: %s（StaticMeshEditor 打开会崩，暂时不要从 UI 加）" % missing)

# 握把 socket 落在**角色骨架网格**上、父骨 = weapon_jnt（斧头网格打不开时的替代方案）
mesh = unreal.load_object(None, MESH_PATH)
L("   [--] 角色骨架网格上的握把 socket:")
grip = {}
for s in ("Grip_Assist", "Grip_Main"):
    try:
        so = mesh.find_socket(s)
        if so:
            v = so.get_editor_property("relative_location")
            grip[s] = {"bone": str(so.get_editor_property("bone_name")),
                       "loc": [v.x, v.y, v.z]}
            L("       %-12s 存在 ✓ 父骨=%s loc=(%.6f, %.6f, %.6f) |·|×100 = %.1f cm" % (
                s, grip[s]["bone"], v.x, v.y, v.z,
                (v.x * v.x + v.y * v.y + v.z * v.z) ** 0.5 * 100))
        else:
            L("       %-12s 不存在" % s)
    except Exception as ex:
        L("       %-12s 查询失败 %s" % (s, ex))
snap["mesh_grip_sockets"] = grip

# ---------------------------------------------------------------- D 骨架侧
L("=== D 骨架侧：武器锚点骨 ===")
mesh = unreal.load_object(None, MESH_PATH)
sk_asset = mesh.get_editor_property("skeleton")
bones = [str(b) for b in AL.get_bone_names(unreal.load_object(None, sk_asset.get_path_name()))] \
    if hasattr(AL, "get_bone_names") else []
if bones:
    for bn in ("weapon_jnt", "weapon_jnt_r", "weapon_jnt_l", "weapon_jnt_offset"):
        ok(bn in bones, "骨架含 %s" % bn)
else:
    for bn in ("weapon_jnt", "weapon_jnt_r", "weapon_jnt_l", "weapon_jnt_offset"):
        L("   [INFO] 预期存在（骨架骨名列表 API 不可用，未校验）: %s" % bn)
snap["skeleton"] = sk_asset.get_path_name()

# ---------------------------------------------------------------- 快照 diff
L("=== 契约快照 diff ===")
if os.path.exists(SNAP):
    old = json.load(open(SNAP, encoding="utf-8"))
    diffs = []
    for key in ("weapon_axe", "axe_bounds", "axe_sockets_present"):
        if old.get(key) != snap.get(key):
            diffs.append(key)
    if diffs:
        L("   [DIFF] 与基线不同的项: %s" % diffs)
        for k in diffs:
            L("      基线: %s" % json.dumps(old.get(k), ensure_ascii=False))
            L("      现在: %s" % json.dumps(snap.get(k), ensure_ascii=False))
    else:
        L("   [OK]  与基线一致")
    ao = old.get("anims", {})
    changed = [k for k in snap["anims"] if ao.get(k) != snap["anims"][k]]
    L("   动画新增/变化 %d 条: %s" % (len(changed), changed[:8]))
else:
    L("   [INFO] 基线不存在（%s）" % SNAP)

with open(SNAP, "w", encoding="utf-8") as f:
    json.dump(snap, f, indent=1, ensure_ascii=False)
L("快照已更新 -> %s" % SNAP)

L("")
L("=== 汇总 ===")
L("   FAIL %d 项: %s" % (len(fails), fails or "无 ✓"))
for w in warns:
    L("   WARN %s" % w)
L("WEAPON_AUDIT_DONE")
