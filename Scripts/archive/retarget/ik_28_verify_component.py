# -*- coding: utf-8 -*-
"""验收：把局部变换（含缩放）逐级复合，算出真正的组件空间坐标（cm）。
判据：关节位置，不依赖骨骼朝向约定 —— 与 AGENTS.md §0.3 的规范一致。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary


def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


class Xform:
    __slots__ = ("p", "q", "s")

    def __init__(self, p=(0.0, 0.0, 0.0), q=(0.0, 0.0, 0.0, 1.0), s=(1.0, 1.0, 1.0)):
        self.p, self.q, self.s = p, q, s

    def child(self, t, q, s):
        sp = self.s
        sc = (t[0] * sp[0], t[1] * sp[1], t[2] * sp[2])
        off = mv(qmat(self.q), sc)
        p = (self.p[0] + off[0], self.p[1] + off[1], self.p[2] + off[2])
        return Xform(p, qmul(self.q, q), (sp[0] * s[0], sp[1] * s[1], sp[2] * s[2]))


def local_of(anim, bone, frame):
    t = AL.get_bone_pose_for_frame(anim, bone, frame, False)
    return ((t.translation.x, t.translation.y, t.translation.z),
            (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
            (t.scale3d.x, t.scale3d.y, t.scale3d.z))


def component_pos(anim, bone, frame):
    """返回 (世界位置 cm, 该骨自身局部旋转四元数)。"""
    chain = [str(x) for x in AL.find_bone_path_to_root(anim, bone)][::-1]  # 最外层在前
    x = Xform()
    for bn in chain:
        t, q, s = local_of(anim, bn, frame)
        x = x.child(t, q, s)
    return x.p, local_of(anim, bone, frame)[1]


def report(pkg, tags, frames):
    a = eal.load_asset(pkg)
    nm = pkg.split("/")[-1]
    if a is None:
        LW("  %s 未加载" % nm)
        return
    L("")
    L("--- %s" % nm)
    for f in frames:
        L("    第 %d 帧：" % f)
        for tag, bone in tags:
            try:
                p, q = component_pos(a, bone, f)
                L("      %-14s (%-16s) x=%8.2f y=%8.2f z=%8.2f" % (tag, bone, p[0], p[1], p[2]))
            except Exception as ex:
                LW("      %-14s %-16s 失败: %s" % (tag, bone, str(ex)[:70]))


TAGS = [("骨盆", "pelvis"), ("头", "head"), ("左脚", "foot_l"),
        ("右脚", "foot_r"), ("左手", "hand_l"), ("右手", "hand_r")]

L("################ 1. 新产物（目标骨架，单位应为 cm）")
report("/Game/Character/Darius/Anims_TP/A_Darius_idle1", TAGS, (0, 32))
report("/Game/Character/Darius/Anims_TP/A_Darius_run", TAGS, (0, 17))

L("")
L("################ 2. 对照：旧一套（同一骨架）")
report("/Game/Character/Darius/Anims/A_Darius_Idle1_TP", TAGS, (0,))
report("/Game/Character/Darius/Anims/A_Darius_Run_TP", TAGS, (0,))

L("")
L("################ 3. 源骨架（单位自洽即可，只看姿势是否合理）")
report("/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_run",
       [("骨盆", "Pelvis"), ("头", "Head"), ("左脚", "L_Foot"), ("右手", "R_Hand")], (0, 17))

L("")
L("################ 4. 旋转是否真的在动（骨盆/大腿/小腿/上臂的局部四元数）")
for pkg in ("/Game/Character/Darius/Anims_TP/A_Darius_run",):
    a = eal.load_asset(pkg)
    for bone in ("pelvis", "thigh_l", "calf_l", "upperarm_r", "head"):
        qs = []
        for f in (0, 8, 17, 26, 34):
            try:
                qs.append(local_of(a, bone, f)[1])
            except Exception:
                pass
        uniq = len(set((round(x[0], 6), round(x[1], 6), round(x[2], 6), round(x[3], 6)) for x in qs))
        L("   %-12s 采样 5 帧，不同姿态数 = %d  %s" % (bone, uniq, "有动画" if uniq > 1 else "**静止**"))
L("=== DONE ===")
