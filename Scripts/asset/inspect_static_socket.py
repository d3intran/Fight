# -*- coding: utf-8 -*-
import unreal

mesh = unreal.load_object(None, "/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
unreal.log(f"Mesh: {mesh.get_name()}")
unreal.log(f"add_socket doc: {mesh.add_socket.__doc__}")

# Check unreal.StaticMeshSocket
sock = unreal.StaticMeshSocket()
unreal.log(f"StaticMeshSocket attributes: {[a for a in dir(sock) if not a.startswith('_')]}")
