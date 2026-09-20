import os
import unreal

PA = "/Game/Character/Darius/SK_Darius_GodKing_Physics"


def LO(p):
    try:
        return unreal.load_object(None, p)
    except Exception:
        return None


pa = LO(PA)
unreal.log("############ 1. 物理资产里的约束（有约束=有刚体对）")
if pa:
    try:
        cs = pa.get_constraints()
        unreal.log("   约束数 = %d" % len(cs))
        names = []
        for c in cs[:80]:
            try:
                n = c.get_editor_property("constraint_bone1_name")
                m = c.get_editor_property("constraint_bone2_name")
                names.append("%s<->%s" % (n, m))
            except Exception as ex:
                names.append("ERR %s" % str(ex)[:40])
        unreal.log("   %s" % names)
    except Exception as ex:
        unreal.log("   get_constraints ERR %s" % str(ex)[:80])
    for b in ("cape_chain_01_l", "cape_chain_05_l", "cape_chain_09_l"):
        try:
            r = pa.get_constraint_by_bone_names(b, "cape_chain_02_l")
            unreal.log("   get_constraint_by_bone_names(%s, cape_chain_02_l) -> %s" % (b, r))
        except Exception as ex:
            unreal.log("   by_bone_names ERR %s" % str(ex)[:60])
    for m in ("pelvis", "spine_01", "head", "cape_chain_01_m", "cape_chain_05_m"):
        try:
            r = pa.get_constraint_by_name(m)
            unreal.log("   get_constraint_by_name(%s) -> %s" % (m, r))
        except Exception as ex:
            unreal.log("   by_name(%s) ERR %s" % (m, str(ex)[:50]))

unreal.log("############ 2. SkeletalMeshEditorSubsystem 能做什么")
try:
    unreal.log("%s" % [m for m in dir(unreal.SkeletalMeshEditorSubsystem) if not m.startswith("_")])
except Exception as ex:
    unreal.log("   ERR %s" % ex)

unreal.log("############ 3. 物理资产文件大小 / 相关资产")
base = "E:/UE/Fight/Content/Character/Darius"
for fn in sorted(os.listdir(base)):
    p = os.path.join(base, fn)
    if os.path.isfile(p) and fn.lower().endswith(".uasset"):
        unreal.log("   %-42s %8d bytes" % (fn, os.path.getsize(p)))

unreal.log("############ 4. RigidBody 节点在图上是否接线")
ABP = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
abp = LO(ABP)
if abp:
    for g in unreal.AnimationLibrary.get_animation_graphs(abp):
        if g.get_name() != "AnimGraph":
            continue
        nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_Base)
        for n in nodes:
            cn = n.get_class().get_name()
            try:
                pins = [str(p.get_name()) for p in n.get_input_pins()] + \
                       ["OUT:" + str(p.get_name()) for p in n.get_output_pins()]
            except Exception:
                pins = []
            unreal.log("   %-46s pins=%s" % (cn, pins))
unreal.log("############ DONE")
