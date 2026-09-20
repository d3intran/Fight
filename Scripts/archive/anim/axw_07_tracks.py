import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

UP_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo"
LOW_PATH = "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"
SK_PATH = "/Game/Character/Darius/SK_Darius_GodKing_Skeleton"

up = eal.load_asset(UP_PATH)
low = eal.load_asset(LOW_PATH)
skel = eal.load_asset(SK_PATH)

up_names = [str(n) for n in up.controller.get_model_interface().get_bone_track_names()]
low_names = [str(n) for n in low.controller.get_model_interface().get_bone_track_names()]
unreal.log("UP  tracks = %d" % len(up_names))
unreal.log("LOW tracks = %d" % len(low_names))
unreal.log("UP-only  = %s" % sorted(set(up_names) - set(low_names)))
unreal.log("LOW-only = %d 个: %s" % (len(set(low_names) - set(up_names)), sorted(set(low_names) - set(up_names))[:40]))
unreal.log("UP frames=%d LOW frames=%d" % (AL.get_num_frames(up), AL.get_num_frames(low)))

# 层级：spine_01 子树
ref = unreal.AnimationLibrary.get_bone_pose_for_frame  # noqa
unreal.log("### skeleton bone count = %d" % len(skel.get_editor_property("bone_tree") or []))

# 用 anim 的 find_bone_path_to_root 反推父子
def chain(anim, bone):
    try:
        return [str(x) for x in AL.find_bone_path_to_root(anim, bone)]
    except Exception:
        return []

SPINE = "spine_01"
parents = {}
for b in set(up_names) | set(low_names):
    c = chain(up, b)
    parents[b] = c[1] if len(c) > 1 else None

upper = set()
stack = [SPINE]
while stack:
    cur = stack.pop()
    if cur in upper:
        continue
    upper.add(cur)
    for b, p in parents.items():
        if p == cur:
            stack.append(b)

unreal.log("### spine_01 子树 (%d 个): %s" % (len(upper), sorted(upper)))
unreal.log("### 下半身（LOW 有、非子树）: %s" % sorted(set(low_names) - upper))
unreal.log("### UP 里属于子树且 LOW 没有的: %s" % sorted(set(up_names) & upper - set(low_names)))
unreal.log("### UP 里不属于子树的（会丢）: %s" % sorted(set(up_names) - upper))

# pelvis 世界旋转对比
def q_at(anim, bone, f):
    t = AL.get_bone_pose_for_frame(anim, bone, f, False)
    return (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w), (t.translation.x, t.translation.y, t.translation.z)

for f in (0, 20, 40):
    qu, tu = q_at(up, "pelvis", min(f, AL.get_num_frames(up)))
    ql, tl = q_at(low, "pelvis", min(f, AL.get_num_frames(low)))
    dot = abs(sum(a * b for a, b in zip(qu, ql)))
    import math
    ang = math.degrees(2 * math.acos(max(-1.0, min(1.0, dot))))
    unreal.log("f%-3d pelvis local rot UP=%s LOW=%s  angle=%.2f deg" % (
        f, [round(v, 4) for v in qu], [round(v, 4) for v in ql], ang))
    unreal.log("      pelvis local loc UP=%s LOW=%s" % ([round(v, 4) for v in tu], [round(v, 4) for v in tl]))

# 根骨
for nm in ("root", "pelvis", "spine_01", "spine_02", "spine_03"):
    pu = AL.get_bone_pose_for_frame(up, nm, 0, False)
    pl = AL.get_bone_pose_for_frame(low, nm, 0, False)
    unreal.log("f0 %-9s UP t=%s s=%s | LOW t=%s s=%s" % (
        nm,
        [round(v, 4) for v in (pu.translation.x, pu.translation.y, pu.translation.z)],
        [round(v, 4) for v in (pu.scale3d.x, pu.scale3d.y, pu.scale3d.z)],
        [round(v, 4) for v in (pl.translation.x, pl.translation.y, pl.translation.z)],
        [round(v, 4) for v in (pl.scale3d.x, pl.scale3d.y, pl.scale3d.z)]))
