import unreal

def build():
    unreal.log("==================================================")
    unreal.log(">> [Stellar Blade Arena] 1:1 Recreation Setup (Calibrated)...")
    unreal.log("==================================================")

    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    target_level = "/Game/Level/Lv-FIght"
    try:
        level_subsystem.load_level(target_level)
    except Exception as e:
        unreal.log_warning(f">> Note loading level: {e}")

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    editor_asset_lib = unreal.EditorAssetLibrary
    mat_lib = unreal.MaterialEditingLibrary

    # 1. Clean up previous actors
    all_actors = actor_subsystem.get_all_level_actors()
    for actor in all_actors:
        label = actor.get_actor_label()
        if label.startswith("TrainingGround_"):
            unreal.log(f">> Removing old actor: {label}")
            actor_subsystem.destroy_actor(actor)

    # 2. Build Material M_TrainingGround_Grid for 1:1 Stellar Blade Hexagon Floor
    mat_path = "/Game/Material/M_TrainingGround_Grid"
    mat_pkg = "/Game/Material"
    mat_name = "M_TrainingGround_Grid"

    if not editor_asset_lib.does_directory_exist(mat_pkg):
        editor_asset_lib.make_directory(mat_pkg)

    if editor_asset_lib.does_asset_exist(mat_path):
        material = editor_asset_lib.load_asset(mat_path)
    else:
        mat_factory = unreal.MaterialFactoryNew()
        material = asset_tools.create_asset(mat_name, mat_pkg, unreal.Material, mat_factory)

    mat_lib.delete_all_material_expressions(material)

    try:
        # HLSL Custom Node for 1:1 Stellar Blade Hexagonal Tiling
        hlsl_code = """
float2 p = Pos;
float R = 200.0;

float q = (0.577350269 * p.x - 0.333333333 * p.y) / R;
float r = (0.666666667 * p.y) / R;

float xc = q;
float zc = r;
float yc = -q - r;

float rx = round(xc);
float ry = round(yc);
float rz = round(zc);

float xd = abs(rx - xc);
float yd = abs(ry - yc);
float zd = abs(rz - zc);

if (xd > yd && xd > zd) {
    rx = -ry - rz;
} else if (yd > zd) {
    ry = -rx - rz;
} else {
    rz = -rx - ry;
}

float2 center = float2(
    R * (1.7320508 * rx + 0.8660254 * rz),
    R * (1.5 * rz)
);

float2 local_p = p - center;

float alx = abs(local_p.x);
float aly = abs(local_p.y);
float d = (R * 0.8660254) - max(alx * 0.5 + aly * 0.8660254, alx);

// Calibrated Linear colors for exact sRGB match with reference:
// Panel: target sRGB [167, 175, 185]
float3 col_panel = float3(0.17, 0.20, 0.24);

// Border frame: target sRGB [140, 148, 158]
float3 col_border = float3(0.11, 0.13, 0.16);

// Groove: target sRGB [105, 115, 125]
float3 col_groove = float3(0.035, 0.045, 0.06);

// Outer groove (0 to 5.5cm)
float outer_groove = 1.0 - saturate(d / 5.5);

// Border frame (5.5 to 26cm)
float in_border = saturate((d - 5.5) / 2.0) * (1.0 - saturate((d - 25.5) / 2.0));

// Inner groove (25.5 to 29.5cm)
float inner_groove = saturate((d - 25.5) / 1.5) * (1.0 - saturate((d - 29.0) / 1.5));

// Inner panel (d > 29.0cm)
float in_panel = saturate((d - 29.0) / 2.0);

// Fine triangular subgrid (spacing 35cm, line 1.5cm)
float sub_s = 35.0;
float l1 = abs(fmod(abs(local_p.y), sub_s) - sub_s * 0.5);
float l2 = abs(fmod(abs(local_p.y * 0.5 + local_p.x * 0.8660254), sub_s) - sub_s * 0.5);
float l3 = abs(fmod(abs(local_p.y * 0.5 - local_p.x * 0.8660254), sub_s) - sub_s * 0.5);
float min_sub = min(l1, min(l2, l3));
float sub_grid = (1.0 - saturate(min_sub / 1.2)) * in_panel;

// Composite BaseColor
float3 col = col_panel;
col = lerp(col, col_border, in_border);
col = lerp(col, col_groove, outer_groove);
col = lerp(col, col_groove, inner_groove);
col -= sub_grid * 0.035;

return col;
"""

        custom_node = mat_lib.create_material_expression(material, unreal.MaterialExpressionCustom, -400, 0)
        custom_node.set_editor_property("code", hlsl_code)
        custom_node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)

        inp = unreal.CustomInput()
        inp.set_editor_property("input_name", "Pos")
        custom_node.set_editor_property("inputs", [inp])

        wp = mat_lib.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -700, 0)
        mask_xy = mat_lib.create_material_expression(material, unreal.MaterialExpressionComponentMask, -550, 0)
        mask_xy.set_editor_property("r", True)
        mask_xy.set_editor_property("g", True)
        mask_xy.set_editor_property("b", False)
        mask_xy.set_editor_property("a", False)
        mat_lib.connect_material_expressions(wp, "", mask_xy, "")
        mat_lib.connect_material_expressions(mask_xy, "", custom_node, "Pos")

        # Connect BaseColor
        mat_lib.connect_material_property(custom_node, "", unreal.MaterialProperty.MP_BASE_COLOR)

        # Roughness (0.35 clean matte composite floor)
        roughness = mat_lib.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 200)
        roughness.set_editor_property("r", 0.35)
        mat_lib.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)

        # Specular (0.5)
        specular = mat_lib.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 300)
        specular.set_editor_property("r", 0.5)
        mat_lib.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)

        # Metallic (0.02)
        metallic = mat_lib.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 400)
        metallic.set_editor_property("r", 0.02)
        mat_lib.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)

        # Emissive is strictly 0.0 (no glowing neon lines)
        zero_c = mat_lib.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 500)
        zero_c.set_editor_property("r", 0.0)
        mat_lib.connect_material_property(zero_c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

        mat_lib.recompile_material(material)
        editor_asset_lib.save_asset(mat_path)
        unreal.log(">> [M_TrainingGround_Grid] Stellar Blade 1:1 Hexagon Material compiled and saved successfully!")
    except Exception as e:
        unreal.log_error(f">> Failed generating material: {e}")

    # 3. Floor Actor (200m x 200m)
    plane_mesh = editor_asset_lib.load_asset("/Engine/BasicShapes/Plane.Plane")
    floor_actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    floor_actor.set_actor_label("TrainingGround_Floor")
    floor_actor.set_actor_location(unreal.Vector(0, 0, 0), False, False)
    mesh_comp = floor_actor.static_mesh_component
    mesh_comp.set_static_mesh(plane_mesh)
    mesh_comp.set_world_scale3d(unreal.Vector(200.0, 200.0, 1.0))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material:
        mesh_comp.set_material(0, material)
    unreal.log(">> Spawned TrainingGround_Floor.")

    # 4. Studio Directional Light (Soft diffused overhead key light)
    dir_light_actor = actor_subsystem.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 2000), unreal.Rotator(pitch=-75.0, yaw=30.0, roll=0.0))
    dir_light_actor.set_actor_label("TrainingGround_KeyLight")
    dir_light_comp = dir_light_actor.light_component
    dir_light_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    dir_light_comp.set_intensity(1.5) # Soft 1.5 Lux studio key
    try:
        dir_light_comp.set_temperature(6500.0)
        dir_light_comp.set_use_temperature(True)
    except Exception:
        pass
    dir_light_comp.set_cast_shadows(True)
    unreal.log(">> Spawned TrainingGround_KeyLight.")

    # 5. Studio Softbox (Center Rect Light)
    rect_actor = actor_subsystem.spawn_actor_from_class(unreal.RectLight, unreal.Vector(0, 0, 2200), unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0))
    rect_actor.set_actor_label("TrainingGround_Softbox")
    rect_comp = rect_actor.rect_light_component
    rect_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    rect_comp.set_source_width(4000.0)
    rect_comp.set_source_height(4000.0)
    rect_comp.set_attenuation_radius(12000.0)
    rect_comp.set_intensity(2500.0) # Soft balanced fill
    try:
        rect_comp.set_temperature(6200.0)
        rect_comp.set_use_temperature(True)
    except Exception:
        pass
    rect_comp.set_cast_shadows(True)
    unreal.log(">> Spawned TrainingGround_Softbox.")

    # 6. SkyLight (Luminous studio ambient fill)
    sky_actor = actor_subsystem.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 500), unreal.Rotator(0, 0, 0))
    sky_actor.set_actor_label("TrainingGround_SkyLight")
    sky_comp = sky_actor.light_component
    sky_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky_comp.set_real_time_capture(False)
    sky_comp.set_intensity(0.5)
    sky_comp.set_light_color(unreal.LinearColor(0.65, 0.72, 0.80, 1.0))
    sky_comp.set_cast_shadows(False)
    unreal.log(">> Spawned TrainingGround_SkyLight.")

    # 7. Exponential Height Fog (Infinite misty grey studio horizon - 1:1 matching reference)
    fog_actor = actor_subsystem.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    fog_actor.set_actor_label("TrainingGround_Fog")
    fog_comp = fog_actor.get_component_by_class(unreal.ExponentialHeightFogComponent)
    fog_comp.set_editor_property("fog_density", 0.002)
    fog_comp.set_editor_property("fog_height_falloff", 0.00005) # Infinite vertical coverage
    fog_comp.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.18, 0.22, 0.26, 1.0))
    fog_comp.set_editor_property("start_distance", 1500.0) # Foreground clear, dissolves at 30m~60m
    unreal.log(">> Spawned TrainingGround_Fog.")

    # 8. Post Process Volume (Locked exposure & subtle bloom)
    pp_actor = actor_subsystem.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, -5000), unreal.Rotator(0, 0, 0))
    pp_actor.set_actor_label("TrainingGround_PostProcess")
    pp_actor.unbound = True
    settings = pp_actor.get_editor_property("settings")
    settings.set_editor_property("override_bloom_intensity", True)
    settings.set_editor_property("bloom_intensity", 0.2)
    settings.set_editor_property("override_vignette_intensity", True)
    settings.set_editor_property("vignette_intensity", 0.1)
    pp_actor.set_editor_property("settings", settings)
    unreal.log(">> Spawned TrainingGround_PostProcess.")

    # 9. Center Test Dummy / Probe (to visualize character lighting)
    probe_mesh = editor_asset_lib.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
    probe_actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 100), unreal.Rotator(0, 0, 0))
    probe_actor.set_actor_label("TrainingGround_Probe")
    p_comp = probe_actor.static_mesh_component
    p_comp.set_static_mesh(probe_mesh)
    p_comp.set_world_scale3d(unreal.Vector(0.8, 0.8, 2.0))
    p_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    unreal.log(">> Spawned TrainingGround_Probe at arena center.")

    # 10. Viewport Camera to third-person combat perspective
    actor_subsystem.set_selected_level_actors([])
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    cam_loc = unreal.Vector(-950.0, 0.0, 260.0)
    cam_rot = unreal.Rotator(pitch=-15.0, yaw=0.0, roll=0.0)
    ues.set_level_viewport_camera_info(cam_loc, cam_rot)

    # Clean display
    unreal.SystemLibrary.execute_console_command(None, "showflag.Billboard 0")
    unreal.SystemLibrary.execute_console_command(None, "showflag.Selection 0")
    unreal.SystemLibrary.execute_console_command(None, "HighResShot 1")

    # 11. Save Level
    level_subsystem.save_current_level()
    unreal.log("==================================================")
    unreal.log(">> [Stellar Blade Arena] 1:1 Recreation Finished Successfully!")
    unreal.log("==================================================")

if __name__ == "__main__":
    build()
