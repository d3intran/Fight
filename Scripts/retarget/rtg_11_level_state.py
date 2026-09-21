# -*- coding: utf-8 -*-
"""rtg_11_level_state —— 只读：关卡 Actor 清单（不做任何生成/销毁）"""

import unreal

L = unreal.log
subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = subs.get_all_level_actors()
L(f"[STATE] actor 总数 = {len(actors)}")
for a in actors:
    L(f"[STATE]   {a.get_name():<24} [{a.get_class().get_name()}]")
L("STATE_DONE")
