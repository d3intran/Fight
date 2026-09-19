import unreal

mat = unreal.load_asset("/Game/Character/Darius/Materials/M_Invisible")
print("M_Invisible:", mat)
print("blend_mode:", mat.get_editor_property("blend_mode"))

print()
print("=== 所有含 shadow / opacity 的属性 ===")
for p in ["cast_dynamic_shadow_as_masked", "b_cast_dynamic_shadow_as_masked",
          "blend_mode", "two_sided", "opacity_mask_clip_value",
          "disable_depth_test", "dithered_lod_transition", "wireframe"]:
    try:
        print(f"  {p}:", mat.get_editor_property(p))
    except Exception as e:
        print(f"  {p}: <无此属性>")

print()
print("=== 尝试开启 cast_dynamic_shadow_as_masked ===")
ok = False
for p in ["cast_dynamic_shadow_as_masked", "b_cast_dynamic_shadow_as_masked"]:
    try:
        mat.set_editor_property(p, True)
        print(f"  设置成功: {p} =", mat.get_editor_property(p))
        ok = True
        break
    except Exception as e:
        print(f"  {p} 失败: {e}")

if ok:
    print("  保存:", unreal.EditorAssetLibrary.save_loaded_asset(mat))

print()
print("=== 检查 SK 各 Section 的材质索引与三角形数 ===")
sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
try:
    lod = sk.get_editor_property("lod_info")
    print("  LOD 数:", len(lod))
    for i, L in enumerate(lod):
        secs = L.get_editor_property("sections")
        print(f"  LOD{i}: sections={len(secs)}")
        for j, s in enumerate(secs):
            print(f"     section[{j}] matIndex={s.get_editor_property('material_index')} "
                  f"numTriangles={s.get_editor_property('num_triangles') if hasattr(s,'get_editor_property') else '?'}")
except Exception as e:
    print("  lod err:", e)
print("=== DONE ===")
