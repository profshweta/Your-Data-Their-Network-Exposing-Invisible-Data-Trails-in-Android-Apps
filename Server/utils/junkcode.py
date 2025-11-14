# analyzers/junk_code.py
"""
Detect/remove junk code: NOPs, identity operations, redundant arithmetic, dead stores used only for obfuscation.
Conservative cleaning: only remove clear NOP-like constructs and no-op arithmetic on local vars not used in observable way.
"""

import re
from typing import List, Dict

def detect_junk_code_clike(code: str) -> List[Dict]:
    findings = []
    # inline asm nop; common patterns
    for m in re.finditer(r'\basm\s*\(\s*".*?nop.*?"\s*\)\s*;', code, re.IGNORECASE | re.DOTALL):
        findings.append({"type": "asm_nop", "lineno": code[:m.start()].count("\n")+1, "snippet": m.group(0)})
    # identity ops: x = x + 0; x = x * 1;
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s*=\s*\1\s*([+\-\*\/])\s*0\b', code):
        findings.append({"type": "identity_add_zero", "lineno": code[:m.start()].count("\n")+1, "snippet": m.group(0)})
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s*=\s*\1\s*\*\s*1\b', code):
        findings.append({"type": "identity_mul_one", "lineno": code[:m.start()].count("\n")+1, "snippet": m.group(0)})
    # dead stores: var assigned then immediately overwritten without use
    # simplified heuristic: pattern "x = <expr>; x = <expr2>;" on consecutive lines
    lines = code.splitlines()
    for i in range(len(lines)-1):
        a = lines[i].strip(); b = lines[i+1].strip()
        m1 = re.match(r'([A-Za-z_]\w*)\s*=\s*[^;]+;', a)
        m2 = re.match(r'([A-Za-z_]\w*)\s*=\s*[^;]+;', b)
        if m1 and m2 and m1.group(1) == m2.group(1):
            findings.append({"type": "dead_store_sequence", "lineno": i+1, "snippet": a + " " + b})
    return findings

def clean_junk_code_clike(code: str) -> List[Dict]:
    s = code
    changes = []
    # remove asm("nop"); occurrences
    s_new = re.sub(r'\basm\s*\(\s*".*?nop.*?"\s*\)\s*;', '', s, flags=re.IGNORECASE|re.DOTALL)
    if s_new != s:
        changes.append({"original": s, "cleaned": s_new, "reason": "Removed inline asm NOPs (C-like)"})
        s = s_new
    # remove identity ops x = x + 0 or x = x * 1
    s_new = re.sub(r'\b([A-Za-z_]\w*)\s*=\s*\1\s*\+\s*0\s*;', '', s)
    s_new = re.sub(r'\b([A-Za-z_]\w*)\s*=\s*\1\s*\*\s*1\s*;', s_new)
    if s_new != s:
        changes.append({"original": s, "cleaned": s_new, "reason": "Removed identity arithmetic (x = x + 0 / x = x * 1)"})
        s = s_new
    # remove consecutive dead-store sequences conservatively: drop the earlier assignment
    lines = s.splitlines()
    out_lines = []
    i = 0
    while i < len(lines):
        if i < len(lines)-1:
            a = lines[i].strip(); b = lines[i+1].strip()
            m1 = re.match(r'([A-Za-z_]\w*)\s*=\s*[^;]+;', a)
            m2 = re.match(r'([A-Za-z_]\w*)\s*=\s*[^;]+;', b)
            if m1 and m2 and m1.group(1) == m2.group(1):
                # drop the earlier assignment (conservative)
                changes.append({"original": a + "\n" + b + "\n", "cleaned": b + "\n", "reason": "Removed redundant earlier store (dead store)"})
                out_lines.append(b)
                i += 2
                continue
        out_lines.append(lines[i])
        i += 1
    cleaned = "\n".join(out_lines)
    if cleaned != code and not changes:
        changes.append({"original": code, "cleaned": cleaned, "reason": "Junk cleaning applied (C-like)"})
    elif cleaned != code:
        changes.append({"original": code, "cleaned": cleaned, "reason": "Junk cleaning applied (C-like)"})
    return changes

# Python junk detection (no-ops, redundant ops)
def detect_junk_code_python(code: str) -> List[Dict]:
    findings = []
    # pass statements that do nothing (but pass is meaningful syntactically)
    for m in re.finditer(r'^\s*pass\s*$', code, re.MULTILINE):
        findings.append({"type": "pass_stmt", "lineno": code[:m.start()].count("\n")+1, "snippet": m.group(0)})
    # x = x + 0
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s*=\s*\1\s*\+\s*0\b', code):
        findings.append({"type": "identity_add_zero", "lineno": code[:m.start()].count("\n")+1, "snippet": m.group(0)})
    return findings

def clean_junk_code_python(code: str) -> List[Dict]:
    s = code
    changes = []
    # remove pass lines that are alone
    s_new = re.sub(r'^\s*pass\s*$(?:\n)?', '', s, flags=re.MULTILINE)
    if s_new != s:
        changes.append({"original": s, "cleaned": s_new, "reason": "Removed redundant pass statements"})
        s = s_new
    # remove x = x + 0
    s_new = re.sub(r'\b([A-Za-z_]\w*)\s*=\s*\1\s*\+\s*0\b', r'\1 = \1', s)
    if s_new != s:
        changes.append({"original": s, "cleaned": s_new, "reason": "Removed identity addition (x = x + 0)."})
        s = s_new
    return changes
