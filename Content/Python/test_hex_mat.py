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
mat_lib = unreal.MaterialEditingLibrary
editor_asset_lib = unreal.EditorAssetLibrary

mat = editor_asset_lib.load_asset('/Game/Material/M_TrainingGround_Grid')
mat_lib.delete_all_material_expressions(mat)

code = """
float R = 220.0;
float2 p = Pos;

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

return d;
"""

custom_node = mat_lib.create_material_expression(mat, unreal.MaterialExpressionCustom, -400, 0)
custom_node.set_editor_property('code', code)
custom_node.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT1)

inp = unreal.CustomInput()
inp.set_editor_property('input_name', 'Pos')
custom_node.set_editor_property('inputs', [inp])

wp = mat_lib.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -600, 0)
mask_xy = mat_lib.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -500, 0)
mask_xy.set_editor_property('r', True)
mask_xy.set_editor_property('g', True)
mask_xy.set_editor_property('b', False)
mask_xy.set_editor_property('a', False)
mat_lib.connect_material_expressions(wp, '', mask_xy, '')
mat_lib.connect_material_expressions(mask_xy, '', custom_node, 'Pos')

div_c = mat_lib.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 100)
div_c.set_editor_property('r', 200.0)
div_n = mat_lib.create_material_expression(mat, unreal.MaterialExpressionDivide, -200, 0)
mat_lib.connect_material_expressions(custom_node, '', div_n, 'A')
mat_lib.connect_material_expressions(div_c, '', div_n, 'B')

mat_lib.connect_material_property(div_n, '', unreal.MaterialProperty.MP_BASE_COLOR)

mat_lib.recompile_material(mat)
editor_asset_lib.save_asset('/Game/Material/M_TrainingGround_Grid')
print('Hexagonal grid Custom node compiled successfully!')
'''

res = client.run_command(test_script, exec_mode=remote_execution.MODE_EXEC_FILE)
print('RES:', res.get('success'))
for item in res.get('output', []):
    print(item['output'].strip())
client.stop()
