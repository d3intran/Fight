import unreal

unreal.log("Skeleton 里含 socket 的: %s" % [m for m in dir(unreal.Skeleton) if "socket" in m.lower()])
unreal.log("SkeletalMesh 里含 socket 的: %s" % [m for m in dir(unreal.SkeletalMesh) if "socket" in m.lower()])
unreal.log("SkeletalMeshComponent 里含 socket/attach 的: %s"
           % [m for m in dir(unreal.SkeletalMeshComponent) if "socket" in m.lower() or "attach" in m.lower()])
unreal.log("SkeletalMeshSocket: %s" % [m for m in dir(unreal.SkeletalMeshSocket) if not m.startswith("_")])

skel = unreal.load_object(None, "/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
mesh = unreal.load_object(None, "/Game/Character/Darius/SK_Darius_GodKing")
for tag, o in (("skeleton", skel), ("mesh", mesh)):
    for m in ("get_socket_by_name", "find_socket", "num_sockets", "get_sockets"):
        f = getattr(o, m, None)
        if not f:
            continue
        try:
            if m == "get_socket_by_name":
                unreal.log("   %s.%s('hand_rSocket') = %s" % (tag, m, f("hand_rSocket")))
            elif m == "find_socket":
                unreal.log("   %s.%s('hand_rSocket') = %s" % (tag, m, f("hand_rSocket")))
            else:
                unreal.log("   %s.%s() = %s" % (tag, m, f()))
        except Exception as ex:
            unreal.log("   %s.%s ERR %s" % (tag, m, str(ex)[:60]))

unreal.log("### hand_rSocket 是不是一根骨？")
a = unreal.load_object(None, "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered")
names = [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]
unreal.log("   骨名里含 hand_r 的: %s" % [n for n in names if "hand_r" in n.lower()])
try:
    unreal.log("   find_bone_path_to_root(hand_rSocket) = %s"
               % [str(x) for x in unreal.AnimationLibrary.find_bone_path_to_root(a, "hand_rSocket")])
except Exception as ex:
    unreal.log("   hand_rSocket 不是骨：%s" % str(ex)[:70])

unreal.log("### BP 上 WeaponAxe 的挂点")
bp = unreal.load_object(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter")
if bp:
    try:
        scs = bp.get_editor_property("simple_construction_script")
        for n in scs.get_all_nodes():
            nm = str(n.get_editor_property("variable_name"))
            if "Axe" in nm or "Weapon" in nm:
                unreal.log("   SCS 节点 %s" % nm)
                for prop in ("attach_to_name", "attach_to_class", "relative_transform"):
                    try:
                        unreal.log("      %-20s = %s" % (prop, n.get_editor_property(prop)))
                    except Exception as ex:
                        unreal.log("      %-20s ERR %s" % (prop, str(ex)[:40]))
                t = n.get_editor_property("component_template")
                unreal.log("      template = %s" % t)
                for prop in ("relative_rotation", "relative_location", "relative_scale3d"):
                    try:
                        unreal.log("      %-20s = %s" % (prop, t.get_editor_property(prop)))
                    except Exception as ex:
                        unreal.log("      %-20s ERR %s" % (prop, str(ex)[:40]))
    except Exception as ex:
        unreal.log("   SCS ERR %s" % str(ex)[:80])
unreal.log("### DONE")
