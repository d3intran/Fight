# -*- coding: utf-8 -*-
"""wp_101_pa_capsules.py —— 本机跑：把长骨的球形碰撞体换成沿骨全长的胶囊

诊断链
------
wp_99  → `SK_Darius_GodKing_Physics` 只有 12 个 body，全是球，球心几乎都在骨骼原点
wp_100 → 所有骨的「沿骨轴」都是**局部 Y**；实测骨长：thigh 45.0 / calf 48.7 /
         upperarm 35.4 / lowerarm 34.0 cm
⇒ 球半径 14cm 只能盖住 45cm 大腿的中间 28cm，**两端各 ~8.5cm 是空的**；
   小腿更糟（48.7cm 的骨、11cm 的球 ⇒ 两端各 ~13cm 空）；
   手臂（upperarm/lowerarm）**连 body 都没有**。
披风从这些空隙里直接穿过去。

修法
----
· thigh_l/r、calf_l/r：删掉 `col_sphere` → 加 `col_capsule`
    - 胶囊长轴 = 「应用 rotation 后的局部 Z」；骨方向是局部 Y ⇒ **rotation.roll = -90**
    - center 放在**骨的中点**（骨方向 −Y ⇒ center.y = −骨长/2）
    - 参数单位 = **骨骼局部米**（与现有 0.14 同一量纲；引擎会把骨骼 scale 传到 shape）
· 用 `-dry` / `-apply` 控制（默认 dry）

跑法：
    uv run --no-project python Scripts/anim/wp_101_pa_capsules.py
    uv run --no-project python Scripts/anim/wp_101_pa_capsules.py -apply
"""
import json
import sys

sys.path.insert(0, "E:/UE/Fight/Scripts")
import ue_mcp  # noqa: E402

TS = "PhysicsToolsets.PhysicsAssetToolset"
PA = {"refPath": "/Game/Character/Darius/SK_Darius_GodKing_Physics.SK_Darius_GodKing_Physics"}
OUT = "E:/UE/Fight/Saved/Attack/wp101_capsules.json"
APPLY = "-apply" in sys.argv


def call(tool, args):
    r = ue_mcp.rpc("tools/call", {"name": "call_tool", "arguments": {
        "toolset_name": TS, "tool_name": tool, "arguments": args}})
    try:
        return json.loads(r["content"][0]["text"])
    except Exception:
        return {"_raw": str(r)[:200]}


# 骨长来自 wp_100 实测（cm）→ 换成本地米
BONE_LEN_CM = {"thigh_l": 44.96, "thigh_r": 44.96, "calf_l": 48.71, "calf_r": 48.71}

# radius 取略小于原球（0.14/0.11）以便胶囊有圆柱段
PLAN = []
for b in ("thigh_l", "thigh_r"):
    L = BONE_LEN_CM[b] / 100.0
    r = 0.13
    PLAN.append({"bone": b, "radius": r, "length": round(L - 2 * r, 4),
                 "center": (0.0, round(-L / 2, 4), 0.0), "old": "col_sphere"})
for b in ("calf_l", "calf_r"):
    L = BONE_LEN_CM[b] / 100.0
    r = 0.11
    PLAN.append({"bone": b, "radius": r, "length": round(L - 2 * r, 4),
                 "center": (0.0, round(-L / 2, 4), 0.0), "old": "col_sphere"})

ue_mcp.init()

print("=" * 96)
print("=== 计划（单位 = 骨骼局部米；rotation.roll = -90 让胶囊长轴对上局部 Y）===")
print("=" * 96)
print("%-12s %10s %10s %-24s %-10s" % ("骨", "radius", "length", "center", "总长(米)"))
for p in PLAN:
    print("%-12s %10.3f %10.3f   (%.4f, %.4f, %.4f)   %.4f" % (
        p["bone"], p["radius"], p["length"],
        p["center"][0], p["center"][1], p["center"][2],
        p["length"] + 2 * p["radius"]))

print("")
print("=== 改前 ===")
for p in PLAN:
    sh = call("GetBodyShapes", {"physicsAsset": PA, "boneName": p["bone"]})
    print("   %-12s %s" % (p["bone"], json.dumps(sh.get("returnValue"), ensure_ascii=False)[:220]))

if not APPLY:
    print("")
    print("[dry] 加 -apply 执行。")
    raise SystemExit(0)

print("")
print("=== 执行 ===")
res = {"plan": PLAN, "results": []}
for p in PLAN:
    b = p["bone"]
    rm = call("RemoveShape", {"physicsAsset": PA, "boneName": b, "shapeName": p["old"]})
    print("   %-12s 删 %s -> %s" % (b, p["old"], json.dumps(rm, ensure_ascii=False)[:80]))
    cap = call("SetCapsule", {
        "physicsAsset": PA, "boneName": b, "shapeName": "col_capsule",
        "center": {"x": p["center"][0], "y": p["center"][1], "z": p["center"][2]},
        "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": -90.0},
        "radius": p["radius"], "length": p["length"],
    })
    print("   %-12s 加 col_capsule -> %s" % (b, json.dumps(cap, ensure_ascii=False)[:120]))
    res["results"].append({"bone": b, "remove": rm, "capsule": cap})

print("")
print("=== 改后 ===")
for p in PLAN:
    sh = call("GetBodyShapes", {"physicsAsset": PA, "boneName": p["bone"]})
    print("   %-12s %s" % (p["bone"], json.dumps(sh.get("returnValue"), ensure_ascii=False)[:260]))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print("")
print("已写 %s" % OUT)
print("WP101_DONE")
