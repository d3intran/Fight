import unreal

PA = "/Game/Character/Darius/SK_Darius_GodKing_Physics"
pa = unreal.load_object(None, PA)

unreal.log("############ 1. 物理资产编辑 API 是否可用")
for cls in ("PhysicsAssetEditorSubsystem", "PhysicsAssetEditorLibrary", "SkeletalMeshSocket",
            "ConstraintInstance", "ConstraintOrionDriveInstance", "LinearConstraintDrive",
            "AngularConstraintDrive", "ConstraintDrive", "ShapeBase", "SphereShape",
            "ConstraintToActor", "BodyInstance", "AggregateShape"):
    unreal.log("   unreal.%-32s exists=%s" % (cls, hasattr(unreal, cls)))
try:
    unreal.log("   ConstraintInstance 属性: %s" % [m for m in dir(unreal.ConstraintInstance) if not m.startswith("_")])
except Exception as ex:
    unreal.log("   CI ERR %s" % str(ex)[:60])

unreal.log("############ 2. 约束数量与限位")
got = None
for args in ((True,), (False,), ()):
    try:
        got = pa.get_constraints(*args)
        unreal.log("   get_constraints%s -> %d" % (args, len(got)))
        break
    except Exception as ex:
        unreal.log("   get_constraints%s ERR %s" % (args, str(ex)[:60]))
if got:
    c0 = got[0]
    fields = [m for m in dir(c0) if not m.startswith("_")]
    unreal.log("   ConstraintTemplate: %s" % fields)
    for c in got[:8]:
        try:
            i = c.get_editor_property("instance")
        except Exception as ex:
            unreal.log("   %s instance ERR %s" % (c.get_name(), str(ex)[:40]))
            continue
        vals = {}
        for pr in ("linear_limit_x", "linear_limit_y", "linear_limit_z", "angular_limit_mode",
                   "swing_limit_type", "swing_base_swing_limit", "swing_max_swing_limit",
                   "twist_limit", "linear_drive_x", "linear_drive_y", "linear_drive_z",
                   "angular_drive_swing_x", "angular_drive_swing_y", "angular_drive_twist",
                   "projection_target", "break_through", "damping", "motor_model", "tree_model",
                   "enable_base_swing_limit", "enable_max_swing_limit", "enable_twist_limit",
                   "enable_linear_limit_x", "enable_linear_limit_y", "enable_linear_limit_z",
                   "linear_drive_frequency", "angular_drive_frequency", "angular_drive_mass_normalization"):
            try:
                v = i.get_editor_property(pr)
                vals[pr] = str(v)[:70]
            except Exception:
                pass
        try:
            b1 = c.get_editor_property("constraint_bone1_name")
            b2 = c.get_editor_property("constraint_bone2_name")
        except Exception:
            b1 = b2 = "?"
        unreal.log("   --- %s <-> %s" % (b1, b2))
        for k in sorted(vals):
            unreal.log("        %-32s %s" % (k, vals[k]))
unreal.log("############ DONE")
