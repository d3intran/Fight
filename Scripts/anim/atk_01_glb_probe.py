"""LoL 神王攻击动画只读探针：解析 GLB，量出攻击动作的时间轴 / 手部轨迹 / 骨盆与脚部位移。

不修改任何资产，只输出 JSON + CSV 到 Docs/Attack/_intermediate/。
用途：为「普通攻击能否借用 LoL 官方上半身」提供客观数字（帧数、命中帧、是否 in-place、脚是否移动）。
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

GLB = Path(r"E:/UE/Assets/Darius_GodKing_LOL_Original/Animations_GLB/darius_skin15_all_anims.glb")
OUT = Path(r"E:/UE/Fight/Docs/Attack/_intermediate")
FPS = 30.0

# 关注的骨（按 LoL 源骨架命名）
INTEREST = [
    "Root", "Pelvis", "Spine1", "Spine2", "Neck", "Head",
    "L_Clavicle", "R_Clavicle", "L_Shoulder", "R_Shoulder",
    "L_Elbow", "R_Elbow", "L_Hand", "R_Hand",
    "L_Hip", "R_Hip", "L_KneeLower", "R_KneeLower",
    "L_Foot", "R_Foot", "L_Toe", "R_Toe",
    "Axe_Handle", "Axe_Head", "Axe_Jaw", "Weapon", "SnapWeapon", "SnapWeapon2Hand",
]
CLIPS = ["attack1", "attack2", "crit", "attack1_toidle", "attack2_toidle", "crit_toidle",
         "idle1", "run"]


def load_glb(path: Path):
    raw = path.read_bytes()
    magic, ver, total = struct.unpack_from("<III", raw, 0)
    assert magic == 0x46546C67, "not a glb"
    off = 12
    js, binc = None, None
    while off < total:
        clen, ctype = struct.unpack_from("<II", raw, off)
        chunk = raw[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            binc = chunk
        off += 8 + clen + ((4 - clen % 4) % 4 if clen % 4 else 0)
    return js, binc


CTYPE = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
         5125: ("I", 4), 5126: ("f", 4)}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_accessor(g, binc, idx):
    acc = g["accessors"][idx]
    n = NCOMP[acc["type"]]
    fmt, size = CTYPE[acc["componentType"]]
    bv = g["bufferViews"][acc["bufferView"]]
    base = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride") or (n * size)
    out = []
    for i in range(acc["count"]):
        o = base + i * stride
        out.append(struct.unpack_from("<" + fmt * n, binc, o))
    return out


# ---------- 矩阵 / 四元数工具 ----------
def quat_to_mat(q):
    x, y, z, w = q
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return [
        [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy)],
        [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx)],
        [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy)],
    ]


def m3_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def m3_v(a, v):
    return tuple(sum(a[i][k] * v[k] for k in range(3)) for i in range(3))


def trs_to_mat(t, q, s):
    R = quat_to_mat(q)
    return [[R[i][j] * s[j] for j in range(3)] for i in range(3)], t


def compose(parent, local):
    """parent=(R,t), local=(R,t) -> (R,t)"""
    PR, Pt = parent
    LR, Lt = local
    R = m3_mul(PR, LR)
    t = tuple(Pt[i] + m3_v(PR, Lt)[i] for i in range(3))
    return R, t


def lerp(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(len(a)))


def slerp(q0, q1, u):
    d = sum(q0[i] * q1[i] for i in range(4))
    if d < 0:
        q1 = tuple(-c for c in q1)
        d = -d
    if d > 0.9995:
        return lerp(q0, q1, u)
    th = math.acos(max(-1.0, min(1.0, d)))
    s = math.sin(th)
    return tuple((math.sin((1 - u) * th) * q0[i] + math.sin(u * th) * q1[i]) / s for i in range(4))


def main():
    g, binc = load_glb(GLB)
    nodes = g["nodes"]
    name2idx = {n.get("name", f"#{i}"): i for i, n in enumerate(nodes)}
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i

    print(f"[glb] nodes={len(nodes)} animations={len(g.get('animations', []))}")
    print("[glb] node names:", ", ".join(sorted(name2idx)[:80]))
    print("[glb] 关注的骨是否齐:", {b: (b in name2idx) for b in INTEREST})

    anims = {a.get("name", f"anim{i}"): a for i, a in enumerate(g.get("animations", []))}
    report = {"fps": FPS, "clips": {}}
    timeline_rows = []

    # 建立每个动画的采样器
    for cname in CLIPS:
        key = None
        for k in anims:
            if k.lower().endswith(cname.lower()) or cname.lower() in k.lower():
                key = k
                break
        if key is None:
            print(f"[skip] 找不到 clip {cname}")
            continue
        a = anims[key]
        # 采样器: (node, path) -> (times, values)
        chan = {}
        for ch in a["channels"]:
            tgt = ch["target"]
            smp = a["samplers"][ch["sampler"]]
            times = [t[0] for t in read_accessor(g, binc, smp["input"])]
            vals = read_accessor(g, binc, smp["output"])
            chan[(tgt["node"], tgt["path"])] = (times, vals)
        n_frames = max(len(v[0]) for v in chan.values())
        dur = max(v[0][-1] for v in chan.values())
        base = {}
        for i, n in enumerate(nodes):
            base[i] = (tuple(n.get("translation", (0, 0, 0))),
                       tuple(n.get("rotation", (0, 0, 0, 1))),
                       tuple(n.get("scale", (1, 1, 1))))

        # 逐帧 FK：取第 0 帧时间轴，按比例重采样到统一帧号
        def local_of(node_i, t):
            bt, br, bs = base[node_i]
            T = br
            if (node_i, "translation") in chan:
                ts, vs = chan[(node_i, "translation")]
                T = _sample_v(ts, vs, t, bt)
            R = br
            if (node_i, "rotation") in chan:
                ts, vs = chan[(node_i, "rotation")]
                R = _sample_q(ts, vs, t, br)
            S = bs
            if (node_i, "scale") in chan:
                ts, vs = chan[(node_i, "scale")]
                S = _sample_v(ts, vs, t, bs)
            return trs_to_mat(T, R, S)

        def world(node_i, t):
            acc = local_of(node_i, t)
            p = parent.get(node_i)
            while p is not None:
                acc = compose(local_of(p, t), acc)
                p = parent.get(p)
            return acc

        # 统一采样 0..dur，步长 = 1/30
        samples = []
        steps = int(round(dur * FPS)) + 1
        for fi in range(steps):
            t = fi / FPS
            row = {"frame": fi, "t": round(t, 4)}
            for b in INTEREST:
                if b not in name2idx:
                    continue
                R, P = world(name2idx[b], t)
                row[b] = [round(c, 4) for c in P]
            samples.append(row)

        def span(b, axis):
            if b not in name2idx:
                return None
            vals = [s[b][axis] for s in samples]
            return [round(min(vals), 3), round(max(vals), 3), round(max(vals) - min(vals), 3)]

        def path_len(b):
            if b not in name2idx:
                return None
            tot = 0.0
            for i in range(1, len(samples)):
                tot += math.dist(samples[i][b], samples[i - 1][b])
            return round(tot, 3)

        # ---- 武器握持分析：左手是否在斧柄轴线上；手→刃的局部偏移（socket 标定） ----
        def wm_of(node_name, t):
            return world(name2idx[node_name], t)

        def sub3(a, b):
            return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

        def dot3(a, b):
            return sum(a[i] * b[i] for i in range(3))

        def nrm3(a):
            n = math.sqrt(dot3(a, a))
            return tuple(c / n for c in a) if n > 1e-9 else (0.0, 0.0, 0.0)

        axe_axis_perp, grip_off_local, grip_off_len, hip_yaw = [], [], [], []
        for fi in range(steps):
            t = fi / FPS
            Lh = wm_of("L_Hand", t)[1]
            RhR, Rh = wm_of("R_Hand", t)
            Hh = wm_of("Axe_Handle", t)[1] if "Axe_Handle" in name2idx else None
            Ah = wm_of("Axe_Head", t)[1] if "Axe_Head" in name2idx else None
            if Hh and Ah:
                ax = nrm3(sub3(Ah, Hh))
                v = sub3(Lh, Hh)
                proj = dot3(v, ax)
                foot = tuple(Hh[i] + ax[i] * proj for i in range(3))
                axe_axis_perp.append(round(math.dist(Lh, foot), 2))
                d = sub3(Ah, Rh)
                loc = tuple(sum(RhR[k][j] * d[k] for k in range(3)) for j in range(3))
                grip_off_local.append([round(c, 1) for c in loc])
                grip_off_len.append(round(math.dist((0, 0, 0), loc), 2))
            lh = samples[fi].get("L_Hip")
            rh = samples[fi].get("R_Hip")
            if lh and rh:
                hip_yaw.append(round(math.degrees(math.atan2(rh[0] - lh[0], rh[2] - lh[2])), 1))

        # 髋轴 yaw 去卷绕（相对首帧）
        if hip_yaw:
            un = [hip_yaw[0]]
            off = 0.0
            for i in range(1, len(hip_yaw)):
                d = hip_yaw[i] - hip_yaw[i - 1]
                if d > 180:
                    off -= 360
                elif d < -180:
                    off += 360
                un.append(hip_yaw[i] + off)
            hip_yaw_rel = [round(v - un[0], 1) for v in un]
        else:
            hip_yaw_rel = []

        # 手部角速度（绕 pelvis 的半径变化 + 位移速度）→ 找峰值帧 = 挥击最快帧
        speed = []
        for i in range(1, len(samples)):
            d = math.dist(samples[i]["R_Hand"], samples[i - 1]["R_Hand"]) * FPS
            speed.append(round(d, 2))
        peak = max(range(len(speed)), key=lambda i: speed[i]) if speed else -1

        axe_speed = []
        for i in range(1, len(samples)):
            if "Axe_Head" in samples[i] and "Axe_Head" in samples[i - 1]:
                axe_speed.append(round(math.dist(samples[i]["Axe_Head"], samples[i - 1]["Axe_Head"]) * FPS, 2))
        axe_peak = max(range(len(axe_speed)), key=lambda i: axe_speed[i]) if axe_speed else -1

        lr = []
        for s in samples:
            if "L_Hand" in s and "R_Hand" in s:
                lr.append(round(math.dist(s["L_Hand"], s["R_Hand"]), 2))

        # 根骨位移分解：Y = 上（glTF 惯例），XZ = 水平
        def root_profile():
            out = []
            for s in samples:
                p = s.get("Root")
                if p is None:
                    return None
                out.append([round(p[0], 2), round(p[1], 2), round(p[2], 2)])
            return out

        rp = root_profile() or [[0, 0, 0]]
        hor = [math.hypot(p[0], p[2]) for p in rp]
        vert = [p[1] for p in rp]

        info = {
            "clip": key,
            "frames": n_frames,
            "samples": steps,
            "duration_s": round(dur, 4),
            "animated_nodes": len({k[0] for k in chan}),
            "root_vertical_range_cm": round(max(vert) - min(vert), 2),
            "root_horizontal_range_cm": round(max(hor) - min(hor), 2),
            "root_horizontal_path_cm": round(sum(
                math.dist((rp[i][0], rp[i][2]), (rp[i - 1][0], rp[i - 1][2])) for i in range(1, len(rp))), 2),
            "root_profile_xyz": rp,
            "Axe_Head_xyz_range": [span("Axe_Head", a) for a in range(3)],
            "Axe_Head_path_cm": path_len("Axe_Head"),
            "Axe_Head_speed_peak_frame": axe_peak,
            "Axe_Head_speed_peak_cm_s": axe_speed[axe_peak] if axe_peak >= 0 else None,
            "Axe_Head_speed_profile": axe_speed,
            "L_Hand_to_axe_axis_cm": axe_axis_perp,
            "L_Hand_to_axe_axis_min_cm": min(axe_axis_perp) if axe_axis_perp else None,
            "grip_hand_to_blade_local": grip_off_local,
            "grip_hand_to_blade_len_cm": grip_off_len,
            "hip_yaw_rel_deg": hip_yaw_rel,
            "hip_yaw_end_rel_deg": hip_yaw_rel[-1] if hip_yaw_rel else None,
            "LR_hand_dist_profile_cm": lr,
            "LR_hand_dist_min_cm": min(lr) if lr else None,
            "LR_hand_dist_max_cm": max(lr) if lr else None,
            "pelvis_xyz_range": [span("Pelvis", a) for a in range(3)],
            "root_xyz_range": [span("Root", a) for a in range(3)],
            "R_Hand_xyz_range": [span("R_Hand", a) for a in range(3)],
            "L_Hand_xyz_range": [span("L_Hand", a) for a in range(3)],
            "R_Hand_path_cm": path_len("R_Hand"),
            "L_Hand_path_cm": path_len("L_Hand"),
            "R_Foot_path_cm": path_len("R_Foot"),
            "L_Foot_path_cm": path_len("L_Foot"),
            "R_Foot_xyz_range": [span("R_Foot", a) for a in range(3)],
            "L_Foot_xyz_range": [span("L_Foot", a) for a in range(3)],
            "head_xyz_range": [span("Head", a) for a in range(3)],
            "R_Hand_speed_peak_frame": peak,
            "R_Hand_speed_peak_cm_s": speed[peak] if peak >= 0 else None,
            "R_Hand_speed_profile": speed,
            "L_Hand_to_R_Hand_min_cm": round(min(
                math.dist(s["L_Hand"], s["R_Hand"]) for s in samples
                if "L_Hand" in s and "R_Hand" in s), 3),
            "L_Hand_to_R_Hand_max_cm": round(max(
                math.dist(s["L_Hand"], s["R_Hand"]) for s in samples
                if "L_Hand" in s and "R_Hand" in s), 3),
        }
        report["clips"][cname] = info
        print(f"\n=== {cname} ({key}) ===")
        for k, v in info.items():
            if k in ("R_Hand_speed_profile", "Axe_Head_speed_profile", "root_profile_xyz", "LR_hand_dist_profile_cm"):
                continue
            print(f"  {k}: {v}")

        for s in samples:
            timeline_rows.append({"clip": cname, **s})

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "lol_attack_probe.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    with (OUT / "lol_attack_timeline.csv").open("w", encoding="utf-8") as f:
        cols = ["clip", "frame", "t"] + INTEREST
        f.write(",".join(cols) + "\n")
        for r in timeline_rows:
            f.write(",".join(
                str(r.get(c, "")) if not isinstance(r.get(c), list) else "|".join(str(x) for x in r[c])
                for c in cols) + "\n")
    print(f"\n[saved] {OUT / 'lol_attack_probe.json'}")
    print(f"[saved] {OUT / 'lol_attack_timeline.csv'}")


def _sample_v(times, vals, t, default):
    if t <= times[0]:
        return vals[0]
    if t >= times[-1]:
        return vals[-1]
    lo = 0
    hi = len(times) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if times[mid] <= t:
            lo = mid
        else:
            hi = mid
    u = (t - times[lo]) / (times[hi] - times[lo]) if times[hi] > times[lo] else 0.0
    return lerp(vals[lo], vals[hi], u)


def _sample_q(times, vals, t, default):
    if t <= times[0]:
        return vals[0]
    if t >= times[-1]:
        return vals[-1]
    lo = 0
    hi = len(times) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if times[mid] <= t:
            lo = mid
        else:
            hi = mid
    u = (t - times[lo]) / (times[hi] - times[lo]) if times[hi] > times[lo] else 0.0
    return slerp(vals[lo], vals[hi], u)


if __name__ == "__main__":
    sys.exit(main())
