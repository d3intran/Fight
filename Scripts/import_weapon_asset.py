"""
=============================================================================
 战斧资产导入与手部插槽挂载流水线 (import_weapon_asset.py)
 -----------------------------------------------------------------------------
 作用：
 1. 将 Blender 导出的独立战斧 FBX ('SM_Darius_GodKing_Axe.fbx') 
    导入虚幻引擎为静态网格体 '/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe'。
 2. 绑定神王专属战斧材质 '/Game/Character/Darius/Materials/MI_Darius_Axe'。
 3. 在静态网格体上添加刀光粒子与判定插槽 (Blade_Tip, Blade_Edge, Pommel)。
 4. 在神王骨骼右手 'hand_r' 上建立插槽 'hand_rSocket'，校准握持角度。
 5. 隐藏原身体骨骼网格中位于脚下的旧战斧 (Slot 7)，赋予纯透明材质 M_Invisible。
 6. 在角色蓝图 'BP_DariusCharacter' 中添加 StaticMeshComponent 并精准挂载至 'hand_rSocket'。
=============================================================================
"""

import unreal
import os
import ctypes
import struct
import re

eal = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

weapon_dir = "/Game/Character/Darius/Weapons"
if not eal.does_directory_exist(weapon_dir):
    eal.make_directory(weapon_dir)

fbx_file = "E:/UE/Fight/Saved/Exported_Weapons/SM_Darius_GodKing_Axe.fbx"
asset_name = "SM_Darius_GodKing_Axe"
dest_path = f"{weapon_dir}/{asset_name}"

# 1. 导入独立战斧静态网格体
unreal.log(f"=== 1. Importing Standalone Axe: {fbx_file} ===")
task = unreal.AssetImportTask()
task.set_editor_property('filename', fbx_file)
task.set_editor_property('destination_path', weapon_dir)
task.set_editor_property('destination_name', asset_name)
task.set_editor_property('replace_existing', True)
task.set_editor_property('automated', True)
task.set_editor_property('save', True)

options = unreal.FbxImportUI()
options.set_editor_property('import_mesh', True)
options.set_editor_property('import_as_skeletal', False)
options.set_editor_property('import_materials', False)
options.set_editor_property('import_textures', False)
options.static_mesh_import_data.set_editor_property('combine_meshes', True)
options.static_mesh_import_data.set_editor_property('generate_lightmap_u_vs', False)
task.set_editor_property('options', options)

asset_tools.import_asset_tasks([task])

axe_mesh = eal.load_asset(dest_path)
if not axe_mesh:
    unreal.log_error("Failed to import SM_Darius_GodKing_Axe!")
else:
    unreal.log(f"Imported SM_Darius_GodKing_Axe: {axe_mesh}")

    # 2. 绑定材质 MI_Darius_Axe
    mi_axe = eal.load_asset("/Game/Character/Darius/Materials/MI_Darius_Axe")
    if mi_axe:
        axe_mesh.set_material(0, mi_axe)
        unreal.log("Assigned MI_Darius_Axe to SM_Darius_GodKing_Axe Slot 0")

    # 3. 添加判定插槽 (用于后续攻击判定与 Niagara 刀光)
    # 战斧尺寸约为 1.72m
    sockets_to_add = [
        ('Socket_Blade_Tip', unreal.Vector(0.0, 70.0, 0.0)),
        ('Socket_Blade_Edge', unreal.Vector(-30.0, 50.0, 0.0)),
        ('Socket_Pommel', unreal.Vector(0.0, -90.0, 0.0))
    ]
    for s_name, s_loc in sockets_to_add:
        sock = axe_mesh.find_socket(s_name)
        if not sock:
            sock = unreal.StaticMeshSocket()
            sock.set_editor_property('socket_name', s_name)
            sock.set_editor_property('relative_location', s_loc)
            axe_mesh.add_socket(sock)
            unreal.log(f"Added Socket [{s_name}] at {s_loc} on Axe StaticMesh")

    eal.save_asset(dest_path)

# 4. 在神王骨骼右手添加 hand_rSocket
unreal.log("=== 4. Setting up hand_rSocket on SK_Darius_GodKing ===")
sk_mesh = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
hand_sock = sk_mesh.find_socket("hand_rSocket")
if not hand_sock:
    # 清理可能残留的无名 Socket
    while sk_mesh.find_socket("Socket"):
        sk_mesh.remove_socket("Socket")
    
    sock = unreal.new_object(unreal.SkeletalMeshSocket, sk_mesh, name="hand_rSocket")
    sock.set_socket_parent(sk_mesh, "hand_r")
    sock.set_editor_property('relative_location', unreal.Vector(0.0, 0.0, 0.0))
    sock.set_editor_property('relative_rotation', unreal.Rotator(roll=0.0, pitch=90.0, yaw=0.0))
    sk_mesh.add_socket(sock, add_to_skeleton=True)
    sk_mesh.rename_socket("Socket", "hand_rSocket")
    eal.save_asset("/Game/Character/Darius/SK_Darius_GodKing")
    unreal.log("Created hand_rSocket on SK_Darius_GodKing")
else:
    hand_sock.set_editor_property('relative_location', unreal.Vector(0.0, 0.0, 0.0))
    hand_sock.set_editor_property('relative_rotation', unreal.Rotator(roll=0.0, pitch=90.0, yaw=0.0))
    eal.save_asset("/Game/Character/Darius/SK_Darius_GodKing")
    unreal.log("hand_rSocket verified and updated on SK_Darius_GodKing")

