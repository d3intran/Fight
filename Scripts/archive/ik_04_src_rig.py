import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()

DIR = "/Game/Character/Darius/Retarget"
SRC_MESH = "/Game/Character/Darius/LOL_Source/SK_LOL_Darius"


def get_rig(name):
    p = DIR + "/" + name
    if eal.does_asset_exist(p):
        return eal.load_asset(p), p
    fac = unreal.IKRigDefinitionFactory()
    return at.create_asset(name, DIR, unreal.IKRigDefinition, fac), p


# ---------------------------------------------------------------- 1) 目标链起止骨
trig, tpath = get_rig("IK_Darius_Target")
tctrl = unreal.IKRigController.get_controller(trig)

L("=== 目标 IK Rig 关键链的 start -> end ===")
L("  %-18s %-24s %-24s" % ("chain", "start", "end"))
for cn in ("Spine", "Neck", "Head", "LeftLeg", "LeftFoot", "LeftClavicle", "LeftArm",
           "RightLeg", "RightFoot", "RightClavicle", "RightArm"):
    try:
        s = tctrl.get_retarget_chain_start_bone(cn)
        e = tctrl.get_retarget_chain_end_bone(cn)
        L("  %-18s %-24s %-24s" % (cn, s, e))
    except Exception as ex:
        L("  %-18s <err %s>" % (cn, ex))

# ---------------------------------------------------------------- 2) 源 IK Rig
srig, spath = get_rig("IK_LOL_Source")
sctrl = unreal.IKRigController.get_controller(srig)

L("")
L("=== 源 IK Rig ===")
smesh = eal.load_asset(SRC_MESH)
L("  mesh = %s" % (SRC_MESH, ))
L("  set_skeletal_mesh -> %s" % sctrl.set_skeletal_mesh(smesh))
L("  现有链 = %d" % len(sctrl.get_retarget_chains() or []))

# 链名必须与目标 IK Rig 完全一致，Retargeter 才能自动配对。
# 起止骨按目标链的实际定义对齐（实测目标侧）：
#   Spine        spine_01 -> spine_03   (3 骨)  | 源只有 Spine1/Spine2 (2 骨)
#   Neck         neck_01  -> neck_01    (单骨)
#   Head         head     -> head       (单骨)
#   LeftLeg      thigh_l  -> foot_l     (3 骨)
#   LeftArm      upperarm_l -> hand_l   (3 骨，不含 clavicle)
#   LeftClavicle clavicle_l -> clavicle_l (单骨)
SRC_CHAINS = [
    ("Spine",         "Spine1",     "Spine2"),
    ("Neck",          "Neck",       "Neck"),
    ("Head",          "Head",       "Head"),
    ("LeftLeg",       "L_Hip",      "L_Foot"),
    ("RightLeg",      "R_Hip",      "R_Foot"),
    ("LeftClavicle",  "L_Clavicle", "L_Clavicle"),
    ("RightClavicle", "R_Clavicle", "R_Clavicle"),
    ("LeftArm",       "L_Shoulder", "L_Hand"),
    ("RightArm",      "R_Shoulder", "R_Hand"),
]

L("")
L("=== 添加源链 ===")
existing = set()
for c in (sctrl.get_retarget_chains() or []):
    try:
        existing.add(str(c.get_editor_property("chain_name")))
    except Exception:
        pass
L("  已有链名: %s" % sorted(existing))

for cn, sb, eb in SRC_CHAINS:
    if cn in existing:
        L("   %-16s 已存在，跳过" % cn)
        continue
    try:
        # 签名: add_retarget_chain(chain_name, start_bone, end_bone, goal_name)
        r = sctrl.add_retarget_chain(cn, sb, eb, "")
        L("   add %-16s (%s -> %s) -> %s" % (cn, sb, eb, r))
    except Exception as ex:
        LW("   add %-16s 失败: %s" % (cn, ex))
        try:
            r = sctrl.add_retarget_chain(cn, sb, eb)
            L("   add(3参) %-16s -> %s" % (cn, r))
        except Exception as ex2:
            LW("   add(3参) 也失败: %s" % ex2)

L("")
L("=== 源链结果 ===")
for c in (sctrl.get_retarget_chains() or []):
    try:
        n = str(c.get_editor_property("chain_name"))
        s = sctrl.get_retarget_chain_start_bone(n)
        e = sctrl.get_retarget_chain_end_bone(n)
        L("   %-18s %-24s -> %s" % (n, s, e))
    except Exception as ex:
        L("   <err %s>" % ex)

# root 设置
def safe(label, fn, *a):
    try:
        L("  %-34s = %s" % (label, fn(*a)))
    except Exception as ex:
        L("  %-34s : %s" % (label, ex))


L("")
L("=== root 设置 ===")
safe("src get_retarget_root()", sctrl.get_retarget_root)
safe("tgt get_retarget_root()", tctrl.get_retarget_root)
for tag, c, rootname in (("src", sctrl, "Root"), ("tgt", tctrl, "pelvis")):
    try:
        r = c.set_retarget_root(rootname)
        L("  %s set_retarget_root(%s) -> %s" % (tag, rootname, r))
    except Exception as ex:
        LW("  %s set_retarget_root(%s) 失败: %s" % (tag, rootname, ex))

eal.save_asset(spath, only_if_is_dirty=False)
eal.save_asset(tpath, only_if_is_dirty=False)
L("")
L("saved: %s / %s" % (spath, tpath))
L("=== DONE ===")
