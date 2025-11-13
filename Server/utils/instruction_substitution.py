# analyzers/instruction_substitution.py
"""
Detect instruction substitution like:
  - x - (-1)  -> x + 1
  - x << 1    -> x * 2
  - x + x     -> 2 * x  (or x * 2)
  - bitwise tricks (x ^ -1) etc.
We'll canonicalize a few safe patterns.
"""

import re
from typing import List, Dict

# Patterns -> canonical replacement
_CLIKE_PATTERNS = [
    # x - (-1)  -> x + 1
    (re.compile(r'([A-Za-z_]\w*)\s*-\s*\(\s*-\s*1\s*\)'), r'\1 + 1', "neg-neg to plus"),
    # x << 1  -> x * 2
    (re.compile(r'([A-Za-z_]\w*)\s*<<\s*1\b'), r'\1 * 2', "shift-left to multiply"),
    # x + x -> 2 * x (note: keep order)
    (re.compile(r'\b([A-Za-z_]\w*)\s*\+\s*\1\b'), r'2 * \1', "x+x to 2*x"),
    # double-negation: --x -> x (in C/C++)
    (re.compile(r'--([A-Za-z_]\w*)'), r'\1', "double-neg"),
]

def detect_instruction_substitution_clike(code: str) -> List[Dict]:
    findings = []
    for pat, repl, reason in _CLIKE_PATTERNS:
        for m in pat.finditer(code):
            findings.append({"type": "instr_sub", "lineno": code[:m.start()].count("\n")+1, "snippet": m.group(0), "suggest": repl, "reason": reason})
    return findings

def clean_instruction_substitution_clike(code: str) -> List[Dict]:
    changes = []
    s = code
    for pat, repl, reason in _CLIKE_PATTERNS:
        # replace all occurrences, record original per replacement
        for m in pat.finditer(s):
            orig = m.group(0)
            # compute replacement on the current match
            new = pat.sub(repl, orig)
            changes.append({"original": orig, "cleaned": new, "reason": f"Canonicalized: {reason}"})
        s = pat.sub(repl, s)
    if changes:
        changes.append({"original": code, "cleaned": s, "reason": "Applied instruction substitution canonicalization (C-like)"})
    return changes

# Python variants (similar)
_PY_PATTERNS = [
    (re.compile(r'([A-Za-z_]\w*)\s*-\s*\(\s*-\s*1\s*\)'), r'\1 + 1', "neg-neg to plus"),
    (re.compile(r'\b([A-Za-z_]\w*)\s*\+\s*\1\b'), r'2 * \1', "x+x to 2*x"),
]

def detect_instruction_substitution_python(code: str) -> List[Dict]:
    findings = []
    for pat, repl, reason in _PY_PATTERNS:
        for m in pat.finditer(code):
            findings.append({"type": "instr_sub_py", "lineno": code[:m.start()].count("\n")+1, "snippet": m.group(0), "suggest": repl, "reason": reason})
    return findings

def clean_instruction_substitution_python(code: str) -> List[Dict]:
    s = code
    changes = []
    for pat, repl, reason in _PY_PATTERNS:
        for m in pat.finditer(s):
            orig = m.group(0)
            new = pat.sub(repl, orig)
            changes.append({"original": orig, "cleaned": new, "reason": f"Canonicalized: {reason}"})
        s = pat.sub(repl, s)
    if changes:
        changes.append({"original": code, "cleaned": s, "reason": "Applied instruction substitution canonicalization (Python)"})
    return changes
