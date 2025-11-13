# analyzers/dynamic_loading.py
"""
Detect dynamic code loading/reflection/indirect calls:
 - Python: eval, exec, compile, importlib, getattr/locals tricks
 - C/C++: function pointers, dlsym, system/exec calls
 - Java/Kotlin: reflection usage (Class.forName, Method.invoke)
Cleaning is conservative: we only report and, for trivial indirect calls (wrapper->function pointer),
we can sometimes inline wrapper.
"""

import re
from typing import List, Dict

# Python dynamic constructs
_PY_DYN = [
    re.compile(r'\beval\s*\('),
    re.compile(r'\bexec\s*\('),
    re.compile(r'\bcompile\s*\('),
    re.compile(r'\bimportlib\.'),
    re.compile(r'\b__import__\s*\('),
    re.compile(r'getattr\s*\('),
]

def detect_dynamic_code_loading_python(code: str) -> List[Dict]:
    findings = []
    for pat in _PY_DYN:
        for m in pat.finditer(code):
            findings.append({"type": "dynamic_py", "lineno": code[:m.start()].count("\n")+1, "snippet": m.group(0), "reason": "dynamic execution/reflection"})
    return findings

def detect_dynamic_code_loading_clike(code: str) -> List[Dict]:
    findings = []
    # function pointers: type (*fp)(); usage: fp();
    if re.search(r'\(\s*\*\s*[A-Za-z_]\w*\s*\)\s*\(', code):
        findings.append({"type": "func_ptr", "reason": "Function pointer usage detected (C/C++)"})
    # dlsym or GetProcAddress
    if re.search(r'\bdlsym\s*\(|\bGetProcAddress\s*\(', code):
        findings.append({"type": "dynamic_link", "reason": "dynamic symbol loading (dlsym/GetProcAddress)"})
    # system/exec
    if re.search(r'\bsystem\s*\(|\bexecve?\s*\(', code):
        findings.append({"type": "exec_call", "reason": "dynamic process creation or exec"})
    # Java reflection hints
    if re.search(r'\bClass\.forName\s*\(|\bgetMethod\s*\(|\binvoke\s*\(', code):
        findings.append({"type": "java_reflection", "reason": "Java reflection API usage"})
    return findings

def clean_dynamic_code_loading_clike(code: str) -> List[Dict]:
    # Very conservative: only inline wrappers that are direct trivial forwarding functions
    changes = []
    # detect trivial wrapper: int wrapper() { return actual(); }
    m = re.search(r'\b([A-Za-z_]\w*)\s*\([^)]*\)\s*\{\s*return\s+([A-Za-z_]\w*)\s*\(\s*\)\s*;\s*\}', code)
    if m:
        wrapper_name = m.group(1); real = m.group(2)
        # Replace calls to wrapper() with real()
        orig_wrapper = m.group(0)
        new_code = re.sub(r'\b' + re.escape(wrapper_name) + r'\s*\(\s*\)', real + '()', code)
        changes.append({"original": orig_wrapper, "cleaned": "", "reason": f"Removed trivial wrapper {wrapper_name} -> inlined calls to {real}()"})
        changes.append({"original": code, "cleaned": new_code, "reason": "Inlined trivial wrapper (C-like)"})
    else:
        # No safe changes
        dyn = detect_dynamic_code_loading_clike(code)
        if dyn:
            changes.append({"original": "", "cleaned": "", "reason": f"Detected dynamic loading/reflection: {dyn}. No automatic rewrite."})
    return changes

def clean_dynamic_code_loading_python(code: str) -> List[Dict]:
    # Do not attempt to remove eval/exec; only flag or suggest replacement.
    findings = detect_dynamic_code_loading_python(code)
    if findings:
        return [{"original": "", "cleaned": "", "reason": f"Detected dynamic constructs (eval/exec/compile/reflection). Manual review required: {findings}"}]
    return []
