import unreal

eal = unreal.EditorAssetLibrary

sk_mesh = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
skel = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")

unreal.log(f"SkeletalMesh methods for socket: {[m for m in dir(sk_mesh) if 'socket' in m.lower()]}")
unreal.log(f"Skeleton methods for socket: {[m for m in dir(skel) if 'socket' in m.lower()]}")
unreal.log(f"SkeletalMeshSocket class: {dir(unreal.SkeletalMeshSocket)}")
