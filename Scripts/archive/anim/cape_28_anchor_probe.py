import unreal

PA = "/Game/Character/Darius/SK_Darius_GodKing_Physics"
pa = unreal.load_object(None, PA)

unreal.log("############ 1. 顺链约束（01->02->...->09）")
for side in ("l", "m", "r"):
    row = []
    for i in range(1, 9):
        a = "cape_chain_%02d_%s" % (i, side)
        b = "cape_chain_%02d_%s" % (i + 1, side)
        try:
            c = pa.get_constraint_by_bone_names(a, b)
        except Exception as ex:
            c = "ERR"
            unreal.log("   ERR %s" % str(ex)[:50])
            break
        row.append("%d-%d:%s" % (i, i + 1, "有" if c else "无"))
    unreal.log("   %s  %s" % (side, "  ".join(row)))

unreal.log("############ 2. 链根是否锚到身体骨")
HEADS = ["cape_chain_01_l", "cape_chain_01_m", "cape_chain_01_r"]
PARENTS = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "clavicle_l", "clavicle_r",
           "shoulder_l", "shoulder_r", "shoulderpad_jnt_l", "shoulderpad_jnt_r", "cape_root",
           "cape_chain_00_l", "root"]
for h in HEADS:
    hit = []
    for p in PARENTS:
        try:
            c = pa.get_constraint_by_bone_names(h, p)
        except Exception:
            c = None
        if c:
            hit.append(p)
    unreal.log("   %-16s 连到: %s" % (h, hit if hit else "★ 无（链根未锚定）"))

unreal.log("############ 3. 身体骨在物理资产里有没有刚体")
sk = unreal.load_object(None, "/Game/Character/Darius/SK_Darius_GodKing")
unreal.log("   （用 get_constraint_by_name 侧测：有约束=>大概率有体）")
for b in ("pelvis", "spine_01", "spine_02", "spine_03", "head", "upperarm_l", "thigh_l"):
    try:
        c = pa.get_constraint_by_name(b)
    except Exception:
        c = None
    unreal.log("   %-14s constraint_by_name -> %s" % (b, "有" if c else "无"))

unreal.log("############ 4. 名字表旁证：物理包里出现过哪些非披风骨名")
import re
raw = open("E:/UE/Fight/Content/Character/Darius/SK_Darius_GodKing_Physics.uasset", "rb").read()
toks = set(re.findall(rb"[a-z][a-z0-9_]{3,24}", raw))
body = sorted(t.decode() for t in toks if any(k in t for k in (b"pelvis", b"spine", b"clavicle", b"head", b"shoulder",
                                                                b"upperarm", b"lowerarm", b"thigh", b"hand", b"neck")))
unreal.log("   %s" % body)
cape = sorted(t.decode() for t in toks if t.startswith(b"cape"))
unreal.log("   cape 相关串: %s" % cape)
unreal.log("   含 'sphere'/'capsule'/'box' 的串: %s" % sorted(t.decode() for t in toks if b"sphere" in t or b"capsule" in t or b"_box" in t)[:8])
unreal.log("############ DONE")
