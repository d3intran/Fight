"""枚举 UE 5.8 引擎自带 Toolsets 的「能做什么」—— 只读引擎源码/脚本，不连编辑器。

两类实现：
  * C++  : Source/**/Public/*.h 里的 UCLASS ... : UToolsetDefinition + UFUNCTION
  * Python: Content/Python/**/toolsets/*.py 里的 @unreal.uclass() ... (unreal.ToolsetDefinition)
           + @toolset_registry.tool_call 装饰的 staticmethod
"""
import glob
import os
import re

ROOT = r"E:/UE_5.8/Engine/Plugins/Experimental/Toolsets"

PY_TOOL = re.compile(r"@toolset_registry\.tool_call\s*\n\s*@staticmethod\s*\n\s*def\s+(\w+)\s*\(", re.M)
PY_TOOL2 = re.compile(r"@staticmethod\s*\n\s*@toolset_registry\.tool_call\s*\n\s*def\s+(\w+)\s*\(", re.M)
PY_CLASS = re.compile(r"class\s+(\w+)\s*\(\s*unreal\.ToolsetDefinition\s*\)")
PY_DOC = re.compile(r'class\s+\w+\s*\(\s*unreal\.ToolsetDefinition\s*\):\s*\n\s*"""(.+?)"""', re.S)

for tdir in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, tdir)
    if not os.path.isdir(p):
        continue
    py_files = glob.glob(p + "/Content/Python/**/*.py", recursive=True)
    py_files = [f for f in py_files if "/tests/" not in f.replace("\\", "/")]
    if not py_files:
        print("%-32s (无 Python 工具实现)" % tdir)
        continue
    total = 0
    for f in sorted(py_files):
        src = open(f, encoding="utf-8", errors="replace").read()
        names = sorted(set(PY_TOOL.findall(src)) | set(PY_TOOL2.findall(src)))
        if not names:
            continue
        classes = PY_CLASS.findall(src)
        doc = PY_DOC.search(src)
        total += len(names)
        print("%-32s %-28s %3d 工具  %s" % (
            tdir if f is py_files[0] else "", os.path.basename(f), len(names),
            (classes[0] if classes else "")))
        if doc:
            print("      「%s」" % " ".join(doc.group(1).split())[:160])
        for n in names:
            print("        -", n)
    if total == 0:
        print("%-32s 有 Python 但没匹配到工具" % tdir)
