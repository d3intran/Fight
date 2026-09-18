import sys, time
sys.path.append('E:/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python')
import remote_execution

client = remote_execution.RemoteExecution()
client.start()
time.sleep(0.5)
node = client.remote_nodes[0]
client.open_command_connection(node['node_id'])
time.sleep(0.3)

test_script = '''
import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor_asset_lib = unreal.EditorAssetLibrary
mat_lib = unreal.MaterialEditingLibrary

mat_path = '/Game/Material/M_TrainingGround_Grid'
material = editor_asset_lib.load_asset(mat_path)
mat_lib.delete_all_material_expressions(material)

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
// Panel: target sRGB [170, 178, 187]
float3 col_panel = float3(0.24, 0.28, 0.33);

// Border frame: target sRGB [145, 153, 162]
float3 col_border = float3(0.16, 0.19, 0.23);

// Groove: target sRGB [105, 115, 125]
float3 col_groove = float3(0.06, 0.08, 0.10);

// Outer groove (0 to 6cm)
float outer_groove = 1.0 - saturate(d / 5.0);

// Border frame (5 to 26cm)
float in_border = saturate((d - 5.0) / 2.0) * (1.0 - saturate((d - 25.0) / 2.0));

// Inner groove (25 to 29cm)
float inner_groove = saturate((d - 25.0) / 1.5) * (1.0 - saturate((d - 28.5) / 1.5));

// Inner panel (d > 28.5cm)
float in_panel = saturate((d - 28.5) / 2.0);

// Fine triangular subgrid (spacing 35cm, line 1.5cm)
float sub_s = 35.0;
float l1 = abs(fmod(abs(local_p.y), sub_s) - sub_s * 0.5);
float l2 = abs(fmod(abs(local_p.y * 0.5 + local_p.x * 0.8660254), sub_s) - sub_s * 0.5);
float l3 = abs(fmod(abs(local_p.y * 0.5 - local_p.x * 0.8660254), sub_s) - sub_s * 0.5);
float min_sub = min(l1, min(l2, l3));
float sub_grid = (1.0 - saturate(min_sub / 1.2)) * in_panel;

// Composite
float3 col = col_panel;
col = lerp(col, col_border, in_border);
col = lerp(col, col_groove, outer_groove);
col = lerp(col, col_groove, inner_groove);
col -= sub_grid * 0.045;

return col;
"""

custom_node = mat_lib.create_material_expression(material, unreal.MaterialExpressionCustom, -400, 0)
custom_node.set_editor_property('code', hlsl_code)
custom_node.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)

inp = unreal.CustomInput()
inp.set_editor_property('input_name', 'Pos')
custom_node.set_editor_property('inputs', [inp])

wp = mat_lib.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -700, 0)
mask_xy = mat_lib.create_material_expression(material, unreal.MaterialExpressionComponentMask, -550, 0)
mask_xy.set_editor_property('r', True)
mask_xy.set_editor_property('g', True)
mask_xy.set_editor_property('b', False)
mask_xy.set_editor_property('a', False)
mat_lib.connect_material_expressions(wp, '', mask_xy, '')
mat_lib.connect_material_expressions(mask_xy, '', custom_node, 'Pos')

mat_lib.connect_material_property(custom_node, '', unreal.MaterialProperty.MP_BASE_COLOR)

roughness = mat_lib.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 200)
roughness.set_editor_property('r', 0.35)
mat_lib.connect_material_property(roughness, '', unreal.MaterialProperty.MP_ROUGHNESS)

specular = mat_lib.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 300)
specular.set_editor_property('r', 0.5)
mat_lib.connect_material_property(specular, '', unreal.MaterialProperty.MP_SPECULAR)

metallic = mat_lib.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 400)
metallic.set_editor_property('r', 0.02)
mat_lib.connect_material_property(metallic, '', unreal.MaterialProperty.MP_METALLIC)

zero_c = mat_lib.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 500)
zero_c.set_editor_property('r', 0.0)
mat_lib.connect_material_property(zero_c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)

mat_lib.recompile_material(material)
editor_asset_lib.save_asset(mat_path)

# Adjust lights and fog
actors = actor_subsystem.get_all_level_actors()
for a in actors:
    label = a.get_actor_label()
    if 'KeyLight' in label:
        comp = a.get_component_by_class(unreal.LightComponentBase)
        comp.set_editor_property('intensity', 1.5)
    elif 'Softbox' in label:
        comp = a.get_component_by_class(unreal.LightComponentBase)
        comp.set_editor_property('intensity', 2500.0)
    elif 'SkyLight' in label:
        comp = a.get_component_by_class(unreal.LightComponentBase)
        comp.set_editor_property('intensity', 0.5)
        comp.set_light_color(unreal.LinearColor(0.65, 0.72, 0.80, 1.0))
    elif 'Fog' in label:
        fcomp = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
        fcomp.set_editor_property('fog_density', 0.002)
        fcomp.set_editor_property('fog_height_falloff', 0.00005)
        fcomp.set_editor_property('fog_inscattering_luminance', unreal.LinearColor(0.24, 0.28, 0.33, 1.0))
        fcomp.set_editor_property('start_distance', 1500.0)

# Capture with AutomationLibrary
task = unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, 'E:/UE/Fight/Saved/Screenshots/sb_calibrated.png', force_game_view=True)
print('Done calibrated update')
'''

res = client.run_command(test_script, exec_mode=remote_execution.MODE_EXEC_FILE)
print('RES:', res.get('success'))
for item in res.get('output', []):
    print(item['output'].strip())
client.stop()
