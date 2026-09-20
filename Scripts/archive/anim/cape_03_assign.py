import unreal

SM = "/Game/Character/Darius/SK_Darius_GodKing"
PA = "/Game/Character/Darius/SK_Darius_GodKing_Physics"

unreal.log("签名: %s" % unreal.SkeletalMeshEditorSubsystem.assign_physics_asset.__doc__)
unreal.log("签名: %s" % unreal.SkeletalMeshEditorSubsystem.is_physics_asset_compatible.__doc__)


def LO(p):
    try:
        return unreal.load_object(None, p)
    except Exception as ex:
        unreal.log("   load ERR %s" % str(ex)[:70])
        return None


sk = LO(SM)
pa = LO(PA)
unreal.log("mesh=%s  pa=%s" % (sk, pa))
if not sk or not pa:
    raise SystemExit(1)

sub = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
try:
    unreal.log("兼容性 = %s" % sub.is_physics_asset_compatible(sk, pa))
except Exception as ex:
    unreal.log("兼容性 ERR %s" % str(ex)[:80])

try:
    cur = sk.get_editor_property("physics_asset")
    unreal.log("改前 physics_asset = %s" % cur)
except Exception as ex:
    unreal.log("读 physics_asset ERR %s" % str(ex)[:70])

ok = False
try:
    ok = sub.assign_physics_asset(sk, pa)
except Exception as ex:
    unreal.log("assign ERR %s" % str(ex)[:120])
unreal.log("assign_physics_asset -> %s" % ok)

try:
    unreal.log("改后 physics_asset = %s" % sk.get_editor_property("physics_asset"))
except Exception as ex:
    unreal.log("读回 ERR %s" % str(ex)[:70])

saved = False
try:
    saved = unreal.EditorAssetLibrary.save_asset(SM)
except Exception as ex:
    unreal.log("save ERR %s" % str(ex)[:100])
unreal.log("save_asset -> %s" % saved)

unreal.log("### 复核（重新读对象）")
sk2 = LO(SM)
try:
    unreal.log("   physics_asset = %s" % sk2.get_editor_property("physics_asset"))
except Exception as ex:
    unreal.log("   ERR %s" % str(ex)[:70])
unreal.log("### DONE")
