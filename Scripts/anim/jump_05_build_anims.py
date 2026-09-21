import math
import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

IDLE_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"
JUMP_START_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeJump_Start"
JUMP_LOOP_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeJump_Loop"
JUMP_LAND_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeJump_Land"

# --- Math utilities ---
def qconj(q):
    return (-q[0], -q[1], -q[2], q[3])

def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)

def qrot(q, v):
    x, y, z, w = q
    m = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))

def qaxis(axis, deg):
    a = math.radians(deg) * 0.5
    s = math.sin(a)
    return (axis[0] * s, axis[1] * s, axis[2] * s, math.cos(a))

def qnorm(q):
    n = math.sqrt(sum(c * c for c in q))
    return tuple(c / n for c in q) if n > 1e-12 else (0.0, 0.0, 0.0, 1.0)

def vlerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

# --- Load idle source ---
idle = eal.load_asset(IDLE_PATH)
if idle is None:
    unreal.log_error(f"Failed to load idle source: {IDLE_PATH}")
    raise SystemExit(1)

model_iface = idle.controller.get_model_interface()
all_tracks = [str(n) for n in model_iface.get_bone_track_names()]
unreal.log(f"Loaded {IDLE_PATH}, total tracks: {len(all_tracks)}")

# Read base pose (frame 0) for all bones
idle_names = [unreal.Name(n) for n in all_tracks]
base_poses_raw = AL.get_bone_poses_for_frame(idle, idle_names, 0, False)
base_map = {}
for n, p in zip(all_tracks, base_poses_raw):
    base_map[n] = (
        (p.translation.x, p.translation.y, p.translation.z),
        (p.rotation.x, p.rotation.y, p.rotation.z, p.rotation.w),
        (p.scale3d.x, p.scale3d.y, p.scale3d.z)
    )

# Hierarchy mapping for FK
parents = {}
chains = {}
for b in all_tracks:
    rc = [str(x) for x in AL.find_bone_path_to_root(idle, b)]
    parents[b] = rc[1] if len(rc) > 1 else None
    chains[b] = rc[::-1]

# FK evaluator on custom track dictionary
def eval_fk(track_dict, fi, bone):
    P, Q, S = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
    for bn in chains.get(bone, []):
        tr = track_dict.get(bn)
        if tr is None or not tr[0]:
            continue
        t, q, s = tr[0][fi], tr[1][fi], tr[2][fi]
        off = qrot(Q, (t[0] * S[0], t[1] * S[1], t[2] * S[2]))
        P = (P[0] + off[0], P[1] + off[1], P[2] + off[2])
        Q = qmul(Q, q)
        S = (S[0] * s[0], S[1] * s[1], S[2] * s[2])
    return P, Q, S

# Helper to rotate a bone around character right axis (0, 1, 0)
def rotate_around_right(track_dict, fi, bone, deg):
    if abs(deg) < 1e-4:
        return
    par = parents.get(bone)
    if par:
        _, pq, _ = eval_fk(track_dict, fi, par)
    else:
        pq = (0.0, 0.0, 0.0, 1.0)
    # Character right axis is (0, 1, 0) in component space
    right_local = qrot(qconj(pq), (0.0, 1.0, 0.0))
    dR = qaxis(right_local, deg)
    q_orig = track_dict[bone][1][fi]
    q_new = qnorm(qmul(dR, q_orig))
    track_dict[bone][1][fi] = q_new

