# -*- coding: utf-8 -*-
"""
wp_90_sprint_bp.py —— 在本机跑（不是 UE 远程）：给 BP_DariusCharacter 接 Sprint 逻辑

目标图逻辑：
    Event EnhancedInputAction IA_Sprint
      Triggered -> SetMaxWalkSpeed(self = CharacterMovement, 440)
      Completed -> SetMaxWalkSpeed(self = CharacterMovement, 220)

理由：BlendSpace 的 Speed 轴已扩到 [0,440]，样本 220=run、440=run_fast。
      MaxWalkSpeed 220 时只播 run；按住 Shift 提到 440 就滑到 run_fast。

跑法：
    uv run --no-project python Scripts/anim/wp_90_sprint_bp.py
    uv run --no-project python Scripts/anim/wp_90_sprint_bp.py --apply
"""
import json
import sys

sys.path.insert(0, "E:/UE/Fight/Scripts")
import ue_mcp  # noqa: E402

TS = "editor_toolset.toolsets.blueprint.BlueprintTools"
BP = "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter"
EG = BP + ":EventGraph"

WALK_SPEED = "220.0"
SPRINT_SPEED = "440.0"
APPLY = "--apply" in sys.argv


def call(tool, args):
    res = ue_mcp.rpc("tools/call", {"name": "call_tool", "arguments": {
        "toolset_name": TS, "tool_name": tool, "arguments": args}})
    try:
        return json.loads(res["content"][0]["text"])
    except Exception:
        return {"_raw": res}


def ref_of(r):
    v = r.get("returnValue")
    if isinstance(v, dict):
        return v.get("refPath")
    return None


def say(s):
    print(s, flush=True)


ue_mcp.init()

# ---------- 0. 现状 ----------
say("=" * 68)
say("=== 0. 现状 ===")
r = call("find_nodes", {"graph": {"refPath": EG}, "title": "IA_Sprint"})
evt_nodes = [x["refPath"] for x in (r.get("returnValue") or [])]
say("   IA_Sprint 事件节点: %s" % evt_nodes)
if not evt_nodes:
    raise SystemExit("没找到 IA_Sprint 事件节点，先跑 create_node 建它")
EVT = evt_nodes[0]

r = call("find_nodes", {"graph": {"refPath": EG}, "title": "SetMaxWalkSpeed"})
existing = [x["refPath"] for x in (r.get("returnValue") or [])]
say("   已有 SetMaxWalkSpeed 节点: %d 个 %s" % (len(existing), existing))

# ---------- 1. 建节点 ----------
say("")
say("=" * 68)
say("=== 1. 建节点 ===")
NODES = {}
if len(existing) >= 2:
    say("   已有 2 个，跳过创建（幂等）")
    NODES["sprint"] = existing[0]
    NODES["walk"] = existing[1]
else:
    if not APPLY:
        say("   [dry] 将建 GetCharacterMovement / SetMaxWalkSpeed x2")
        raise SystemExit(0)
    r = call("create_node", {"graph": {"refPath": EG},
                             "type_id": "Variables|Character|GetCharacterMovement",
                             "pos": {"x": -1400, "y": 950}})
    NODES["get"] = ref_of(r)
    say("   GetCharacterMovement -> %s" % NODES["get"])
    r = call("create_node", {"graph": {"refPath": EG},
                             "type_id": "Class|CharacterMovementComponent|SetMaxWalkSpeed",
                             "pos": {"x": -900, "y": 840}})
    NODES["sprint"] = ref_of(r)
    say("   SetMaxWalkSpeed(440) -> %s" % NODES["sprint"])
    r = call("create_node", {"graph": {"refPath": EG},
                             "type_id": "Class|CharacterMovementComponent|SetMaxWalkSpeed",
                             "pos": {"x": -900, "y": 1120}})
    NODES["walk"] = ref_of(r)
    say("   SetMaxWalkSpeed(220) -> %s" % NODES["walk"])

