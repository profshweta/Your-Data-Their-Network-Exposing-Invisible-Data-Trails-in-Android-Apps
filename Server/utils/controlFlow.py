# -------------------- controlflow.py --------------------
import re
from typing import List, Dict, Tuple

class FakeConditionCleaner:
    """
    Detect and clean fake/unreachable conditions from source code.
    Reports detailed mapping of:
        - original (obfuscated) code snippet
        - cleaned (deobfuscated) snippet
        - reason for change
    """

    def __init__(self):
        # Patterns for fake conditions
        self.python_patterns = [
            (re.compile(r'if\s+False\s*:\s*', re.IGNORECASE), "Unreachable branch (condition always False)"),
            (re.compile(r'if\s+True\s*:\s*', re.IGNORECASE), "Always-true condition simplified (kept body, removed if header)"),
            (re.compile(r'if\s+[^\n]*>\s*\d+\s+and\s+[^\n]*<\s*\d+\s*:\s*', re.IGNORECASE),
             "Contradictory numeric range in condition (impossible)")
        ]

        self.c_like_patterns = [
            (re.compile(r'if\s*\(\s*(false|0)\s*\)', re.IGNORECASE), "Unreachable branch (condition always false)"),
            (re.compile(r'if\s*\(\s*(true|1)\s*\)', re.IGNORECASE), "Always-true condition simplified (kept statement/block, removed condition header)"),
            (re.compile(r'if\s*\([^)]*>\s*\d+\s*&&\s*[^)]*<\s*\d+\)', re.IGNORECASE),
             "Contradictory numeric range in condition (impossible)")
        ]

    # ---------- Python helper ----------
    def _extract_python_if_block(self, code: str, match_start: int) -> Tuple[str, str]:
        header_end = code.find('\n', match_start)
        if header_end == -1:
            return code[match_start:], code[:match_start]

        header = code[match_start:header_end+1]
        body_start = header_end + 1
        end = body_start
        while True:
            if end >= len(code):
                break
            nl = code.find('\n', end)
            if nl == -1:
                nl = len(code)
            line = code[end:nl]
            if not line or not (line[0] == ' ' or line[0] == '\t'):
                break
            end = nl + 1
        removed = code[match_start:end]
        new_code = code[:match_start] + code[end:]
        return removed, new_code

    def _dedent_python_body(self, body_text: str) -> str:
        lines = body_text.splitlines()
        indents = [len(re.match(r'^[ \t]+', ln).group(0)) for ln in lines if ln.strip() and re.match(r'^[ \t]+', ln)]
        if not indents:
            return "\n".join(lines) + ("\n" if body_text.endswith("\n") else "")
        min_indent = min(indents)
        dedented_lines = [ln[min_indent:] if len(ln) >= min_indent else ln for ln in lines]
        return "\n".join(dedented_lines) + ("\n" if body_text.endswith("\n") else "")

    # ---------- C-like helper ----------
    def _extract_c_like_block_or_line(self, code: str, start_idx: int) -> Tuple[str, str]:
        i = start_idx
        while i < len(code) and code[i].isspace():
            i += 1
        if i < len(code) and code[i] == '{':
            stack = ['{']
            end = i + 1
            while stack and end < len(code):
                if code[end] == '{': stack.append('{')
                elif code[end] == '}': stack.pop()
                end += 1
            removed = code[start_idx:end]
            return removed, code[:start_idx] + code[end:]
        else:
            end = i
            while end < len(code) and code[end] not in (';', '\n'):
                end += 1
            if end < len(code) and code[end] == ';': end += 1
            removed = code[start_idx:end]
            return removed, code[:start_idx] + code[end:]

    # ---------- Detection ----------
    def detect_fake_conditions(self, code: str) -> List[Dict]:
        findings = []

        # Python
        for pat, reason in self.python_patterns:
            for m in pat.finditer(code):
                findings.append({"condition": m.group(0), "position": m.start(), "reason": reason})

        # C-like
        for pat, reason in self.c_like_patterns:
            for m in pat.finditer(code):
                findings.append({"condition": m.group(0), "position": m.start(), "reason": reason})

        return findings

    # ---------- Cleaning ----------
    def clean_code(self, code: str) -> List[Dict]:
        """
        Returns a list of changes:
        [
            {"original": ..., "cleaned": ..., "reason": ...},
            ...
        ]
        """
        changes = []
        cleaned_code = code

        # Python patterns
        for pat, reason in self.python_patterns:
            while True:
                m = pat.search(cleaned_code)
                if not m: break
                start = m.start()
                removed, cleaned_code = self._extract_python_if_block(cleaned_code, start)
                if "True" in m.group(0):
                    header_end = removed.find('\n')
                    body = removed[header_end+1:] if header_end != -1 else ""
                    dedented_body = self._dedent_python_body(body)
                    cleaned_code = cleaned_code[:start] + dedented_body + cleaned_code[start:]
                    changes.append({"original": removed, "cleaned": dedented_body, "reason": reason})
                else:
                    changes.append({"original": removed, "cleaned": "", "reason": reason})

        # C-like patterns
        for pat, reason in self.c_like_patterns:
            while True:
                m = pat.search(cleaned_code)
                if not m: break
                start = m.start()
                removed, cleaned_code = self._extract_c_like_block_or_line(cleaned_code, start)
                if "true" in m.group(0).lower() or "1" in m.group(0):
                    # Keep block/statement only
                    if '{' in removed:
                        block_start = removed.find('{')
                        block = removed[block_start:]
                        cleaned_code = cleaned_code[:start] + block + cleaned_code[start:]
                        changes.append({"original": removed, "cleaned": block, "reason": reason})
                    else:
                        # single statement
                        stmt = removed[m.end()-start:]
                        cleaned_code = cleaned_code[:start] + stmt + cleaned_code[start:]
                        changes.append({"original": removed, "cleaned": stmt, "reason": reason})
                else:
                    changes.append({"original": removed, "cleaned": "", "reason": reason})

        return changes