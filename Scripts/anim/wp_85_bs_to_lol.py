# -*- coding: utf-8 -*-
"""
wp_85_bs_to_lol.py —— 把 BS_Darius_Locomotion 的内容换成 LoL 重定向动画

现状：BS 是 2D (Speed 0~220 × Direction -180~180)，13 个样本，用的是 Mixamo 线的
      A_Darius_AxeIdle_Layered / A_Darius_AxeWalk_Layered。
目标：Speed 0~440，9 个样本 →
      0   → A_Darius_idle1
      220 → A_Darius_run
      440 → A_Darius_run_fast
      每个速度在 Direction = -180 / 0 / +180 各放一份，保证 2D 凸包覆盖整个域。

不动 ABP —— ABP 里那个 BlendSpacePlayer 引用的还是同一个资产对象，内容换了就生效。
原 Mixamo 版会先备份成 BS_Darius_Locomotion_M1_Mixamo。

跑法：
    echo dry > Saved/Attack/wp85_mode.txt
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_85_bs_to_lol.py
    echo apply > Saved/Attack/wp85_mode.txt
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_85_bs_to_lol.py
"""
import json
import os
import unreal

BS = "/Game/Character/Darius/Anims/BS_Darius_Locomotion"
BACKUP = "/Game/Character/Darius/Anims/BS_Darius_Locomotion_M1_Mixamo"
MODE_FILE = "E:/UE/Fight/Saved/Attack/wp85_mode.txt"

DESIGN = [
    # (speed, direction, asset)
    (0.0,   -180.0, "A_Darius_idle1"),
    (0.0,      0.0, "A_Darius_idle1"),
    (0.0,    180.0, "A_Darius_idle1"),
    (220.0, -180.0, "A_Darius_run"),
    (220.0,    0.0, "A_Darius_run"),
    (220.0,  180.0, "A_Darius_run"),
    (440.0, -180.0, "A_Darius_run_fast"),
    (440.0,    0.0, "A_Darius_run_fast"),
    (440.0,  180.0, "A_Darius_run_fast"),
]
ANIM_DIR = "/Game/Character/Darius/Animations/LOL_Retarget"
SPEED_MAX = 440.0


def L(s): unreal.log("[WP85] %s" % s)
def LW(s): unreal.log_warning("[WP85] %s" % s)


def mode():
    try:
        return open(MODE_FILE, encoding="utf-8").read().strip().lower()
    except Exception:
        return "dry"


def dump(bs, tag):
    """打印当前轴与样本"""
    try:
        bps = bs.get_editor_property("blend_parameters")
        axes = []
        for i in range(min(2, len(bps))):
            b = bps[i]
            axes.append("%s[%.1f,%.1f]" % (b.get_editor_property("display_name"),
                                           b.get_editor_property("min"),
                                           b.get_editor_property("max")))
        L("   [%s] 轴: %s" % (tag, "  ".join(axes)))
    except Exception as ex:
        LW("   [%s] 读轴失败: %s" % (tag, str(ex)[:60]))
    try:
        sd = bs.get_editor_property("sample_data")
        L("   [%s] 样本 x%d:" % (tag, len(sd)))
        seen = {}
        for s in sd:
            a = s.get_editor_property("animation")
            v = s.get_editor_property("sample_value")
            nm = a.get_name() if a else "None"
            seen.setdefault(nm, []).append("(%.0f,%.0f)" % (v.x, v.y))
        for nm, pts in seen.items():
            L("      %-32s %s" % (nm, " ".join(sorted(pts))))
    except Exception as ex:
        LW("   [%s] 读样本失败: %s" % (tag, str(ex)[:60]))


# ---------- 0. 载入 ----------
bs = unreal.load_asset(BS)
if bs is None:
    raise RuntimeError("载入 BS 失败: %s" % BS)
L("模式 = %s" % mode())
L("BS = %s" % bs.get_name())
dump(bs, "改前")

# ---------- 1. 备份 ----------
if unreal.EditorAssetLibrary.does_asset_exist(BACKUP):
    L("备份已存在，跳过: %s" % BACKUP)
else:
    if mode() == "apply":
        got = unreal.EditorAssetLibrary.duplicate_asset(BS, BACKUP)
        L("备份 -> %s  (%s)" % (BACKUP, bool(got)))
        if got:
            unreal.EditorAssetLibrary.save_asset(BACKUP)
    else:
        L("[dry] 将备份 -> %s" % BACKUP)

# ---------- 2. 解析动画 ----------
samples = []
anims = {}
missing = []
for spd, dr, nm in DESIGN:
    p = "%s/%s" % (ANIM_DIR, nm)
    if p not in anims:
        a = unreal.load_asset(p)
        if a is None:
            missing.append(p)
        anims[p] = a
    a = anims[p]
    if a is None:
        continue
    samples.append((spd, dr, a, nm))
if missing:
    LW("缺失动画: %s" % missing)
L("可用样本 %d / %d" % (len(samples), len(DESIGN)))

# ---------- 3. 组装新轴与新样本 ----------
new_axes = list(bs.get_editor_property("blend_parameters"))
b0 = new_axes[0]
old_max = b0.get_editor_property("max")
b0.set_editor_property("min", 0.0)
b0.set_editor_property("max", SPEED_MAX)
b0.set_editor_property("display_name", "Speed")
b0.set_editor_property("grid_num", 8)
new_axes[0] = b0
L("轴0 Speed: %.0f -> %.0f" % (old_max, SPEED_MAX))

new_sd = []
for spd, dr, a, nm in samples:
    s = unreal.BlendSample()
    s.set_editor_property("animation", a)
    s.set_editor_property("sample_value", unreal.Vector(spd, dr, 0.0))
    s.set_editor_property("rate_scale", 1.0)
    new_sd.append(s)
L("新样本 %d 个" % len(new_sd))

# ---------- 4. 写入 ----------
if mode() != "apply":
    L("")
    L("[dry] 将写入:")
    for spd, dr, a, nm in samples:
        L("    Speed=%-5.0f Dir=%-6.0f -> %s" % (spd, dr, nm))
    L("")
    L("把 Saved/Attack/wp85_mode.txt 改成 apply 后重跑。")
else:
    bs.set_editor_property("blend_parameters", new_axes)
    bs.set_editor_property("sample_data", new_sd)
    ok = unreal.EditorAssetLibrary.save_loaded_asset(bs)
    L("写入并保存: %s" % ok)
    bs2 = unreal.load_asset(BS)
    dump(bs2, "改后")

L("WP85 DONE")
