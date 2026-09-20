import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

NEW = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"
UP = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Mixamo"
LOW = "/Game/Character/Darius/Anims_TP_v2/A_Darius_idle1"

WATCH = ["spine_01", "spine_02", "spine_03", "neck_01", "head",
         "cape_chain_01_m", "cape_chain_05_m", "cape_chain_09_m",
         "clavicle_l", "upperarm_l", "hand_r", "pelvis", "thigh_l", "foot_l"]

assets = {}
for tag, p in (("NEW", NEW), ("AXEIDLE", UP), ("OLDIDLE", LOW)):
    a = eal.load_asset(p)
    if not a:
        unreal.log_error("%s 加载失败" % p)
        continue
    nf = int(AL.get_num_frames(a))
    objs = [unreal.Name(b) for b in WATCH]
    poses = AL.get_bone_poses_for_frame(a, objs, 0, False)
    assets[tag] = {}
    for i, b in enumerate(WATCH):
        t = poses[i]
        assets[tag][b] = ((t.translation.x, t.translation.y, t.translation.z),
                          (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
                          (t.scale3d.x, t.scale3d.y, t.scale3d.z))
    unreal.log("### %-8s %-58s frames=%d tracks=%d" % (
        tag, p, nf, len(a.controller.get_model_interface().get_bone_track_names())))


def ang(a, b):
    import math
    d = abs(sum(x * y for x, y in zip(a, b)))
    return math.degrees(2.0 * math.acos(max(-1.0, min(1.0, d))))


unreal.log("### frame0 局部旋转对比（度）")
unreal.log("   %-18s %10s %10s %10s" % ("bone", "NEW~AXEIDLE", "NEW~OLDIDLE", "AXEIDLE~OLDIDLE"))
for b in WATCH:
    if b not in assets.get("NEW", {}):
        continue
    qn = assets["NEW"][b][1]
    qa = assets["AXEIDLE"].get(b, ((0, 0, 0), (0, 0, 0, 1), (1, 1, 1)))[1]
    qo = assets["OLDIDLE"].get(b, ((0, 0, 0), (0, 0, 0, 1), (1, 1, 1)))[1]
    unreal.log("   %-18s %10.2f %10.2f %10.2f" % (b, ang(qn, qa), ang(qn, qo), ang(qa, qo)))

unreal.log("### frame0 局部平移对比")
for b in ("spine_01", "pelvis", "cape_chain_01_m"):
    if b in assets.get("NEW", {}):
        unreal.log("   %-18s NEW=%s  AXEIDLE=%s  OLDIDLE=%s" % (
            b, [round(v, 4) for v in assets["NEW"][b][0]],
            [round(v, 4) for v in assets["AXEIDLE"][b][0]],
            [round(v, 4) for v in assets["OLDIDLE"][b][0]]))

unreal.log("### 循环接缝（首末 key 全骨）")
a = eal.load_asset(NEW)
names = [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]
nf = int(AL.get_num_frames(a))
objs = [unreal.Name(b) for b in names]
p0 = AL.get_bone_poses_for_frame(a, objs, 0, False)
p1 = AL.get_bone_poses_for_frame(a, objs, nf, False)
import math
worst = (0.0, None)
for i, b in enumerate(names):
    d = math.sqrt(sum((getattr(p0[i].translation, k) - getattr(p1[i].translation, k)) ** 2
                      for k in ("x", "y", "z")))
    if d > worst[0]:
        worst = (d, b)
unreal.log("   最大 %.4f cm (%s)" % worst)
unreal.log("### DONE")
