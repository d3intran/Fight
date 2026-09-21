# -*- coding: utf-8 -*-
import unreal

mesh = unreal.load_object(None, "/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
unreal.log(f"Mesh loaded: {mesh.get_name()}")

try:
    sock = unreal.new_object(unreal.StaticMeshSocket, mesh)
    sock.set_editor_property("socket_name", unreal.Name("Blade_Tip"))
    sock.set_editor_property("relative_location", unreal.Vector(0.0, -75.668, 50.067))
    sock.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
    sock.set_editor_property("relative_scale", unreal.Vector(1.0, 1.0, 1.0))
    mesh.add_socket(sock)
    unreal.log("add_socket succeeded!")
    found = mesh.find_socket("Blade_Tip")
    unreal.log(f"find_socket('Blade_Tip'): {found}")
    if found:
        unreal.log(f"Socket name: {found.get_editor_property('socket_name')}, loc: {found.get_editor_property('relative_location')}")
except Exception as ex:
    unreal.log_error(f"Failed to add socket: {ex}")
