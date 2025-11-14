# analyzers/mixed_language.py
"""
Detect mixed-language obfuscation signals, such as:
 - inline assembly or ASM blocks inside C/C++  
 - presence of JNI-like bridging code (native method definitions)  
 - generated code markers or embedded Java/Kotlin code segments in C comments
Cleaning: only report and optionally remove pure ASM nop sections or trivial inline assembler used as junk.
"""

import re
from typing import List, Dict

def detect_mixed_language(code: str) -> List[Dict]:
    findings = []
    # inline asm in C: __asm__("..."); or asm("...");
    if re.search(r'\b(__asm__|asm)\s*\(', code):
        findings.append({"type": "inline_asm", "reason": "Inline assembler block detected"})
    # JNI: Java native method / System.loadLibrary or 'jni.h' inclusion
    if re.search(r'#\s*include\s*<jni.h>', code) or re.search(r'System\.loadLibrary', code):
        findings.append({"type": "jni_bridge", "reason": "JNI/native bridge detected"})
    # Kotlin/Java embedded strings (large embedded source snippets)
    if re.search(r'class\s+[A-Z]\w+\s*\{', code) and re.search(r'#include', code):
        findings.append({"type": "mixed_java_c", "reason": "Mixed Java/C code smells (both class and #include present)"})
    return findings

# -------------------- Python cleaning --------------------
def clean_mixed_language_python(code: str) -> List[Dict]:
    changes = []
    # For Python, just detect and annotate mixed constructs (no auto removal)
    findings = detect_mixed_language(code)
    if findings:
        changes.append({"original": "", "cleaned": "", "reason": f"Detected mixed-language constructs: {findings}. No automatic cleaning applied."})
    return changes

# -------------------- C-like cleaning --------------------
def clean_mixed_language_clike(code: str) -> List[Dict]:
    changes = []
    s = code
    # remove asm("nop") etc
    s_new = re.sub(r'\basm\s*\(\s*".*?nop.*?"\s*\)\s*;', '', s, flags=re.DOTALL | re.IGNORECASE)
    if s_new != s:
        changes.append({"original": s, "cleaned": s_new, "reason": "Removed inline asm nop occurrences (mixed-language cleaning)"})
    else:
        findings = detect_mixed_language(code)
        if findings:
            changes.append({"original": "", "cleaned": "", "reason": f"Detected mixed-language constructs: {findings}. No automatic cleaning applied."})
    return changes
