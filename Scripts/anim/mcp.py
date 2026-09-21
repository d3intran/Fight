#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""mcp.py —— 薄包装：给 ue_mcp.py 传 JSON 时避免 shell 转义地狱。

用法:
    uv run --no-project python Scripts/anim/mcp.py list
    uv run --no-project python Scripts/anim/mcp.py describe <toolset>
    uv run --no-project python Scripts/anim/mcp.py tools <toolset>        # 只打印工具名
    uv run --no-project python Scripts/anim/mcp.py call <toolset> <tool> '<json-args>'
    uv run --no-project python Scripts/anim/mcp.py topcall <tool> '<json-args>'
"""
import json
import sys
import urllib.request

URL = "http://127.0.0.1:8000/mcp"
_proto = "2025-11-25"
_session = None


def _post(payload, notify=False):
    global _session
    hdr = {"Content-Type": "application/json",
           "Accept": "application/json, text/event-stream"}
    if _session:
        hdr["Mcp-Session-Id"] = _session
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=hdr)
    with urllib.request.urlopen(req, timeout=300) as r:
        sid = r.headers.get("Mcp-Session-Id")
        if sid:
            _session = sid
        body = r.read().decode("utf-8", "replace")
    if notify:
        return None
    for line in body.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    return json.loads(body)


def call_tool(toolset, tool, args):
    a = {"tool_name": tool, "arguments": args}
    if toolset:
        a["toolset_name"] = toolset
    r = _post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": "call_tool", "arguments": a}}, notify=False)
    if "error" in r:
        return {"error": r["error"]}
    return r


def unwrap(r):
    """把 mcp 返回的 content[0].text 解成 python 对象"""
    try:
        t = r["result"]["content"][0]["text"]
    except Exception:
        return r
    try:
        return json.loads(t)
    except Exception:
        return t


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd = sys.argv[1]
    if cmd == "list":
        r = _post({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        for t in r.get("result", {}).get("tools", []):
            print("-", t["name"])
    elif cmd == "describe":
        r = _post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                   "params": {"name": "describe_toolset",
                              "arguments": {"toolset_name": sys.argv[2]}}})
        d = unwrap(r)
        if isinstance(d, dict) and "tools" in d:
            for t in d["tools"]:
                print("### %s" % t["name"])
                print("    " + (t.get("description", "") or "").split("\n")[0][:200])
        else:
            print(json.dumps(d, ensure_ascii=False, indent=1)[:4000])
    elif cmd == "tools":
        r = _post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                   "params": {"name": "describe_toolset",
                              "arguments": {"toolset_name": sys.argv[2]}}})
        d = unwrap(r)
        for t in d.get("tools", []):
            print(t["name"])
    elif cmd == "call":
        args = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        r = call_tool(sys.argv[2], sys.argv[3], args)
        print(json.dumps(unwrap(r), ensure_ascii=False, indent=1))
    elif cmd == "topcall":
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        r = _post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                   "params": {"name": sys.argv[2], "arguments": args}})
        print(json.dumps(unwrap(r), ensure_ascii=False, indent=1))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
