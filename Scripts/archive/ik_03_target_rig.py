import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()

DIR = "/Game/Character/Darius/Retarget"
TARGET_MESH = "/Game/Character/Darius/SK_Darius_GodKing"
RIG_NAME = "IK_Darius_Target"


def get_or_create_rig(name):
    path = DIR + "/" + name
    if eal.does_asset_exist(path):
        return eal.load_asset(path), path
    fac = unreal.IKRigDefinitionFactory()
    rig = at.create_asset(name, DIR, unreal.IKRigDefinition, fac)
    return rig, path


rig, path = get_or_create_rig(RIG_NAME)
L("rig = %s" % rig)

ctrl = unreal.IKRigController.get_controller(rig)
L("controller = %s" % ctrl)

mesh = eal.load_asset(TARGET_MESH)
L("mesh = %s (%s)" % (TARGET_MESH, mesh.get_class().get_name() if mesh else "NOT FOUND"))

ok = ctrl.set_skeletal_mesh(mesh)
L("set_skeletal_mesh -> %s" % ok)
L("  ctrl.get_skeletal_mesh() = %s" % ctrl.get_skeletal_mesh())


def safe(label, fn, *a):
    try:
        L("  %-24s = %s" % (label, fn(*a)))
    except Exception as ex:
        L("  %-24s : %s" % (label, ex))


L("  num_solvers = %s" % ctrl.get_num_solvers())
safe("get_root_bone(0)", ctrl.get_root_bone, 0)
safe("get_root_motion_bone(0)", ctrl.get_root_motion_bone, 0)
safe("get_retarget_root()", ctrl.get_retarget_root)
safe("get_retarget_chains()", ctrl.get_retarget_chains)

L("")
L("=== 尝试 apply_auto_generated_retarget_definition ===")
try:
    r = ctrl.apply_auto_generated_retarget_definition()
    L("  返回 = %s" % r)
except Exception as ex:
    LW("  异常: %s" % ex)

chains = ctrl.get_retarget_chains()
n = len(chains) if chains else 0
L("  当前链数 = %d" % n)
if chains:
    for c in chains:
        try:
            L("     %s" % c)
        except Exception:
            pass

eal.save_asset(path, only_if_is_dirty=False)
L("")
L("saved: %s" % path)
L("=== DONE ===")
