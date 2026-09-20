"""
=============================================================================
 虚幻引擎 Python 远程执行通用驱动器 (ue_remote.py)
 -----------------------------------------------------------------------------
 作用：
 1. 基于 UDP 广播 (端口 6766) 自动发现正在运行的 Unreal Editor 实例。
 2. 建立 TCP 命令通道，在不阻塞编辑器界面的情况下向编辑器发送执行 Python 脚本。
 3. 收集并格式化输出远端执行日志（Info / Warning / Error），支持异常栈追踪。
 
 依赖：
 - uv run --no-project python Scripts/ue_remote.py <script_path.py>
=============================================================================
"""

import os
import sys
import time

sys.path.append('E:/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python')
import remote_execution

def run_ue_code(code_str):
    client = remote_execution.RemoteExecution()
    client.start()
    nodes = []
    for _ in range(6):
        time.sleep(0.5)
        nodes = client.remote_nodes
        if nodes:
            break
    if not nodes:
        print("[Error] 未发现正在运行且开启 Remote Execution 的虚幻编辑器实例！")
        client.stop()
        return False, []
    
    client.open_command_connection(nodes[0]['node_id'])
    time.sleep(0.3)
    res = client.run_command(code_str, exec_mode=remote_execution.MODE_EXEC_FILE)
    client.stop()
    
    output = []
    if res and 'output' in res:
        for item in res['output']:
            output.append(f"[{item.get('type', 'Log')}] {item.get('output', '').strip()}")
    if res and not res.get('success'):
        output.append(f"[Error] 执行失败:\n{res.get('result')}")
        
    return res.get('success', False), output

if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            code = f.read()
    else:
        code = sys.stdin.read()

    # ⚠️ 必须把脚本先落成**真实文件**，再向 UE 传「路径」，而不是传「内容」。
    # 实测（2026-09-18，二分定位）：MODE_EXEC_FILE 下若直接传内容，UE 会在内容里
    # 嗅探形如 `xxx.py` 的字样并误判成文件路径 —— 只要脚本的 docstring / 注释里
    # 写了自己的文件名（例如用法示例 `... Scripts/plan_14_xxx.py`），就会报
    # `Could not load Python file '<整段内容>'` 且完全不执行。
    # 对照组：同样长度、同样结构但不含 `.py` 字样的脚本一律正常。
    # 修复：一律落盘后传路径；万一某个 UE 版本反过来只认内容，再回退一次。
    runner = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ue_remote_run.py")
    with open(runner, 'w', encoding='utf-8') as f:
        f.write(code)

    success, logs = run_ue_code(runner)
    if not success and any("Could not load Python file" in l for l in logs):
        success, logs = run_ue_code(code)

    for l in logs:
        print(l)
    sys.exit(0 if success else 1)
