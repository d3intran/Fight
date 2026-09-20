"""UE 编辑器内置 MCP server (127.0.0.1:8000/mcp) 的最小 HTTP 客户端。

用法:
  ue_mcp.py list                       # 列工具
  ue_mcp.py schema <tool>              # 看某工具入参
  ue_mcp.py call <tool> '<json-args>'  # 调用
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
    with urllib.request.urlopen(req, timeout=180) as r:
        sid = r.headers.get("Mcp-Session-Id")
        if sid:
            _session = sid
        body = r.read().decode("utf-8", "replace")
    if notify:
        return None
    if body.lstrip().startswith("{"):
        return json.loads(body)
    out = None
    for ln in body.splitlines():
        if ln.startswith("data:"):
            try:
                out = json.loads(ln[5:].strip())
            except Exception:
                pass
    return out


def init():
    r = _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
               "params": {"protocolVersion": _proto, "capabilities": {},
                          "clientInfo": {"name": "qoder-cli", "version": "1.0"}}})
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, notify=True)
    return r


def rpc(method, params=None, mid=2):
    r = _post({"jsonrpc": "2.0", "id": mid, "method": method, "params": params or {}})
    if isinstance(r, dict) and "error" in r:
        raise SystemExit("MCP error: %s" % json.dumps(r["error"], ensure_ascii=False)[:2000])
    return r.get("result") if isinstance(r, dict) else r


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    init()
    if cmd == "list":
        tools = rpc("tools/list").get("tools", [])
        print("共 %d 个工具" % len(tools))
        for t in tools:
            print("  %-46s %s" % (t["name"], (t.get("description") or "").split("\n")[0][:90]))
    elif cmd == "schema":
        tools = rpc("tools/list").get("tools", [])
        for t in tools:
            if t["name"] == sys.argv[2]:
                print(json.dumps(t, ensure_ascii=False, indent=1)[:6000])
    elif cmd == "call":
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        res = rpc("tools/call", {"name": sys.argv[2], "arguments": args})
        print(json.dumps(res, ensure_ascii=False, indent=1))
    elif cmd == "batch":
        # 批量：参数是 JSON 文件路径，内容 {"toolset":"...","calls":[{"tool":"Name","args":{}}]}
        spec = json.load(open(sys.argv[2], encoding="utf-8"))
        tsname = spec["toolset"]
        for i, c in enumerate(spec["calls"]):
            res = rpc("tools/call", {"name": "call_tool", "arguments": {
                "toolset_name": tsname, "tool_name": c["tool"],
                "arguments": c.get("args", {})}}, mid=10 + i)
            txt = ""
            try:
                txt = res["content"][0]["text"]
            except Exception:
                txt = json.dumps(res, ensure_ascii=False)[:200]
            print("[%02d] %-22s %s" % (i, c["tool"], txt[:200]))
    elif cmd == "raw":
        print(json.dumps(rpc(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}),
                         ensure_ascii=False, indent=1)[:8000])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
