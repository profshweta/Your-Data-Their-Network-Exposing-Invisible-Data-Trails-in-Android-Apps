"""# Inline Expansion Complex Test Cases with Loops

# 1. Constant multiplication inside assignment
a = 12 * 4

# 2. Constant addition inside parentheses
b = (50 + 25)

# 3. Constant exponentiation (square)
c = 9 ** 2

# 4. Function returning inline multiplication
def f1():
    return (2 * 5) + 3

# 5. Inline addition inside an expression
x = (1 + 2) * (3 + 4)

# 6. Inline squaring inside variable assignment
y = (7 ** 2) + (2 ** 2)

# 7. Mixed variable + constant inline addition
z = 10 + (5 + 5)

# 8. Nested multiplications with loop
val = 1
for i in range(2):
    val *= (2 * 3) + (4 * 5)

# 9. Inline expansion inside if-condition inside loop
for i in range(3):
    if (2 + 3) > i:
        print("Inline addition in loop condition", i)

# 10. Inline exponentiation inside nested loop
for i in range(2):
    for j in range(2):
        p = (i + j) * (2 ** 2)
        print("Loop square:", p)

# 11. Inline expansion in while loop
k = 0
while k < (2 + 2):
    k += (3 * 3)
    print("While loop step:", k)

# 12. Inline in function argument (looped calls)
def square_and_add(n):
    return n + (4 ** 2)

for i in range(3):
    print("Function call:", square_and_add(i))"""








# analyzers/inline_expansion.py
import ast
import re
from typing import List, Dict

# Safe AST constant evaluator for arithmetic/comparison (Python)
_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
                   ast.LShift, ast.RShift, ast.BitAnd, ast.BitOr, ast.BitXor, ast.FloorDiv)
_ALLOWED_UNARYOPS = (ast.UAdd, ast.USub, ast.Invert)

def _eval_constant_ast(node):


    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, _ALLOWED_UNARYOPS):
        val = _eval_constant_ast(node.operand)
        if isinstance(node.op, ast.UAdd): return +val
        if isinstance(node.op, ast.USub): return -val
        if isinstance(node.op, ast.Invert): return ~val
    if isinstance(node, ast.BinOp) and isinstance(node.op, _ALLOWED_BINOPS):
        L = _eval_constant_ast(node.left)
        R = _eval_constant_ast(node.right)
        op = node.op
        if isinstance(op, ast.Add): return L + R
        if isinstance(op, ast.Sub): return L - R
        if isinstance(op, ast.Mult): return L * R
        if isinstance(op, ast.Div): return L / R
        if isinstance(op, ast.FloorDiv): return L // R
        if isinstance(op, ast.Mod): return L % R
        if isinstance(op, ast.Pow): return L ** R
        if isinstance(op, ast.LShift): return L << R
        if isinstance(op, ast.RShift): return L >> R
        if isinstance(op, ast.BitAnd): return L & R
        if isinstance(op, ast.BitOr): return L | R
        if isinstance(op, ast.BitXor): return L ^ R
    raise ValueError("Not a constant-evaluable expression")

# ---------------- Python constant folding transformer ----------------
class _ConstantFolder(ast.NodeTransformer):
    def __init__(self):
        self.changes = []
    def visit_BinOp(self, node):
        self.generic_visit(node)
        try:
            val = _eval_constant_ast(node)
            orig = ast.unparse(node)
            new = ast.copy_location(ast.Constant(value=val), node)
            self.changes.append((orig, repr(val), node.lineno))
            return new
        except Exception:
            return node

def detect_inline_expansion_python(code: str) -> List[Dict]:


    findings = []
    try:
        tree = ast.parse(code)
    except Exception as e:
        return [{"type": "parse_error", "reason": str(e)}]
    class V(ast.NodeVisitor):
        def visit_BinOp(self, node):
            try:
                val = _eval_constant_ast(node)
                findings.append({"type": "constant_fold", "lineno": node.lineno, "expr": ast.unparse(node), "value": val})
            except Exception:
                # detect x*x pattern
                if isinstance(node.op, ast.Mult) and isinstance(node.left, ast.Name) and isinstance(node.right, ast.Name) and node.left.id == node.right.id:
                    findings.append({"type": "variable_square", "lineno": node.lineno, "var": node.left.id})
            self.generic_visit(node)
    V().visit(tree)
    return findings

def clean_inline_expansion_python(code: str) -> List[Dict]:


    results = []
    try:
        tree = ast.parse(code)
    except Exception as e:
        return [{"original": code, "cleaned": code, "reason": f"parse_error: {e}"}]
    folder = _ConstantFolder()
    new_tree = folder.visit(tree)
    cleaned_code = None
    try:
        cleaned_code = ast.unparse(new_tree)
    except Exception:
        cleaned_code = code
    for orig, valrepr, lineno in folder.changes:
        results.append({"original": orig, "cleaned": str(valrepr), "lineno": lineno, "reason": "Constant folded"})
    results.append({"original": code, "cleaned": cleaned_code, "reason": "Full cleaned file (Python inline folding)"})
    return results

# ---------------- C-like regex heuristics ----------------
_numop_re = re.compile(r'\b(\d+)\s*([\+\-\*\/%])\s*(\d+)\b')

def detect_inline_expansion_clike(code: str, ext_tag="C-like") -> List[Dict]:
    findings = []
    for i, line in enumerate(code.splitlines(), start=1):
        for m in _numop_re.finditer(line):
            a, op, b = m.groups()
            findings.append({"type": "const_expr", "lineno": i, "expr": m.group(0), "lang": ext_tag})
        if re.search(r'\b(\w+)\s*\*\s*\1\b', line):
            findings.append({"type": "square_pattern", "lineno": i, "expr": line.strip(), "lang": ext_tag})
    return findings

def clean_inline_expansion_clike(code: str) -> List[Dict]:
    
    s = code
    changes = []
    def _eval_match(m):
        a, op, b = m.groups()
        # safe integer arithmetic
        a_i = int(a); b_i = int(b)
        if op == '+': r = a_i + b_i
        elif op == '-': r = a_i - b_i
        elif op == '*': r = a_i * b_i
        elif op == '/':
            if b_i == 0: raise ZeroDivisionError
            r = a_i // b_i
        elif op == '%': r = a_i % b_i
        else:
            raise ValueError
        changes.append({"original": m.group(0), "cleaned": str(r), "reason": "Constant arithmetic folded"})
        return str(r)

    # replace iteratively until no more matches
    while True:
        new, n = _numop_re.subn(lambda m: _eval_match(m), s, count=1)
        if n == 0:
            break
        s = new
    if changes:
        changes.append({"original": code, "cleaned": s, "reason": "Applied simple constant folding (C-like)"})
    return changes