# 5. 隐藏原身体骨骼网格中位于脚下的旧战斧 (Slot 7)
unreal.log("=== 5. Hiding Floor Axe via M_Invisible ===")
invis_mat_path = "/Game/Character/Darius/Materials/M_Invisible"
if not eal.does_asset_exist(invis_mat_path):
    mat_factory = unreal.MaterialFactoryNew()
    invis_mat = asset_tools.create_asset("M_Invisible", "/Game/Character/Darius/Materials", unreal.Material, mat_factory)
    mat_lib = unreal.MaterialEditingLibrary
    invis_mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    zero_c = mat_lib.create_material_expression(invis_mat, unreal.MaterialExpressionConstant, -200, 0)
    zero_c.set_editor_property('r', 0.0)
    mat_lib.connect_material_property(zero_c, '', unreal.MaterialProperty.MP_OPACITY_MASK)
    mat_lib.recompile_material(invis_mat)
    eal.save_asset(invis_mat_path)
    unreal.log("Created M_Invisible material!")
else:
    invis_mat = eal.load_asset(invis_mat_path)

# 将 Slot 7 赋予 M_Invisible 从而彻底隐蔽旧地面网格
mats = list(sk_mesh.get_editor_property('materials'))
mats[7].set_editor_property('material_interface', invis_mat)
sk_mesh.set_editor_property('materials', mats)
eal.save_asset("/Game/Character/Darius/SK_Darius_GodKing")
unreal.log("Hidden original floor axe on SK_Darius_GodKing by setting Slot 7 to M_Invisible!")

# 6. 在 BP_DariusCharacter 中配置 WeaponAxe 并挂接至 hand_rSocket
unreal.log("=== 6. Attaching Axe Component in BP_DariusCharacter ===")
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary

bp_path = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
darius_bp = eal.load_asset(bp_path)
handles = subsystem.k2_gather_subobject_data_for_blueprint(darius_bp)

mesh_handle = None
weapon_handle = None
for h in handles:
    data = subsystem.k2_find_subobject_data_from_handle(h)
    d_name = str(lib.get_display_name(data))
    if 'CharacterMesh0' in d_name:
        mesh_handle = h
    if 'WeaponAxe' in d_name:
        weapon_handle = h

if not weapon_handle and mesh_handle:
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property('parent_handle', mesh_handle)
    params.set_editor_property('new_class', unreal.StaticMeshComponent)
    params.set_editor_property('blueprint_context', darius_bp)
    
    new_handle, fail_reason = subsystem.add_new_subobject(params)
    if lib.is_handle_valid(new_handle):
        subsystem.rename_subobject(new_handle, "WeaponAxe")
        weapon_handle = new_handle
        unreal.log("Added WeaponAxe StaticMeshComponent to BP_DariusCharacter")

# 配置网格资产并校准 SCS 挂接节点
if weapon_handle:
    data = subsystem.k2_find_subobject_data_from_handle(weapon_handle)
    axe_comp = lib.get_object_for_blueprint(data, darius_bp)
    if axe_comp:
        axe_comp.set_editor_property('static_mesh', axe_mesh)
    
    # 获取 SCS 节点并写入精准的 AttachToName 和 ParentComponentOrVariableName
    node4_path = f"{bp_path}.BP_DariusCharacter_C:SimpleConstructionScript_0.SCS_Node_4"
    node4 = unreal.load_object(None, node4_path)
    if node4:
        m4 = re.search(r'\(0x([0-9a-fA-F]+)\)', repr(node4))
        if m4:
            ptr4 = int(m4.group(1), 16)
            # 1. AttachToName = 'hand_rSocket'
            sm_sock = unreal.StaticMeshSocket()
            sm_sock.set_editor_property('socket_name', 'hand_rSocket')
            m_s = re.search(r'\(0x([0-9a-fA-F]+)\)', repr(sm_sock))
            sock_p = int(m_s.group(1), 16)
            hand_idx = struct.unpack('<I', (ctypes.c_uint8 * 4).from_address(sock_p + 0x30))[0]
            
            # 2. ParentComponentOrVariableName = 'CharacterMesh0'
            sm_sock.set_editor_property('socket_name', 'CharacterMesh0')
            mesh_idx = struct.unpack('<I', (ctypes.c_uint8 * 4).from_address(sock_p + 0x30))[0]
            
            # 写入 AttachToName (0x98: Index, 0x9c: Number, 0xa0: DisplayIndex)
            struct.pack_into('<I', (ctypes.c_uint8 * 4).from_address(ptr4 + 0x98), 0, hand_idx)
            struct.pack_into('<I', (ctypes.c_uint8 * 4).from_address(ptr4 + 0x9c), 0, 0)
            struct.pack_into('<I', (ctypes.c_uint8 * 4).from_address(ptr4 + 0xa0), 0, hand_idx)
            
            # 写入 ParentComponentOrVariableName (0xa4: Index, 0xa8: Number, 0xac: DisplayIndex)
            struct.pack_into('<I', (ctypes.c_uint8 * 4).from_address(ptr4 + 0xa4), 0, mesh_idx)
            struct.pack_into('<I', (ctypes.c_uint8 * 4).from_address(ptr4 + 0xa8), 0, 0)
            struct.pack_into('<I', (ctypes.c_uint8 * 4).from_address(ptr4 + 0xac), 0, mesh_idx)
            
            # bIsParentComponentNative = true
            struct.pack_into('<I', (ctypes.c_uint8 * 4).from_address(ptr4 + 0xbc), 0, 1)
            node4.modify()

darius_bp.modify()
unreal.BlueprintEditorLibrary.compile_blueprint(darius_bp)
eal.save_asset(bp_path)
unreal.log("=== Weapon import and character attachment pipeline completed successfully! ===")
