import unreal

eal = unreal.EditorAssetLibrary
BP_PATH = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
BP_C = "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C"

unreal.log("############ 跳跃参数修改")
bp = eal.load_asset(BP_PATH)
cls = unreal.load_class(None, BP_C)
cdo = unreal.get_default_object(cls)
cmc = cdo.get_components_by_class(unreal.CharacterMovementComponent)[0]
old = cmc.get_editor_property("jump_z_velocity")
G = 980.0
unreal.log("   改前 jump_z_velocity = %.0f  ⇒ 理论跳高 %.0f cm（= v²/2g）" % (old, old * old / (2 * G)))

NEW_V = 420.0
cmc.set_editor_property("jump_z_velocity", NEW_V)
unreal.log("   改后 jump_z_velocity = %.0f  ⇒ 理论跳高 %.0f cm" % (NEW_V, NEW_V * NEW_V / (2 * G)))

try:
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.log("   编译通过")
except Exception as ex:
    unreal.log("   编译 ERR %s" % str(ex)[:80])
unreal.log("   save -> %s" % eal.save_asset(BP_PATH))

unreal.log("############ 复核")
cdo2 = unreal.get_default_object(unreal.load_class(None, BP_C))
cmc2 = cdo2.get_components_by_class(unreal.CharacterMovementComponent)[0]
v = cmc2.get_editor_property("jump_z_velocity")
unreal.log("   jump_z_velocity = %.0f  ⇒ 跳高 %.0f cm" % (v, v * v / (2 * G)))
unreal.log("############ DONE")
