import unreal

AL = unreal.AnimationLibrary
ANIMS = ["/Game/Character/Darius/Anims/A_Darius_Walk_Layered",
         "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered",
         "/Game/Character/Darius/Anims/A_Darius_Idle1"]


def T(v):
    return (v.x, v.y, v.z)


def Q(q):
    return (q.x, q.y, q.z, q.w)


for ap in ANIMS:
    a = unreal.load_object(None, ap)
    if not a:
        unreal.log("   %-24s 不存在" % ap.split("/")[-1])
        continue
    names = [str(x) for x in a.controller.get_model_interface().get_bone_track_names()]
    cape = [x for x in names if "cape" in x.lower()]
    nf = int(AL.get_num_frames(a))
    unreal.log("###### %s  轨道=%d 披风骨轨道=%d 帧=0..%d" % (ap.split("/")[-1], len(names), len(cape), nf))
    if not cape:
        continue
    objs = [unreal.Name(x) for x in cape]
    fr = [0, max(1, nf // 4), max(2, nf // 2), max(3, (3 * nf) // 4), nf]
    P = {}
    for f in fr:
        ps = AL.get_bone_poses_for_frame(a, objs, f, False)
        P[f] = [(T(t.translation), Q(t.rotation)) for t in ps]
    for i, bn in enumerate(cape):
        base = P[fr[0]][i]
        dmax = 0.0
        amax = 0.0
        for f in fr[1:]:
            t, q = P[f][i]
            d = ((t[0] - base[0][0]) ** 2 + (t[1] - base[0][1]) ** 2 + (t[2] - base[0][2]) ** 2) ** 0.5
            dot = abs(sum(base[1][k] * q[k] for k in range(4)))
            dot = min(1.0, max(-1.0, dot))
            import math
            ang = math.degrees(2 * math.acos(min(1.0, dot)))
            dmax = max(dmax, d)
            amax = max(amax, ang)
        unreal.log("   %-20s 全帧最大位移漂移 %.5f   最大旋转 %.3f 度   loc=%s" % (
            bn, dmax, amax, [round(v, 2) for v in base[0]]))
    # 与绑定姿势对比：pelvis 的轨道 loc 用来判断单位尺度
    try:
        i = names.index("pelvis") if "pelvis" in names else None
        if i is not None:
            ps = AL.get_bone_poses_for_frame(a, [unreal.Name("pelvis")], 0, False)
            unreal.log("   (参照) pelvis 局部平移 = %s" % [round(v, 4) for v in T(ps[0].translation)])
    except Exception as ex:
        unreal.log("   pelvis ERR %s" % str(ex)[:50])
unreal.log("###### DONE")