def build_anim(target_path, n_frames, curve_fn):
    unreal.log(f"\n=== Building {target_path} ({n_frames} frames) ===")
    if not eal.does_asset_exist(target_path):
        anim = eal.duplicate_asset(IDLE_PATH, target_path)
    else:
        anim = eal.load_asset(target_path)
    
    ctrl = anim.controller
    ctrl.set_number_of_frames(unreal.FrameNumber(n_frames), False)
    n_keys = n_frames + 1
    
    # Initialize track dictionary with duplicated base poses
    track_dict = {}
    for b in all_tracks:
        bp = base_map[b]
        track_dict[b] = (
            [bp[0]] * n_keys,
            [bp[1]] * n_keys,
            [bp[2]] * n_keys
        )
    
    # Apply motion curve for each frame
    for fi in range(n_keys):
        t_norm = fi / float(n_frames)
        curve_fn(track_dict, fi, t_norm, n_keys)
        
    # Recalculate weapon_jnt so it locks to weapon_jnt_r
    if "weapon_jnt" in track_dict and "weapon_jnt_r" in track_dict:
        wj_pos, wj_rot, wj_scl = [], [], []
        par_wj = parents.get("weapon_jnt")
        for fi in range(n_keys):
            cr = eval_fk(track_dict, fi, "weapon_jnt_r")
            cp = eval_fk(track_dict, fi, par_wj)
            Qi = qconj(cp[1])
            dt = tuple(cr[0][k] - cp[0][k] for k in range(3))
            lr = qrot(Qi, dt)
            wj_pos.append(tuple(lr[k] / cp[2][k] if abs(cp[2][k]) > 1e-9 else lr[k] for k in range(3)))
            wj_rot.append(qnorm(qmul(Qi, cr[1])))
            wj_scl.append(tuple(cr[2][k] / cp[2][k] if abs(cp[2][k]) > 1e-9 else 1.0 for k in range(3)))
        track_dict["weapon_jnt"] = (wj_pos, wj_rot, wj_scl)
        
    # Write tracks to controller
    written = 0
    for b in all_tracks:
        op, orr, os_ = track_dict[b]
        t_vecs = [unreal.Vector(*v) for v in op]
        q_quats = [unreal.Quat(v[0], v[1], v[2], v[3]) for v in orr]
        s_vecs = [unreal.Vector(*v) for v in os_]
        if ctrl.set_bone_track_keys(unreal.Name(b), t_vecs, q_quats, s_vecs, False):
            written += 1
            
    unreal.log(f"Written {written}/{len(all_tracks)} tracks.")
    saved = eal.save_asset(target_path)
    unreal.log(f"Saved: {saved}")
    
    # Verify pelvis CS height range
    z_vals = []
    for fi in range(n_keys):
        p, _, _ = eval_fk(track_dict, fi, "pelvis")
        z_vals.append(p[2])
    unreal.log(f"Pelvis CS Z range: [{min(z_vals):.1f} .. {max(z_vals):.1f}] cm")

# --- Curve functions ---

def curve_jump_start(td, fi, u, n_keys):
    # u in [0, 1] over 12 frames (0.4s)
    # 0.0 -> 0.33: Anticipation squat (crouch)
    # 0.33 -> 0.67: Explosive launch push-off
    # 0.67 -> 1.00: Airborne tuck entry
    base_pelvis_t = base_map["pelvis"][0]
    
    if u < 0.35:
        # Anticipation crouch
        k = math.sin((u / 0.35) * math.pi * 0.5) # 0 -> 1
        d_pelvis_y = 0.08 * k    # lowers pelvis by ~8cm
        thigh_bend = -18.0 * k   # hip flexion
        calf_bend = 28.0 * k     # knee flexion
        foot_bend = -10.0 * k    # ankle dorsiflexion
        spine_tilt = -4.0 * k    # forward lean
    elif u < 0.70:
        # Push off
        v = (u - 0.35) / 0.35    # 0 -> 1
        d_pelvis_y = 0.08 * (1.0 - v) - 0.04 * v # dips to +4cm launch
        thigh_bend = -18.0 * (1.0 - v) + 5.0 * v
        calf_bend = 28.0 * (1.0 - v) - 5.0 * v
        foot_bend = -10.0 * (1.0 - v) + 15.0 * v # plantarflexion (point toes)
        spine_tilt = -4.0 * (1.0 - v)
    else:
        # Airborne tuck
        w = (u - 0.70) / 0.30    # 0 -> 1
        d_pelvis_y = -0.04 * (1.0 - w) - 0.05 * w # tuck at +5cm
        thigh_bend = 5.0 * (1.0 - w) - 14.0 * w
        calf_bend = -5.0 * (1.0 - w) + 22.0 * w
        foot_bend = 15.0 * (1.0 - w) - 10.0 * w
        spine_tilt = -4.0 * w
        
    td["pelvis"][0][fi] = (base_pelvis_t[0], base_pelvis_t[1] + d_pelvis_y, base_pelvis_t[2])
    rotate_around_right(td, fi, "thigh_l", thigh_bend)
    rotate_around_right(td, fi, "thigh_r", thigh_bend * 0.9)
    rotate_around_right(td, fi, "calf_l", calf_bend)
    rotate_around_right(td, fi, "calf_r", calf_bend * 0.9)
    rotate_around_right(td, fi, "foot_l", foot_bend)
    rotate_around_right(td, fi, "foot_r", foot_bend * 0.9)
    rotate_around_right(td, fi, "spine_01", spine_tilt)

