import unreal

# ---------- 1. 修正 hand_rSocket 的 100x 继承缩放（资产层，持久化） ----------
sk = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
sock = sk.find_socket(unreal.Name("hand_rSocket"))
print("before relScale:", sock.get_editor_property("relative_scale"))
sock.set_editor_property("relative_scale", unreal.Vector(0.01, 0.01, 0.01))
print("after  relScale:", sock.get_editor_property("relative_scale"))

saved = unreal.EditorAssetLibrary.save_loaded_asset(sk)
print("SK saved:", saved)

# 复核：重新从磁盘载入
unreal.EditorAssetLibrary.unload_asset("/Game/Character/Darius/SK_Darius_GodKing")
sk2 = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
s2 = sk2.find_socket(unreal.Name("hand_rSocket"))
print("reloaded relScale:", s2.get_editor_property("relative_scale"))

# ---------- 2. 检查 M_Invisible 的 Opacity Mask 是否为常量 0 ----------
mat = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/Materials/M_Invisible")
print()
print("M_Invisible blend:", mat.get_editor_property("blend_mode"))
try:
    om = mat.get_editor_property("opacity_mask")
    print("opacity_mask struct:", om)
    try:
        print("  use_constant:", om.get_editor_property("use_constant"))
        print("  constant:", om.get_editor_property("constant"))
        print("  expression:", om.get_editor_property("expression"))
    except Exception as e:
        print("  field err:", e)
except Exception as e:
    print("opacity_mask err:", e)
try:
    op = mat.get_editor_property("opacity")
    print("opacity struct:", op)
    try:
        print("  use_constant:", op.get_editor_property("use_constant"))
        print("  constant:", op.get_editor_property("constant"))
    except Exception as e:
        print("  field err:", e)
except Exception as e:
    print("opacity err:", e)
print("=== DONE ===")
