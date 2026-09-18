# -*- coding: utf-8 -*-
import unreal
p = "/Game/Temp/RT_AxeCap"
unreal.log("load_asset -> %s" % unreal.load_asset(p))
if unreal.EditorAssetLibrary.does_asset_exist(p):
    unreal.log("delete_asset -> %s" % unreal.EditorAssetLibrary.delete_asset(p))
if unreal.EditorAssetLibrary.does_directory_exist("/Game/Temp"):
    unreal.log("delete_directory -> %s" % unreal.EditorAssetLibrary.delete_directory("/Game/Temp"))