def curve_jump_loop(td, fi, u, n_keys):
    # Airborne combat tuck with subtle looping breath/wind sway
    base_pelvis_t = base_map["pelvis"][0]
    sway = math.sin(u * 2.0 * math.pi)
    
    d_pelvis_y = -0.05 + 0.005 * sway
    thigh_bend = -14.0 + 1.0 * sway
    calf_bend = 22.0 - 1.5 * sway
    foot_bend = -10.0 + 1.0 * sway
    spine_tilt = -4.5 + 0.5 * sway
    
    td["pelvis"][0][fi] = (base_pelvis_t[0], base_pelvis_t[1] + d_pelvis_y, base_pelvis_t[2])
    rotate_around_right(td, fi, "thigh_l", thigh_bend)
    rotate_around_right(td, fi, "thigh_r", thigh_bend * 0.92)
    rotate_around_right(td, fi, "calf_l", calf_bend)
    rotate_around_right(td, fi, "calf_r", calf_bend * 0.92)
    rotate_around_right(td, fi, "foot_l", foot_bend)
    rotate_around_right(td, fi, "foot_r", foot_bend * 0.92)
    rotate_around_right(td, fi, "spine_01", spine_tilt)

def curve_jump_land(td, fi, u, n_keys):
    # 0.0 -> 0.25: Contact touch-down
    # 0.25 -> 0.50: Deep compression absorption
    # 0.50 -> 1.00: Spring rebound & settle to Idle
    base_pelvis_t = base_map["pelvis"][0]
    
    if u < 0.35:
        # Deep compression
        k = math.sin((u / 0.35) * math.pi * 0.5) # 0 -> 1
        d_pelvis_y = 0.12 * k    # lowers pelvis by ~12cm
        thigh_bend = -22.0 * k
        calf_bend = 32.0 * k
        foot_bend = -12.0 * k
        spine_tilt = -7.0 * k
    else:
        # Rebound to stand
        v = (u - 0.35) / 0.65    # 0 -> 1
        decay = math.cos(v * math.pi * 0.5) # 1 -> 0
        d_pelvis_y = 0.12 * decay
        thigh_bend = -22.0 * decay
        calf_bend = 32.0 * decay
        foot_bend = -12.0 * decay
        spine_tilt = -7.0 * decay
        
    td["pelvis"][0][fi] = (base_pelvis_t[0], base_pelvis_t[1] + d_pelvis_y, base_pelvis_t[2])
    rotate_around_right(td, fi, "thigh_l", thigh_bend)
    rotate_around_right(td, fi, "thigh_r", thigh_bend * 0.95)
    rotate_around_right(td, fi, "calf_l", calf_bend)
    rotate_around_right(td, fi, "calf_r", calf_bend * 0.95)
    rotate_around_right(td, fi, "foot_l", foot_bend)
    rotate_around_right(td, fi, "foot_r", foot_bend * 0.95)
    rotate_around_right(td, fi, "spine_01", spine_tilt)

# Build all three animations
build_anim(JUMP_START_PATH, 12, curve_jump_start)
build_anim(JUMP_LOOP_PATH, 16, curve_jump_loop)
build_anim(JUMP_LAND_PATH, 14, curve_jump_land)

unreal.log("\n=== ALL JUMP ANIMATIONS BUILT SUCCESSFULLY ===")
