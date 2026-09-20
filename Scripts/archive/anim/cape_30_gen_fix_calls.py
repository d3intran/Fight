"""生成披风物理改造的 MCP 批量调用清单（写入 Saved/cape_fix_calls.json）。

改造内容（依据 Saved/cape_geom.txt 的实测数字）：
  1) 锚点骨 spine_03 建刚体 + 球 + Kinematic，并把 3 条链根约束上去
  2) 身体碰撞骨（脊柱链/骨盆/颈/头/肩/大腿/小腿）建球体刚体，Kinematic
  3) 27 根披风刚体：换成贴合薄片的_sphere（半径 0.05，现有 0.505 太大），设为 Simulated
"""
import json
import sys

PA_REF = sys.argv[1] if len(sys.argv) > 1 else \
    "/Script/Engine.PhysicsAsset'/Game/Temp/PA_capeA_test.PA_capeA_test'"

# 骨轴在 bone-local 里是 +Y（实测 骨轴局部=[0,1,0]）
ANCHOR = "spine_03"
# (骨名, 球半径 m)：半径取「该骨中点到披风的实测距离」× 0.75 左右，
#  既能挡住披风又不会把它顶离身体太远。数据源 Saved/cape_geom.txt。
BODIES = [
    ("pelvis", 0.15, (0.0, 0.05, 0.0)),
    ("spine_01", 0.16, (0.0, 0.06, 0.0)),
    ("spine_02", 0.17, (0.0, 0.06, 0.0)),
    ("spine_03", 0.18, (0.0, 0.10, 0.0)),
    ("neck_01", 0.10, (0.0, 0.05, 0.0)),
    ("head", 0.13, (0.0, 0.04, 0.0)),
    ("clavicle_l", 0.12, (0.0, 0.10, 0.0)),
    ("clavicle_r", 0.12, (0.0, 0.10, 0.0)),
    ("thigh_l", 0.14, (0.0, 0.10, 0.0)),
    ("thigh_r", 0.14, (0.0, 0.10, 0.0)),
    ("calf_l", 0.11, (0.0, 0.10, 0.0)),
    ("calf_r", 0.11, (0.0, 0.10, 0.0)),
]
CAPE_R = 0.05
LINK_HALF = {  # 各链节半长（bone-local Y），来自实测 len/2
    ("l", 1): 0.1156, ("l", 2): 0.1049, ("l", 3): 0.0861, ("l", 4): 0.1057, ("l", 5): 0.0867,
    ("l", 6): 0.0998, ("l", 7): 0.0908, ("l", 8): 0.0847, ("l", 9): 0.0847,
    ("m", 1): 0.0842, ("m", 2): 0.1037, ("m", 3): 0.0866, ("m", 4): 0.1024, ("m", 5): 0.0863,
    ("m", 6): 0.1006, ("m", 7): 0.0895, ("m", 8): 0.0842, ("m", 9): 0.0842,
    ("r", 1): 0.1156, ("r", 2): 0.1049, ("r", 3): 0.0861, ("r", 4): 0.1057, ("r", 5): 0.0867,
    ("r", 6): 0.0998, ("r", 7): 0.0908, ("r", 8): 0.0847, ("r", 9): 0.0847,
}

PA = {"refPath": PA_REF}
calls = []


def add(tool, args):
    a = {"physicsAsset": PA}
    a.update(args)
    calls.append({"tool": tool, "args": a})


# 1 锚点骨
add("AddBody", {"boneName": ANCHOR})
add("SetSphere", {"boneName": ANCHOR, "shapeName": "anchor_sphere",
                  "center": {"x": 0.0, "y": 0.10, "z": 0.0}, "radius": 0.18})
add("SetBodyPhysicsMode", {"boneName": ANCHOR, "mode": "Kinematic"})
for side in ("l", "m", "r"):
    add("AddConstraint", {"bone1Name": "cape_chain_01_%s" % side, "bone2Name": ANCHOR})

# 2 身体碰撞骨（spine_03 已在上面建过）
for bn, r, ctr in BODIES:
    if bn == ANCHOR:
        continue
    add("AddBody", {"boneName": bn})
    add("SetSphere", {"boneName": bn, "shapeName": "col_sphere",
                      "center": {"x": ctr[0], "y": ctr[1], "z": ctr[2]}, "radius": r})
    add("SetBodyPhysicsMode", {"boneName": bn, "mode": "Kinematic"})

# 3 披风 27 根：换小球 + Simulated
for side in ("l", "m", "r"):
    for i in range(1, 10):
        bn = "cape_chain_%02d_%s" % (i, side)
        add("RemoveShape", {"boneName": bn, "shapeName": "%s_sphere" % bn})
        add("SetSphere", {"boneName": bn, "shapeName": "cape_sphere",
                          "center": {"x": 0.0, "y": LINK_HALF[(side, i)], "z": 0.0},
                          "radius": CAPE_R})
        add("SetBodyPhysicsMode", {"boneName": bn, "mode": "Simulated"})

out = {"toolset": "PhysicsToolsets.PhysicsAssetToolset", "calls": calls}
with open("Saved/cape_fix_calls.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("生成 %d 个调用 -> Saved/cape_fix_calls.json   目标 %s" % (len(calls), PA_REF))
