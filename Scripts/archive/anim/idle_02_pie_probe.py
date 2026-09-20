import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

unreal.log("PIE running = %s" % les.is_in_play_in_editor())
unreal.log("UnrealEditorSubsystem 相关方法: %s"
           % [m for m in dir(ues) if "world" in m.lower() or "play" in m.lower()])
unreal.log("LevelEditorSubsystem 相关方法: %s"
           % [m for m in dir(les) if "world" in m.lower() or "play" in m.lower()])

gw = None
for m in ("get_game_world", "get_editor_world"):
    f = getattr(ues, m, None)
    if f is None:
        unreal.log("   %s 不存在" % m)
        continue
    try:
        w = f()
        unreal.log("   %s() = %s" % (m, w))
        if m == "get_game_world":
            gw = w
    except Exception as ex:
        unreal.log("   %s ERR %s" % (m, str(ex)[:80]))

worlds = []
if gw:
    worlds.append(("game", gw))
worlds.append(("editor", ues.get_editor_world()))

for tag, w in worlds:
    if not w:
        continue
    unreal.log("---- world[%s] = %s  name=%s" % (tag, w, w.get_name()))
    try:
        actors = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
        unreal.log("     actor 数 = %d" % len(actors))
        for a in actors[:12]:
            unreal.log("       %-34s %s" % (a.get_name(), a.get_class().get_name()))
    except Exception as ex:
        unreal.log("     枚举 actor ERR %s" % str(ex)[:80])

# 在 PIE 世界里找角色并读实时骨骼
if gw:
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        cn = a.get_class().get_name()
        if "Darius" in a.get_name() or "Darius" in cn or "Character" in cn:
            unreal.log("### 候选角色 %s (%s)" % (a.get_name(), cn))
            comps = a.get_components_by_class(unreal.SkeletalMeshComponent)
            for c in comps:
                unreal.log("   组件 %s  anim_mode=%s" % (c.get_name(), c.get_animation_mode()))
                try:
                    anim = c.get_anim_instance()
                    unreal.log("     anim_instance = %s" % (anim.get_class().get_name() if anim else None))
                except Exception as ex:
                    unreal.log("     anim_instance ERR %s" % str(ex)[:70])
                try:
                    pa = c.get_editor_property("physics_asset")
                    unreal.log("     physics_asset = %s" % (pa.get_name() if pa else None))
                except Exception as ex:
                    unreal.log("     physics_asset ERR %s" % str(ex)[:70])
                for b in ("pelvis", "spine_03", "head", "thigh_l", "thigh_r",
                          "cape_chain_01_l", "cape_chain_05_l", "cape_chain_09_l"):
                    try:
                        st = c.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD)
                        unreal.log("     %-18s world=%s" % (
                            b, [round(v, 2) for v in (st.translation.x, st.translation.y, st.translation.z)]))
                    except Exception as ex:
                        unreal.log("     %-18s ERR %s" % (b, str(ex)[:60]))
unreal.log("### DONE")
