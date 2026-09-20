import unreal

eal = unreal.EditorAssetLibrary
BS_PATH = "/Game/Character/Darius/Anims/BS_Darius_Locomotion"
IDLE_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"
WALK_PATH = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered"

bs = eal.load_asset(BS_PATH)
if not bs:
    unreal.log_error("Failed to load BS_Darius_Locomotion")
    raise SystemExit(1)

idle_anim = eal.load_asset(IDLE_PATH)
walk_anim = eal.load_asset(WALK_PATH)
if not idle_anim or not walk_anim:
    unreal.log_error(f"Failed to load anims: idle={idle_anim}, walk={walk_anim}")
    raise SystemExit(1)

unreal.log(f"Configuring BlendSpace: {BS_PATH}")

# Configure Axes
axes = []
a0 = unreal.BlendParameter()
a0.set_editor_property("display_name", "Speed")
a0.set_editor_property("min", 0.0)
a0.set_editor_property("max", 220.0)
a0.set_editor_property("grid_num", 4)
a0.set_editor_property("snap_to_grid", False)
axes.append(a0)

a1 = unreal.BlendParameter()
a1.set_editor_property("display_name", "Direction")
a1.set_editor_property("min", -180.0)
a1.set_editor_property("max", 180.0)
a1.set_editor_property("grid_num", 4)
a1.set_editor_property("snap_to_grid", False)
axes.append(a1)

bs.set_editor_property("blend_parameters", axes)

# Construct samples
def make_sample(anim, speed, direction, rate_scale):
    s = unreal.BlendSample()
    s.set_editor_property("animation", anim)
    s.set_editor_property("sample_value", unreal.Vector(speed, direction, 0.0))
    s.set_editor_property("rate_scale", rate_scale)
    return s

samples = [
    # Idle at Speed = 0
    make_sample(idle_anim, 0.0, 0.0, 1.0),
    make_sample(idle_anim, 0.0, 180.0, 1.0),
    make_sample(idle_anim, 0.0, -180.0, 1.0),
    
    # Natural Walk at Speed = 150 (rate 1.0 matches 148.5 cm/s stride)
    make_sample(walk_anim, 150.0, 0.0, 1.0),
    make_sample(walk_anim, 150.0, 90.0, 1.0),
    make_sample(walk_anim, 150.0, -90.0, 1.0),
    make_sample(walk_anim, 150.0, 180.0, 1.0),
    make_sample(walk_anim, 150.0, -180.0, 1.0),
    
    # Brisk Walk at Speed = 220 (rate 1.48 matches 220 cm/s stride)
    make_sample(walk_anim, 220.0, 0.0, 1.48),
    make_sample(walk_anim, 220.0, 90.0, 1.48),
    make_sample(walk_anim, 220.0, -90.0, 1.48),
    make_sample(walk_anim, 220.0, 180.0, 1.48),
    make_sample(walk_anim, 220.0, -180.0, 1.48),
]

bs.set_editor_property("sample_data", samples)
saved = eal.save_loaded_asset(bs)
unreal.log(f"Saved BS_Darius_Locomotion: {saved}")

# Verify
bs_check = eal.load_asset(BS_PATH)
axes_check = bs_check.get_editor_property("blend_parameters")
unreal.log("=== Verification Check ===")
for i, a in enumerate(axes_check):
    unreal.log(f"  Axis {i}: name={a.get_editor_property('display_name')} min={a.get_editor_property('min')} max={a.get_editor_property('max')}")

samples_check = bs_check.get_editor_property("sample_data")
unreal.log(f"  Total samples: {len(samples_check)}")
for i, s in enumerate(samples_check):
    a = s.get_editor_property("animation")
    v = s.get_editor_property("sample_value")
    rs = s.get_editor_property("rate_scale")
    unreal.log(f"    [{i:2d}] {a.get_name():<28} pos=({v.x:5.1f}, {v.y:6.1f}) rate={rs:.2f}")
