"""# Dead Code Test Cases

# 1. Unused variable
x = 10   # dead
y = 20
print(y)

# 2. If condition always True
if True:
    print("Always runs")
else:
    print("Dead branch")

# 3. If condition always False
if False:
    print("Dead branch")
else:
    print("Always runs")

# 4. Code after return
def f1():
    return 5
    print("Dead")  # dead

# 5. Code after break
for i in range(3):
    break
    print("Dead")  # dead

# 6. Unreachable else
if True:
    print("Run")
else:
    print("Dead")

# 7. While False loop
while False:
    print("Never runs")  # dead

# 8. Constant condition (0 is False)
if 0:
    print("Dead")
else:
    print("Runs")

# 9. Constant condition (non-zero is True)
if 1:
    print("Runs")
else:
    print("Dead")

# 10. Multiple returns
def f2(x):
    if x > 0:
        return 1
        print("Dead")  # dead
    else:
        return -1
"""

# analyzers/deadcode.py
import ast
import re
from typing import List, Dict, Tuple

# --------------------------
# Python (AST) helpers
# --------------------------
class _DeadCodeRemover(ast.NodeTransformer):
    """
    Transformations:
      - remove `if False: ...` blocks
      - replace `if True: body` with `body` (in-place)
      - record lines removed
    """
    def __init__(self):
        self.changes = []

    def visit_If(self, node: ast.If):
        # evaluate constant tests only
        try:
            if isinstance(node.test, ast.Constant):
                val = node.test.value
                if val is False:
                    original = ast.get_source_segment(self.source_text, node) if hasattr(self, "source_text") else ast.unparse(node)
                    # remove the entire if-block
                    self.changes.append((original, "", "If condition is constant False (dead code)"))
                    return None  # remove node
                elif val is True:
                    # keep body in place of if
                    body_nodes = [self.visit(b) for b in node.body]
                    original = ast.get_source_segment(self.source_text, node) if hasattr(self, "source_text") else ast.unparse(node)
                    cleaned = "\n".join([ast.unparse(b) for b in body_nodes if b is not None])
                    self.changes.append((original, cleaned, "If condition is constant True (inlined body)"))
                    return body_nodes  # splice body
        except Exception:
            pass
        self.generic_visit(node)
        return node

    def run(self, tree: ast.AST, source_text: str):
        self.source_text = source_text
        new_tree = self.visit(tree)
        return new_tree, self.changes


def detect_deadcode_python(code: str) -> List[Dict]:
    """
    Detect dead-code patterns in Python source using AST scanning.
    Returns list of findings (simple descriptions and line numbers).
    """
    findings = []
    try:
        tree = ast.parse(code)
    except Exception as e:
        findings.append({"type": "parse_error", "reason": str(e)})
        return findings

    # If/While constant tests
    class V(ast.NodeVisitor):
        def visit_If(self, node):
            if isinstance(node.test, ast.Constant):
                if node.test.value is False:
                    findings.append({"type": "dead_if_false", "lineno": node.lineno, "snippet": ast.unparse(node.test)})
                elif node.test.value is True:
                    findings.append({"type": "dead_else", "lineno": node.lineno, "snippet": ast.unparse(node.test)})
            self.generic_visit(node)

        def visit_While(self, node):
            if isinstance(node.test, ast.Constant) and node.test.value is False:
                findings.append({"type": "dead_while_false", "lineno": node.lineno})
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            # detect code after return in function body
            for i, stmt in enumerate(node.body):
                if isinstance(stmt, ast.Return):
                    for later in node.body[i+1:]:
                        findings.append({"type": "dead_after_return", "lineno": getattr(later, "lineno", None), "func": node.name})
            self.generic_visit(node)

        def visit_Assign(self, node):
            # naive assigned variable capture (we'll refine in unused)
            self.generic_visit(node)

    V().visit(tree)

    # Unused variables: track simple assignments and loads
    assigned = {}
    used = set()
    class U(ast.NodeVisitor):
        def visit_Assign(self, node):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                assigned[node.targets[0].id] = getattr(node, "lineno", None)
            self.generic_visit(node)
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                used.add(node.id)
    U().visit(tree)
    for var, lineno in assigned.items():
        if var not in used:
            findings.append({"type": "unused_var", "var": var, "lineno": lineno})

    return findings


