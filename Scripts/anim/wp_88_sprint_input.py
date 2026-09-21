# -*- coding: utf-8 -*-
"""
wp_88_sprint_input.py —— 建 IA_Sprint（Boolean）+ 绑 Left Shift 到 IMC_Default

不碰蓝图图，只做输入资产层。跑完 Shift 就"有信号"了，剩下 BP 里切 MaxWalkSpeed。

跑法：
    echo dry > Saved/Attack/wp88_mode.txt
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_88_sprint_input.py
"""
import unreal

IA_PATH = "/Game/Input/Actions/IA_Sprint"
IA_NAME = "IA_Sprint"
IA_DIR = "/Game/Input/Actions"
IMC_PATH = "/Game/Input/IMC_Default"
MODE_FILE = "E:/UE/Fight/Saved/Attack/wp88_mode.txt"

# Left Shift 在 UE 里的 FKey 名
KEY_NAME = "LeftShift"


def L(s): unreal.log("[WP88] %s" % s)
def LW(s): unreal.log_warning("[WP88] %s" % s)


def mode():
    try:
        return open(MODE_FILE, encoding="utf-8").read().strip().lower()
    except Exception:
        return "dry"


def dump_imc(tag):
    imc = unreal.load_asset(IMC_PATH)
    if imc is None:
        LW("   [%s] IMC 载入失败" % tag); return
    try:
        d = imc.get_editor_property("default_key_mappings")
        arr = d.get_editor_property("mappings")
        L("   [%s] IMC 映射 %d 条:" % (tag, len(arr)))
        for m in arr:
            try:
                a = m.get_editor_property("action")
                an = a.get_name() if a else "None"
            except Exception:
                an = "?"
            try:
                k = m.get_editor_property("key")
                kn = k.get_editor_property("key_name") if k else "?"
            except Exception:
                kn = "?"
            L("      %-24s <- %s" % (an, kn))
    except Exception as ex:
        LW("   [%s] 读失败: %s" % (tag, str(ex)[:80]))


L("模式 = %s" % mode())

# ---------- 1. 建 IA_Sprint ----------
L("=" * 70)
L("=== 1. IA_Sprint ===")
ia = unreal.load_asset(IA_PATH)
if ia is not None:
    L("   已存在: %s  value_type=%s" % (IA_PATH, ia.get_editor_property("value_type")))
else:
    if mode() != "apply":
        L("   [dry] 将创建 %s" % IA_PATH)
    else:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        ia = tools.create_asset(IA_NAME, IA_DIR, unreal.InputAction,
                                unreal.InputAction_Factory())
        if ia is None:
            raise RuntimeError("创建 IA_Sprint 失败")
        ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
        ok = unreal.EditorAssetLibrary.save_loaded_asset(ia)
        L("   创建 %s  value_type=%s  save=%s" % (
            IA_PATH, ia.get_editor_property("value_type"), ok))
        ia = unreal.load_asset(IA_PATH)

# ---------- 2. IMC 绑定 ----------
L("")
L("=" * 70)
L("=== 2. IMC_Default 绑定 LeftShift ===")
dump_imc("改前")

imc = unreal.load_asset(IMC_PATH)
if imc is None:
    raise RuntimeError("载入 IMC 失败")

exist = False
try:
    d = imc.get_editor_property("default_key_mappings")
    arr = d.get_editor_property("mappings")
    for m in arr:
        try:
            a = m.get_editor_property("action")
            k = m.get_editor_property("key")
            if a and a.get_name() == IA_NAME and k and str(k.get_editor_property("key_name")) == KEY_NAME:
                exist = True
        except Exception:
            pass
except Exception as ex:
    LW("   读映射失败: %s" % str(ex)[:80])

L("   已有 IA_Sprint<-LeftShift 映射: %s" % exist)
if exist:
    L("   跳过（幂等）")
elif mode() != "apply":
    L("   [dry] 将新增一条 %s <- %s" % (IA_NAME, KEY_NAME))
else:
    ia = unreal.load_asset(IA_PATH)
    if ia is None:
        raise RuntimeError("IA_Sprint 不存在，先建")
    d = imc.get_editor_property("default_key_mappings")
    arr = d.get_editor_property("mappings")
    m = unreal.EnhancedActionKeyMapping()
    m.set_editor_property("action", ia)
    # FKey 不能直接构造（unreal.Key() 只接受零参），从已有 mapping 借一个 struct 再改 key_name
    k = None
    for x in arr:
        try:
            k = x.get_editor_property("key")
            if k is not None:
                break
        except Exception:
            pass
    if k is None:
        k = unreal.Key()
    try:
        k.set_editor_property("key_name", KEY_NAME)
        L("   借用 key struct 并改名为 %s -> %s" % (KEY_NAME, k.get_editor_property("key_name")))
    except Exception as ex:
        LW("   设置 key_name 失败: %s" % str(ex)[:80])
    m.set_editor_property("key", k)
    arr.append(m)
    d.set_editor_property("mappings", arr)
    imc.set_editor_property("default_key_mappings", d)
    ok = unreal.EditorAssetLibrary.save_loaded_asset(imc)
    L("   新增并保存: %s" % ok)

if mode() == "apply":
    dump_imc("改后")
else:
    L("")
    L("[dry] 把 Saved/Attack/wp88_mode.txt 改成 apply 后重跑。")

L("WP88 DONE")
