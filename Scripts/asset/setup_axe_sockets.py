# -*- coding: utf-8 -*-
"""setup_axe_sockets —— 为战斧静态网格程序化配置战斗判定与握把插槽"""
import unreal

AXE_PATH = "/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe"
eal = unreal.EditorAssetLibrary

mesh = unreal.load_object(None, AXE_PATH)
if not mesh:
    raise RuntimeError(f"Cannot load {AXE_PATH}")

SOCKET_DEFS = [
    {
        "name": "Grip_Main",
        "loc": unreal.Vector(0.0, 0.0, 13.6),
        "rot": unreal.Rotator(0.0, 0.0, 0.0),
        "scale": unreal.Vector(1.0, 1.0, 1.0),
        "tag": "Grip",
    },
    {
        "name": "Grip_Assist",
        "loc": unreal.Vector(0.0, 30.0, 15.0),
        "rot": unreal.Rotator(0.0, 0.0, 0.0),
        "scale": unreal.Vector(1.0, 1.0, 1.0),
        "tag": "Grip",
    },
    {
        "name": "Pommel",
        "loc": unreal.Vector(0.0, 83.0, 18.0),
        "rot": unreal.Rotator(0.0, 0.0, 0.0),
        "scale": unreal.Vector(1.0, 1.0, 1.0),
        "tag": "Pommel",
    },
    {
        "name": "Blade_Tip",
        "loc": unreal.Vector(0.0, -75.7, 50.1),
        "rot": unreal.Rotator(0.0, 0.0, 0.0),
        "scale": unreal.Vector(1.0, 1.0, 1.0),
        "tag": "Hitbox",
    },
    {
        "name": "Blade_Edge",
        "loc": unreal.Vector(0.0, -50.0, 45.0),
        "rot": unreal.Rotator(0.0, 0.0, 0.0),
        "scale": unreal.Vector(1.0, 1.0, 1.0),
        "tag": "Hitbox",
    },
]

unreal.log(f"=== 开始为 {mesh.get_name()} 配置战斗插槽 ===")

for defn in SOCKET_DEFS:
    sname = defn["name"]
    # 检查是否已存在
    existing = mesh.find_socket(sname)
    if existing:
        unreal.log(f"更新已存在插槽: {sname}")
        existing.set_editor_property("relative_location", defn["loc"])
        existing.set_editor_property("relative_rotation", defn["rot"])
        existing.set_editor_property("relative_scale", defn["scale"])
        existing.set_editor_property("tag", defn["tag"])
    else:
        unreal.log(f"创建新插槽: {sname}")
        sock = unreal.new_object(unreal.StaticMeshSocket, mesh)
        sock.set_editor_property("socket_name", unreal.Name(sname))
        sock.set_editor_property("relative_location", defn["loc"])
        sock.set_editor_property("relative_rotation", defn["rot"])
        sock.set_editor_property("relative_scale", defn["scale"])
        sock.set_editor_property("tag", defn["tag"])
        mesh.add_socket(sock)

# 标记脏并保存
mesh.modify()
ok = eal.save_asset(AXE_PATH, only_if_is_dirty=False)
unreal.log(f"保存资产 {AXE_PATH}: {'成功' if ok else '失败'}")

# 校验
unreal.log("=== 校验插槽清单 ===")
for defn in SOCKET_DEFS:
    sname = defn["name"]
    sock = mesh.find_socket(sname)
    if sock:
        loc = sock.get_editor_property("relative_location")
        unreal.log(f"  [OK] {sname:<12} -> loc=({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")
    else:
        unreal.log_warning(f"  [FAIL] {sname} 未找到！")