# 找 GetCharacterMovement 节点（若已存在）
r = call("find_nodes", {"graph": {"refPath": EG}, "title": "GetCharacterMovement"})
gets = [x["refPath"] for x in (r.get("returnValue") or [])]
say("   GetCharacterMovement 节点: %s" % gets)
NODES["get"] = gets[0] if gets else NODES.get("get")

if not all(NODES.get(k) for k in ("get", "sprint", "walk")):
    raise SystemExit("节点不全: %s" % NODES)

# ---------- 2. 取 pin_id ----------
say("")
say("=" * 68)
say("=== 2. 读 pin ===")
refs = [EVT, NODES["get"], NODES["sprint"], NODES["walk"]]
r = call("get_node_infos", {"nodes": [{"refPath": x} for x in refs]})
infos = r.get("returnValue") or []
PINS = {}
for n in infos:
    key = n["node"]["refPath"].split(".")[-1]
    d = {}
    for p in n.get("input_pins", []) + n.get("output_pins", []):
        d[p["name"]] = p["pin_id"]
    PINS[key] = d
    say("   %-38s pins=%s" % (key, list(d.keys())))


def pin(node, name):
    k = node.split(".")[-1]
    p = PINS.get(k, {}).get(name)
    if p is None:
        say("   !! 找不到 pin %s.%s" % (k, name))
    return p


key_evt = EVT.split(".")[-1]
key_gs = NODES["get"].split(".")[-1]
key_sp = NODES["sprint"].split(".")[-1]
key_wk = NODES["walk"].split(".")[-1]

JOBS = [
    ("IA_Sprint.Triggered  -> SetMaxWalkSpeed(440).execute",
     (key_evt, "Triggered"), (key_sp, "execute")),
    ("CharacterMovement    -> SetMaxWalkSpeed(440).self",
     (key_gs, "CharacterMovement"), (key_sp, "self")),
    ("IA_Sprint.Completed  -> SetMaxWalkSpeed(220).execute",
     (key_evt, "Completed"), (key_wk, "execute")),
    ("CharacterMovement    -> SetMaxWalkSpeed(220).self",
     (key_gs, "CharacterMovement"), (key_wk, "self")),
]

if not APPLY:
    say("")
    say("[dry] 将连线 %d 条 + 设 2 个常量。加 --apply 执行。" % len(JOBS))
    raise SystemExit(0)

# ---------- 3. 连线 ----------
say("")
say("=" * 68)
say("=== 3. 连线 ===")
for label, (on, op), (dn, dp) in JOBS:
    out_p = pin(NODES.get(on, EVT if on == key_evt else NODES.get(on, "")), op) \
        if False else PINS.get(on, {}).get(op)
    in_p = PINS.get(dn, {}).get(dp)
    if out_p is None or in_p is None:
        say("   跳过 %s （pin 缺失 out=%s in=%s）" % (label, out_p, in_p))
        continue
    r = call("connect_pins", {"output_pin": out_p, "input_pin": in_p})
    ok = "_raw" not in r or "error" not in str(r).lower()
    say("   %-52s %s" % (label, "OK" if ok else json.dumps(r, ensure_ascii=False)[:160]))

# ---------- 4. 设常量 ----------
say("")
say("=" * 68)
say("=== 4. 设速度常量 ===")
for key, val in ((key_sp, SPRINT_SPEED), (key_wk, WALK_SPEED)):
    p = PINS.get(key, {}).get("MaxWalkSpeed")
    if p is None:
        say("   跳过 %s" % key); continue
    r = call("set_pin_value", {"pin": p, "value": val})
    say("   %-38s MaxWalkSpeed=%s  %s" % (key, val, "OK" if "_raw" not in r else str(r)[:140]))

# ---------- 5. 编译保存 ----------
say("")
say("=" * 68)
say("=== 5. 编译保存 ===")
r = call("compile_blueprint", {"blueprint": {"refPath": BP}})
say("   compile: %s" % json.dumps(r, ensure_ascii=False)[:200])

# 用 UE 远程侧保存
sys.path.insert(0, "E:/UE/Fight/Scripts")
say("")
say("完成。请跑 wp_91 做只读复验。")