def clean_deadcode_python(code: str) -> List[Dict]:
    """
    Attempt to remove dead code in Python source.
    Returns list of changes: {"original":..., "cleaned":..., "reason":...}
    """
    results = []
    try:
        tree = ast.parse(code)
    except Exception as e:
        return [{"original": code, "cleaned": code, "reason": f"parse_error: {e}"}]

    remover = _DeadCodeRemover()
    new_tree, changes = remover.run(tree, code)
    # unparse new_tree (may be list when splicing body — handle carefully)
    try:
        cleaned_code = ast.unparse(new_tree) if not isinstance(new_tree, list) else "\n".join(ast.unparse(n) for n in new_tree)
    except Exception:
        # fallback: do not change
        cleaned_code = code

    for orig, cleaned, reason in changes:
        results.append({"original": orig, "cleaned": cleaned, "reason": reason})

    # Also remove simple unused assignments by regex (safe: only single-name assigns to literal)
    # e.g., `x = 4` where x not used — remove those lines if they exist exactly.
    # We already reported unused vars above; here perform textual removal for simple case.
    facts = detect_deadcode_python(code)
    for f in facts:
        if f.get("type") == "unused_var" and isinstance(f.get("lineno"), int):
            lines = cleaned_code.splitlines()
            idx = f["lineno"] - 1
            if 0 <= idx < len(lines):
                orig_line = lines[idx]
                # verify assignment pattern
                if re.match(r'^\s*' + re.escape(f["var"]) + r'\s*=\s*[^#\n]+', orig_line):
                    lines[idx] = ""  # remove
                    results.append({"original": orig_line + "\n", "cleaned": "", "reason": f"Removed unused assignment '{f['var']}'"})
                    cleaned_code = "\n".join(lines)
    # Return changes and cleaned code appended as last item
    results.append({"original": code, "cleaned": cleaned_code, "reason": "Full cleaned file (Python deadcode removal)"})
    return results


# --------------------------
# C-like regex helpers
# --------------------------
def detect_deadcode_clike(code: str, ext_tag: str = "C-like") -> List[Dict]:
    findings = []
    lines = code.splitlines()
    for i, line in enumerate(lines, start=1):
        if re.search(r'\bif\s*\(\s*(false|0)\s*\)', line, re.IGNORECASE):
            findings.append({"type": "dead_if_false", "lineno": i, "snippet": line.strip(), "lang": ext_tag})
        if re.search(r'\bwhile\s*\(\s*(false|0)\s*\)', line, re.IGNORECASE):
            findings.append({"type": "dead_while_false", "lineno": i, "snippet": line.strip(), "lang": ext_tag})
        if re.search(r'\breturn\b.*;', line) and i < len(lines) and lines[i].strip():
            findings.append({"type": "after_return", "lineno": i+1, "snippet": lines[i].strip(), "lang": ext_tag})
    return findings


def clean_deadcode_clike(code: str) -> List[Dict]:
    """
    Clean simple C-like dead code:
      - remove `if(false) { ... }` blocks
      - replace `if(true) { ... }` with block contents (strip braces)
      - remove single-line unused var assignments that are literal and not used elsewhere (conservative)
    Returns list of changes
    """
    changes = []
    s = code

    # remove if(false) { ... } or if(false) statement;
    pattern_false_block = re.compile(r'\bif\s*\(\s*(?:false|0)\s*\)\s*(\{(?:[^{}]*|\{[^}]*\})*\}|[^;]*;)', re.IGNORECASE | re.DOTALL)
    while True:
        m = pattern_false_block.search(s)
        if not m: break
        orig = m.group(0)
        s = s[:m.start()] + s[m.end():]
        changes.append({"original": orig, "cleaned": "", "reason": "if(false) removed (dead code)"})

    # inline if(true) { block } => replace with block contents
    pattern_true_block = re.compile(r'\bif\s*\(\s*(?:true|1)\s*\)\s*(\{(?:[^{}]*|\{[^}]*\})*\}|[^;]*;)', re.IGNORECASE | re.DOTALL)
    while True:
        m = pattern_true_block.search(s)
        if not m: break
        orig = m.group(0)
        blk = m.group(1)
        # strip outer braces if present
        if blk.strip().startswith("{") and blk.strip().endswith("}"):
            inner = blk.strip()[1:-1]
        else:
            inner = blk
        s = s[:m.start()] + inner + s[m.end():]
        changes.append({"original": orig, "cleaned": inner, "reason": "if(true) inlined (kept body)"})

    # conservative removal of simple unused assignments: pattern `int x = 4;` only if var name does not appear elsewhere
    assign_pattern = re.compile(r'\b(?:int|long|char|float|double)\s+([A-Za-z_]\w*)\s*=\s*[^;]+;')
    for m in assign_pattern.finditer(s):
        var = m.group(1)
        # if var occurs only once (the definition), remove it
        if len(re.findall(r'\b' + re.escape(var) + r'\b', s)) == 1:
            orig = m.group(0)
            s = s[:m.start()] + s[m.end():]
            changes.append({"original": orig, "cleaned": "", "reason": f"Removed likely-unused declaration '{var}'"})

    changes.append({"original": code, "cleaned": s, "reason": "Full cleaned file (C-like deadcode removal)"})
    return changes
