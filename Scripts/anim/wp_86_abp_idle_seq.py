# -*- coding: utf-8 -*-
"""
wp_86_abp_idle_seq.py —— 把 ABP_Darius_Test 的 Idle 状态序列换成 A_Darius_idle1

现状：Idle 状态里是 AnimGraphNode_SequencePlayer(A_Darius_AxeIdle_Layered)（M1 的 Mixamo 线）。
目标：换成 /Game/Character/Darius/Animations/LOL_Retarget/A_Darius_idle1。

只改这一处；Jump/Fall/Land 的 4 个 SequencePlayer 不动。
改完 compile + save。

跑法：
    echo dry > Saved/Attack/wp86_mode.txt
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_86_abp_idle_seq.py
"""
import unreal

ABP = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
MODE_FILE = "E:/UE/Fight/Saved/Attack/wp86_mode.txt"

REPLACE = {
    "A_Darius_AxeIdle_Layered": "/Game/Character/Darius/Animations/LOL_Retarget/A_Darius_idle1",
}


def L(s): unreal.log("[WP86] %s" % s)
def LW(s): unreal.log_warning("[WP86] %s" % s)


def mode():
    try:
        return open(MODE_FILE, encoding="utf-8").read().strip().lower()
    except Exception:
        return "dry"


def list_seq_nodes(abp, tag):
    """返回 [(node, seq_asset, seq_name)]"""
    out = []
    try:
        nodes = unreal.AnimationLibrary.get_nodes_of_class(abp, unreal.AnimGraphNode_SequencePlayer)
    except Exception as ex:
        LW("   [%s] 查询失败: %s" % (tag, str(ex)[:70]))
        return out
    L("   [%s] SequencePlayer x%d" % (tag, len(nodes)))
    for i, n in enumerate(nodes):
        seq = None
        try:
            sub = n.get_editor_property("node")
            seq = sub.get_editor_property("sequence")
        except Exception as ex:
            LW("      #%d 读 node.sequence 失败: %s" % (i, str(ex)[:60]))
        nm = seq.get_name() if seq else "None"
        L("      #%d  %-34s %s" % (i, nm, seq.get_path_name() if seq else ""))
        out.append((n, seq, nm))
    return out


abp = unreal.load_asset(ABP)
if abp is None:
    raise RuntimeError("载入 ABP 失败: %s" % ABP)
L("模式 = %s" % mode())
L("ABP = %s" % abp.get_name())
nodes = list_seq_nodes(abp, "改前")

# 计划
plan = []
for n, seq, nm in nodes:
    if nm in REPLACE:
        plan.append((n, nm, REPLACE[nm]))
L("")
L("计划替换 %d 处:" % len(plan))
for _, old, new in plan:
    a = unreal.load_asset(new)
    L("    %-34s -> %-34s (%s)" % (old, new.rsplit("/", 1)[-1],
                                   "存在" if a is not None else "!! 缺失"))

if mode() != "apply":
    L("")
    L("[dry] 把 Saved/Attack/wp86_mode.txt 改成 apply 后重跑。")
    L("WP86 DONE")
else:
    # ---------- 写入 ----------
    done = 0
    for n, old, new in plan:
        a = unreal.load_asset(new)
        if a is None:
            LW("   跳过（资产缺失）: %s" % new); continue
        try:
            sub = n.get_editor_property("node")
            sub.set_editor_property("sequence", a)
            n.set_editor_property("node", sub)
            done += 1
            L("   已替换: %s -> %s" % (old, a.get_name()))
        except Exception as ex:
            LW("   替换失败 %s: %s" % (old, str(ex)[:90]))

    # 重新评估图，再编译保存
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(abp)
        L("compile_blueprint OK")
    except Exception as ex:
        LW("compile 失败: %s" % str(ex)[:90])
    ok = unreal.EditorAssetLibrary.save_loaded_asset(abp)
    L("保存: %s   （替换 %d 处）" % (ok, done))

    abp2 = unreal.load_asset(ABP)
    list_seq_nodes(abp2, "改后")
L("WP86 DONE")
