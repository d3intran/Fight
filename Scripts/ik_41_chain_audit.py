# -*- coding: utf-8 -*-
"""审计 IK Rig / Retargeter 的**链**：源有几条、目标有几条、哪些被映射上了。

## 为什么这是关键
`auto_align_all_bones(CHAIN_TO_CHAIN)` 的原理是**用链里子骨的方向**定本骨朝向。
- 骨不在任何链里 ⇒ 定不出方向 ⇒ **偏移留 0** ⇒ 该骨整棵子树继承错误。
- 链没有源对应（源 IK Rig 只有 9 条链，目标 29 条）⇒ 该链根本不会被对齐。

实测（`ik_38` 读回）：目标侧 `clavicle_l/r`、`neck_01`、`head`、`hand_l/r`、`foot_l/r`
的 retarget pose 偏移**全是 0** —— 而 `ik_37` 里锁骨 49~67°、头 62°、小臂 56° 全部超门限。
两者对得上：**就是这些链没被映射**。

本脚本只读不写：把两边的链、映射关系、以及源骨架可用骨名全部列出来，
为「给源补链」提供依据。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

IK_SRC = "/Game/Character/Darius/Retarget/IK_LOL_Source"
IK_TGT = "/Game/Character/Darius/Retarget/IK_Darius_Target"
RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
MESH_SRC = "/Game/Character/Darius/LOL_Source/SK_LOL_Darius"
MESH_TGT = "/Game/Character/Darius/SK_Darius_GodKing"
E = unreal.RetargetSourceOrTarget


def call(fn, *args):
    try:
        return fn(*args)
    except Exception as ex:
        return "<ERR:%s>" % str(ex)[:70]


def bone_names(mesh_path):
    """借一个临时 SkeletalMeshActor 读骨名（`Skeleton` 资产没暴露 reference_skeleton）。"""
    sm = eal.load_asset(mesh_path)
    if sm is None:
        return None, "mesh 加载失败"
    a = actor_sub.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
    a.set_actor_label("Probe_BoneNames")
    comp = a.get_editor_property("skeletal_mesh_component")
    try:
        comp.set_skinned_asset_and_update(sm)
    except Exception:
        comp.set_skeletal_mesh(sm)
    try:
        n = int(comp.get_num_bones())
        names = [str(comp.get_bone_name(i)) for i in range(n)]
    except Exception as ex:
        names, n = [], "get_num_bones 失败: %s" % str(ex)[:70]
    actor_sub.destroy_actor(a)
    return names, n


# ---------------------------------------------------------------- 1. 链映射
rtg = eal.load_asset(RTG)
if rtg is None:
    LW("!! 找不到 retargeter")
    raise SystemExit(1)
ctrl = unreal.IKRetargeterController.get_controller(rtg)
ALL = sorted([x for x in dir(ctrl) if not x.startswith("_")])
L("################ 1. 含 chain 的控制器接口")
L("   " + ", ".join([x for x in ALL if "chain" in x.lower()]))

L("")
L("################ 2. 链设置（哪条链有源对应）")
for tag, side in (("SOURCE", E.SOURCE), ("TARGET", E.TARGET)):
    arr = call(ctrl.get_all_chain_settings, side)
    if not isinstance(arr, (list, tuple)) or not arr:
        L("   %s: get_all_chain_settings -> %s" % (tag, arr))
        continue
    L("")
    L("   ---- %s 共 %d 条" % (tag, len(arr)))
    if tag == "TARGET":
        L("   %-18s %-18s %s" % ("链名", "源链名", "其它字段"))
        n_unmapped = 0
        for cs in arr:
            try:
                cn = str(cs.chain_name)
                sn = str(cs.source_chain_name)
            except Exception:
                L("      %s" % str(cs)[:100])
                continue
            extra = ""
            try:
                fields = [f for f in dir(cs) if not f.startswith("_") and f not in
                          ("chain_name", "source_chain_name", "static_class")]
                extra = ", ".join("%s=%s" % (f, getattr(cs, f)) for f in fields[:6])
            except Exception:
                pass
            if not sn or sn == "None":
                n_unmapped += 1
            L("   %-18s %-18s %s" % (cn, sn, extra[:90]))
        L("   ⇒ 无源对应的目标链 = %d / %d" % (n_unmapped, len(arr)))
    else:
        for cs in arr:
            try:
                L("      %-18s -> %s" % (cs.chain_name, cs.end_bone))
            except Exception:
                L("      %s" % str(cs)[:90])

# ---------------------------------------------------------------- 3. 骨名
L("")
L("################ 3. 骨架骨名")
for tag, mp in (("SOURCE", MESH_SRC), ("TARGET", MESH_TGT)):
    names, n = bone_names(mp)
    L("")
    L("   ---- %s  %s  骨数=%s" % (tag, mp.split("/")[-1], n))
    if names:
        L("      %s" % ", ".join(names))
L("=== DONE ===")
