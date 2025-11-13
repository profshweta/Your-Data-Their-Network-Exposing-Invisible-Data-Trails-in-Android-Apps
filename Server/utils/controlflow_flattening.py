# analyzers/controlflow_flattening.py
"""
Detect/control-flow flattening patterns (dispatcher loops, state-machine switch inside loop).
Conservative detection + optional simple unflatten attempt (only for tiny patterns).
"""

import re
import ast
from typing import List, Dict

def detect_controlflow_flattening_clike(code: str) -> List[Dict]:
    findings = []
    # Very common flattening pattern: state variable + while/switch inside
    pattern = re.compile(r'\bwhile\s*\(\s*(?:1|true)\s*\)\s*\{.*?\b(switch|if)\s*\s*\([^)]*\)\s*\{', re.IGNORECASE | re.DOTALL)
    if pattern.search(code):
        findings.append({"type": "dispatcher_loop", "reason": "while(true)/switch dispatcher pattern", "hint": "control-flow flattening (C-like)"})
    # state variable updates: look for `state = <const>` inside switch cases
    if re.search(r'\bstate\s*=\s*\d+\s*;', code):
        findings.append({"type": "state_var", "reason": "state variable updated inside loop", "hint": "possible flattened flow"})
    return findings

def clean_controlflow_flattening_clike(code: str) -> List[Dict]:
    """
    Conservative: we will not attempt full de-flattening.
    Instead, we:
      - detect small dispatcher with 2-3 cases and produce a suggested straight-line replacement as text,
        but do not modify code automatically unless pattern exactly matches a simple form.
    Returns list of change dicts; last item contains full cleaned placeholder if applied.
    """
    changes = []
    # match a simple dispatcher with two cases that assign/accumulate to result and exit
    m = re.search(r'while\s*\(\s*(?:1|true)\s*\)\s*\{\s*switch\s*\(\s*state\s*\)\s*\{\s*(case\s*1\s*:\s*([^}]*)break\s*;)\s*(case\s*2\s*:\s*([^}]*)break\s*;)\s*\}\s*\}', code, re.DOTALL | re.IGNORECASE)
    if m:
        case1 = m.group(2).strip()
        case2 = m.group(4).strip()
        # attempt to extract simple assignments that produce pieces of result
        # produce a suggested deobfuscated snippet
        suggested = "// Suggested deobfuscated sequence\n" + "/* case1 */\n" + case1 + "\n/* case2 */\n" + case2 + "\n"
        changes.append({"original": m.group(0), "cleaned": suggested, "reason": "Simple dispatcher unflattened into sequential suggestions"})
        # produce cleaned file placeholder (conservative)
        cleaned = code[:m.start()] + suggested + code[m.end():]
        changes.append({"original": code, "cleaned": cleaned, "reason": "Applied small-scope unflatten (C-like) - manual review required"})
    else:
        # no safe automatic transform; only report detection
        if detect_controlflow_flattening_clike(code):
            changes.append({"original": "", "cleaned": "", "reason": "Detected control-flow flattening patterns, no automatic rewrite performed (too risky)."})
    return changes

def detect_controlflow_flattening_python(code: str) -> List[Dict]:
    # Python rarely uses switch; detect weird while True + dict dispatch / state var patterns
    findings = []
    if re.search(r'while\s+True\s*:\s*', code):
        # look for dict dispatch / if chain inside loop
        if re.search(r'\b(state|mode)\b', code) and re.search(r'\bif\b.*\belse\b', code, re.DOTALL):
            findings.append({"type": "dispatcher_loop_py", "reason": "while True with state/if-dispatch found"})
    # dict-based dispatcher: table = {0: lambda: ..., 1: lambda: ...}; table[state]()
    if re.search(r'\{.*lambda.*:.*\}', code, re.DOTALL):
        findings.append({"type": "dict_dispatch", "reason": "dictionary-based dispatcher (python)"})
    return findings

def clean_controlflow_flattening_python(code: str) -> List[Dict]:
    # No safe fully automated de-flattening. Provide hints only.
    findings = detect_controlflow_flattening_python(code)
    if findings:
        return [{"original": "", "cleaned": "", "reason": "Detected Python flattened control-flow patterns. Manual reconstruction recommended."}]
    return []
