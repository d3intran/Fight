import unreal

PA = "/Game/Character/Darius/SK_Darius_GodKing_Physics"
pa = unreal.load_object(None, PA)

TRY = ["body_setups", "skeletal_body_setups", "constraint_setup", "body_instances",
       "actor_constraints", "skeleton", "physical_asset_name"]
unreal.log("### 1. PhysicsAsset 容器属性")
for pr in TRY:
    try:
        v = pa.get_editor_property(pr)
        unreal.log("   %-24s OK  len=%s  first=%s" % (pr, len(v) if hasattr(v, "__len__") else "-",
                                                     type(v[0]).__name__ if hasattr(v, "__len__") and len(v) else "-"))
    except Exception as ex:
        unreal.log("   %-24s ERR %s" % (pr, str(ex)[:55]))

try:
    bs = pa.get_editor_property("body_setups")
except Exception:
    bs = []
unreal.log("### 2. 前 3 个 body 条目可读字段")
if bs:
    unreal.log("   entry 字段: %s" % [m for m in dir(bs[0]) if not m.startswith("_")])
    for e in bs[:3]:
        try:
            unreal.log("   entry export_text = %s" % str(e.export_text())[:200])
        except Exception as ex:
            unreal.log("   export ERR %s" % str(ex)[:40])
        try:
            sb = e.get_editor_property("body_setup")
            unreal.log("      body_setup=%s" % sb)
            for pr in ("bone_name", "physics_type", "body_mass", "linear_damping",
                       "angular_damping", "collision_response", "b_override_mass",
                       "b_override_damping", "interpolate"):
                try:
                    unreal.log("      %-20s = %s" % (pr, sb.get_editor_property(pr)))
                except Exception as ex:
                    unreal.log("      %-20s ERR %s" % (pr, str(ex)[:40]))
        except Exception as ex:
            unreal.log("      body_setup ERR %s" % str(ex)[:40])

unreal.log("### 3. 约束条目")
try:
    cs = pa.get_editor_property("constraint_setup")
    unreal.log("   len=%d" % len(cs))
    if cs:
        unreal.log("   entry 字段: %s" % [m for m in dir(cs[0]) if not m.startswith("_")])
        for e in cs[:2]:
            try:
                unreal.log("   export=%s" % str(e.export_text())[:160])
            except Exception as ex:
                unreal.log("   ERR %s" % str(ex)[:40])
            try:
                t = e.get_editor_property("constraint_template")
                unreal.log("      template=%s" % t)
                for pr in ("name", "bone1", "bone2", "constraint_bone1", "constraint_bone2",
                           "instance", "orm", "break_force", "break_torque"):
                    try:
                        unreal.log("      %-20s = %s" % (pr, str(t.get_editor_property(pr))[:70]))
                    except Exception:
                        pass
            except Exception as ex:
                unreal.log("      template ERR %s" % str(ex)[:40])
except Exception as ex:
    unreal.log("   constraint_setup ERR %s" % str(ex)[:50])
unreal.log("### DONE")
