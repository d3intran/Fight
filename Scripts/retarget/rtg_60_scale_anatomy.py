# rtg_60_scale_anatomy - 只读：解剖 scale=100 的来源与影响面（不写任何资产）
import unreal

def L(s): print(f"[ANAT] {s}")

skel = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
mesh = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")

L(f"skeleton asset = {skel.get_name()}  class={skel.get_class().get_name()}")

# 骨骼树在 Skeleton 上
try:
    tree = skel.get_editor_property("bone_tree")
    acc = []
    def walk(node, d):
        nm = str(node.get_editor_property("name"))
        acc.append((d, nm))
        for c in node.get_editor_property("children"):
            walk(c, d + 1)
    for node in tree:
        walk(node, 0)
    L(f"总骨数 = {len(acc)}")
    L("--- 前 12 层结构 ---")
    for d, nm in acc:
        if d <= 2:
            L(f"  {'  '*d}{nm}")
except Exception as ex:
    L(f"bone_tree err {ex}")

# 参考骨骼的相对变换（Skeleton 的 reference_skeleton / 各骨 rest）
try:
    ref = skel.get_editor_property("reference_skeleton")
    L(f"reference_skeleton = {ref.get_name()}")
except Exception as ex:
    L(f"ref err {ex}")

APE = unreal.AnimPoseExtensions
try:
    pose = APE.get_anim_pose_for_skeletal_mesh(mesh)
    L("pose ok")
except Exception as ex:
    L(f"get_anim_pose_for_skeletal_mesh err {ex}")
    pose = None

if pose:
    for b in ("darius_godking_mesh_LOD0_Skeleton", "root", "pelvis", "spine_01",
              "thigh_l", "foot_l", "foot_r", "hand_r", "weapon_jnt"):
        for space, sname in ((unreal.AnimPoseSpaces.LOCAL, "LOCAL"), (unreal.AnimPoseSpaces.WORLD, "WORLD")):
            try:
                t = APE.get_bone_pose(pose, unreal.Name(b), space)
                L(f"BONE {b:<34} {sname:<5} loc=({t.translation.x:10.4f},{t.translation.y:10.4f},{t.translation.z:10.4f}) "
                  f"scale=({t.scale3d.x:9.4f},{t.scale3d.y:9.4f},{t.scale3d.z:9.4f})")
            except Exception as ex:
                L(f"BONE {b} {sname} err {str(ex)[:60]}")

try:
    bb = mesh.get_bounds()
    box, org = bb.box_extent, bb.origin
    L(f"mesh bounds origin=({org.x:.2f},{org.y:.2f},{org.z:.2f}) extent=({box.x:.2f},{box.y:.2f},{box.z:.2f}) → 高≈{box.z*2:.1f}cm")
except Exception as ex:
    L(f"bounds err {ex}")

try:
    names = unreal.SkeletalMeshEditorSubsystem.get_socket_names(mesh)
    L(f"SOCKETS = {[str(x) for x in names]}")
except Exception as ex:
    L(f"socket err {ex}")
L("DONE")
