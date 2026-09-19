# -*- coding: utf-8 -*-
"""原始坐标探针：把源与产物的髋/膝/踝在**组件空间**的真实坐标直接打印出来。

## 为什么需要它
接触审计给出「产物膝/脚左右次序反了」，但朝向验收说每条腿的方向误差 0.01°
（方向若真被保留，脚不可能交叉）。两边必有一边在骗人。
本脚本不做任何推断，只把**组件空间坐标**打出来 —— 谁在左边、谁在右边，
用原始数字的符号就能直接看出来，不依赖任何骨架约定或身体坐标系。

用法（经网关跑；docstring 里别写自己的文件名）：
    uv run --no-project python Scripts/ue_remote.py Scripts/<本脚本>
"""
import json
import os
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

CFG = "E:/UE/Fight/Saved/retarget_cycle.json"
TGT_DIR = "/Game/Character/Darius/Anims_TP_v2"
if os.path.isfile(CFG):
    try:
        with open(CFG, encoding="utf-8") as fh:
            TGT_DIR = json.load(fh).get("out_dir") or TGT_DIR
    except Exception as ex:
        LW("读 %s 失败: %s" % (CFG, ex))


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


class Sampler:
    def __init__(self, anim, bones):
        self.path = {}
        for b in bones:
            try:
                self.path[b] = [str(x) for x in AL.find_bone_path_to_root(anim, b)][::-1]
            except Exception as ex:
                LW("  路径失败 %s: %s" % (b, str(ex)[:60]))
                self.path[b] = []
        need = set()
        for p in self.path.values():
            need.update(p)
        self.bones = sorted(need)
        self.local = {}
        for f in (0, 8, 16):
            d = {}
            for b in self.bones:
                try:
                    t = AL.get_bone_pose_for_frame(anim, b, f, False)
                    d[b] = ((t.translation.x, t.translation.y, t.translation.z),
                            (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
                            (t.scale3d.x, t.scale3d.y, t.scale3d.z))
                except Exception:
                    d[b] = None
            self.local[f] = d
        self.frames = [f for f in (0, 8, 16) if f < int(AL.get_num_frames(anim))]

    def pos(self, bone, frame):
        p, q, s = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
        for bn in (self.path.get(bone) or []):
            tr = self.local[frame].get(bn)
            if tr is None:
                continue
            t, bq, bs = tr
            off = mv(qmat(q), (t[0] * s[0], t[1] * s[1], t[2] * s[2]))
            p = (p[0] + off[0], p[1] + off[1], p[2] + off[2])
            q = qmul(q, bq)
            s = (s[0] * bs[0], s[1] * bs[1], s[2] * bs[2])
        return p


SRC_BONES = ["Root", "Spine2", "Head", "L_Hip", "R_Hip", "L_KneeLower", "R_KneeLower",
             "L_Foot", "R_Foot"]
TGT_BONES = ["root", "spine_03", "head", "thigh_l", "thigh_r", "calf_l", "calf_r",
             "foot_l", "foot_r"]

PAIRS = [
    ("idle1",
     "/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_idle1",
     TGT_DIR + "/A_Darius_idle1",
     SRC_BONES, TGT_BONES),
    ("run",
     "/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_run",
     TGT_DIR + "/A_Darius_run",
     SRC_BONES, TGT_BONES),
]

L("=== 原始坐标探针（组件空间，单位 cm；不做任何归一化与坐标变换）===")
for tag, src_p, tgt_p, sb, tb in PAIRS:
    sa = eal.load_asset(src_p)
    ta = eal.load_asset(tgt_p)
    if sa is None or ta is None:
        LW("  %s 加载失败" % tag)
        continue
    ss = Sampler(sa, sb)
    ts = Sampler(ta, tb)
    L("")
    L("################ %s" % tag)
    for f in ss.frames:
        L("  ---- frame %d ----" % f)
        L("    %-14s %26s   %26s" % ("骨", "源 (x, y, z)", "产物 (x, y, z)"))
        for a, b in zip(sb, tb):
            ps, pt = ss.pos(a, f), ts.pos(b, f)
            L("    %-14s (%8.1f,%8.1f,%8.1f)   (%8.1f,%8.1f,%8.1f)"
              % (a + "/" + b, ps[0], ps[1], ps[2], pt[0], pt[1], pt[2]))
L("=== DONE ===")
