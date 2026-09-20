import unreal

PA = "/Game/Character/Darius/SK_Darius_GodKing_Physics"
pa = unreal.load_object(None, PA)

acc = pa.get_constraints(True)
unreal.log("############ 约束配对（%d 条）" % len(acc))
a0 = acc[0]
unreal.log("   accessor 可访问名: %s" % [m for m in dir(a0) if not m.startswith("_")])
for pr in ("constraint_bone1_name", "constraint_bone2_name", "name", "instance",
           "constraint_template", "constraint_name", "bone1", "bone2"):
    try:
        unreal.log("   prop %-26s -> %s" % (pr, str(a0.get_editor_property(pr))[:100]))
    except Exception as ex:
        unreal.log("   prop %-26s ERR %s" % (pr, str(ex)[:50]))
for c in acc:
    try:
        s = str(c.export_text())
        unreal.log("   %s" % s[:220])
    except Exception as ex:
        unreal.log("   export ERR %s" % str(ex)[:60])
        break
unreal.log("############ 物理资产上其它可读属性")
for pr in ("preview_skeletal_mesh", "skeletal_mesh", "constraint_setup", "collision_disabled_bodies",
           "bounds_bodies", "preview_body_thickness", "preview_physics", "preview_anim_sequence",
           "preview_local_axis", "preview_world_axis", "preview_center_of_mass"):
    try:
        v = pa.get_editor_property(pr)
        unreal.log("   %-28s = %s" % (pr, "len=%d" % len(v) if hasattr(v, "__len__") else str(v)[:80]))
    except Exception as ex:
        unreal.log("   %-28s ERR %s" % (pr, str(ex)[:45]))
unreal.log("############ DONE")
