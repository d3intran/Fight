import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()

DIR = "/Game/Character/Darius/Retarget"

L("=== IKRigController 里与 mesh/preview/root 有关的成员 ===")
for m in dir(unreal.IKRigController):
    if any(k in m.lower() for k in ("mesh", "preview", "skeletal", "root", "retarget")):
        L("   %s" % m)

L("")
L("=== IKRigDefinition 全部成员 ===")
ms = [m for m in dir(unreal.IKRigDefinition) if not m.startswith("_")]
L("   %s" % ", ".join(ms))

L("")
L("=== IKRigDefinitionFactory 全部成员 ===")
ms = [m for m in dir(unreal.IKRigDefinitionFactory) if not m.startswith("_")]
L("   %s" % ", ".join(ms))

L("")
L("=== 尝试创建源 IK Rig ===")
try:
    if not eal.does_directory_exist(DIR):
        ok = eal.make_directory(DIR)
        L("make_directory %s -> %s" % (DIR, ok))
except Exception as ex:
    L("make_directory 失败: %s" % ex)

name = "IK_LOL_Source"
path = DIR + "/" + name
rig = None
try:
    if eal.does_asset_exist(path):
        L("已存在，直接加载")
        rig = eal.load_asset(path)
    else:
        fac = unreal.IKRigDefinitionFactory()
        rig = at.create_asset(name, DIR, unreal.IKRigDefinition, fac)
        L("create_asset -> %s" % rig)
        if rig:
            eal.save_asset(path, only_if_is_dirty=False)
            L("saved")
except Exception as ex:
    LW("create_asset 异常: %s" % ex)

if rig is None:
    L("!! rig 为 None，尝试其它创建路径")
    for cls_name in ("IKRigBlueprintFactory", "IKRigDefinitionFactory"):
        c = getattr(unreal, cls_name, None)
        L("   %s -> %s" % (cls_name, c))
else:
    L("")
    L("rig = %s (%s)" % (rig.get_name(), rig.get_class().get_name()))
    try:
        ctrl = unreal.IKRigController.get_controller(rig)
        L("controller = %s" % ctrl)
        if ctrl:
            L("-- 与 mesh/root/chain 有关的 controller 方法 --")
            for m in dir(ctrl):
                if any(k in m.lower() for k in ("mesh", "preview", "retarget_root", "chain", "solver")):
                    L("   %s" % m)
            L("-- 当前 skeletal mesh = %s" % ctrl.get_skeletal_mesh())
            L("-- 当前 retarget chains = %s" % ctrl.get_retarget_chains())
    except Exception as ex:
        LW("get_controller 异常: %s" % ex)

L("")
L("=== 可用的 SkeletalMesh 资产 ===")
for p in ("/Game/Character/Darius/LOL_Source/SK_LOL_Darius",
          "/Game/Character/Darius/SK_Darius_GodKing"):
    o = eal.load_asset(p)
    L("   %-52s -> %s" % (p, o.get_class().get_name() if o else "NOT FOUND"))

L("=== DONE ===")
