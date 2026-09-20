import json
import math
import os
import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

MERGED = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered"
UP_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo"
LOW_PATH = "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"
OUT = "E:/UE/Fight/Saved/Preview/AxwExport"
os.makedirs(OUT, exist_ok=True)

anim = eal.load_asset(MERGED)
if not anim:
    unreal.log_error("load fail")
    raise SystemExit(1)

unreal.log("Exporter available = %s" % hasattr(unreal, "Exporter"))
fn = os.path.join(OUT, "A_Darius_AxeWalk_Layered.fbx")
task = unreal.AssetExportTask()
task.set_editor_property("object", anim)
task.set_editor_property("filename", fn)
task.set_editor_property("automated", True)
task.set_editor_property("prompt", False)
task.set_editor_property("replace_identical", True)
ok = False
try:
    ok = unreal.Exporter.run_asset_export_task(task)
except Exception as ex:
    unreal.log_error("export ERR %s" % ex)
unreal.log("FBX export ok=%s exists=%s size=%s" % (
    ok, os.path.exists(fn), os.path.getsize(fn) if os.path.exists(fn) else -1))

# ---------------- 导出逐帧关键骨位置（供离线画图 / 复核） ----------------
BONES = ["root", "pelvis", "spine_03", "neck_01", "head", "clavicle_l", "clavicle_r",
         "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r",
         "thigh_l", "calf_l", "foot_l", "ball_l", "toe_l",
         "thigh_r", "calf_r", "foot_r", "ball_r", "toe_r",
         "weapon_jnt", "weapon_jnt_r"]


def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def dump(path, tag):
    a = eal.load_asset(path)
    names = [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]
    nf = int(AL.get_num_frames(a))
    chains = {}
    for b in BONES:
        if b in names:
            chains[b] = [str(x) for x in AL.find_bone_path_to_root(a, b)][::-1]
    lc = {n.lower(): n for n in names}
    frames = []
    for f in range(nf + 1):
        poses = AL.get_bone_poses_for_frame(a, [unreal.Name(b) for b in names], f, False)
        loc = {}
        for i, b in enumerate(names):
            t = poses[i]
            loc[b] = ((t.translation.x, t.translation.y, t.translation.z),
                      (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
                      (t.scale3d.x, t.scale3d.y, t.scale3d.z))
        out = {}
        for b, chain in chains.items():
            P, Q, S = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
            for bn in chain:
                key = bn if bn in loc else lc.get(bn.lower())
                tr = loc.get(key) if key else None
                if tr is None:
                    continue
                t, q, s = tr
                off = mv(qmat(Q), (t[0] * S[0], t[1] * S[1], t[2] * S[2]))
                P = (P[0] + off[0], P[1] + off[1], P[2] + off[2])
                Q = qmul(Q, q)
                S = (S[0] * s[0], S[1] * s[1], S[2] * s[2])
            out[b] = [round(v, 3) for v in P]
        frames.append(out)
    p = os.path.join(OUT, "bones_%s.json" % tag)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump({"frames": frames, "fps": 30}, fh)
    unreal.log("dumped %d frames -> %s" % (len(frames), p))


dump(MERGED, "merged")
dump(LOW_PATH, "low")
dump(UP_PATH, "up")
unreal.log("### DONE")
