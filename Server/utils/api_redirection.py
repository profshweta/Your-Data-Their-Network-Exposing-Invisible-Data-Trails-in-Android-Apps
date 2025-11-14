# analyzers/api_redirection.py
"""
Detect API redirection/wrapper patterns:
  - tiny wrappers that call another function and do nothing else
  - multiple-level wrappers
Cleaning: inline trivial wrappers (calls) conservatively.
"""

import re
from typing import List, Dict

def detect_api_redirection_clike(code: str) -> List[Dict]:
    findings = []
    # detect small wrapper function that only calls another function and returns its value
    # e.g., int wrapper() { return actual(); }
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\((?:[^)]*)\)\s*\{\s*return\s+([A-Za-z_]\w*)\s*\(\s*\)\s*;\s*\}', code):
        findings.append({"type": "trivial_wrapper", "lineno": code[:m.start()].count("\n")+1, "wrapper": m.group(1), "target": m.group(2)})
    # wrapper that forwards single arg: return actual(a);
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\(\s*([^\)]*)\)\s*\{\s*return\s+([A-Za-z_]\w*)\s*\(\s*\2\s*\)\s*;\s*\}', code):
        findings.append({"type": "arg_forwarding_wrapper", "lineno": code[:m.start()].count("\n")+1, "wrapper": m.group(1), "target": m.group(3)})
    return findings

def clean_api_redirection_clike(code: str) -> List[Dict]:
    changes = []
    s = code
    # Inline trivial wrappers: replace calls to wrapper() with actual()
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\((?:\s*)\)\s*;\s*', s):
        # attempt to find wrapper definition
        call_name = m.group(1)
        # find def: return actual();
        mm = re.search(r'\b' + re.escape(call_name) + r'\s*\([^)]*\)\s*\{\s*return\s+([A-Za-z_]\w*)\s*\(\s*\)\s*;\s*\}', s)
        if mm:
            actual = mm.group(1)
            s_new = re.sub(r'\b' + re.escape(call_name) + r'\s*\(\s*\)', actual + '()', s)
            if s_new != s:
                changes.append({"original": call_name + "()", "cleaned": actual + "()", "reason": f"Inlined trivial wrapper {call_name} -> {actual}"})
                s = s_new
    if changes:
        changes.append({"original": code, "cleaned": s, "reason": "Inlined trivial API wrappers (C-like)"})
    else:
        findings = detect_api_redirection_clike(code)
        if findings:
            changes.append({"original": "", "cleaned": "", "reason": f"Detected wrapper patterns but no safe automatic inlining performed: {findings}"})
    return changes

def detect_api_redirection_python(code: str) -> List[Dict]:
    findings = []
    # def wrapper(): return actual()
    for m in re.finditer(r'def\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*:\s*return\s+([A-Za-z_]\w*)\s*\(\s*\)\s*', code):
        findings.append({"type": "trivial_wrapper_py", "lineno": code[:m.start()].count("\n")+1, "wrapper": m.group(1), "target": m.group(2)})
    return findings

def clean_api_redirection_python(code: str) -> List[Dict]:
    s = code
    changes = []
    # inline trivial wrappers by replacing calls
    for m in re.finditer(r'def\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*:\s*return\s+([A-Za-z_]\w*)\s*\(\s*\)\s*', s):
        wrapper = m.group(1); target = m.group(2)
        # replace calls wrapper() with target()
        s_new = re.sub(r'\b' + re.escape(wrapper) + r'\s*\(\s*\)', target + '()', s)
        if s_new != s:
            changes.append({"original": wrapper + "() calls", "cleaned": target + "()", "reason": f"Inlined trivial wrapper {wrapper} -> {target}"})
            s = s_new
    if changes:
        changes.append({"original": code, "cleaned": s, "reason": "Inlined trivial wrappers (Python)"})
    else:
        finds = detect_api_redirection_python(code)
        if finds:
            changes.append({"original": "", "cleaned": "", "reason": f"Detected wrappers: {finds}. No automatic inlining applied."})
    return changes
