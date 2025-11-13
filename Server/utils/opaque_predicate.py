# Opaque Predicate Complex Test Cases

# 1. Always true with redundant check inside loop

"""for i in range(2):
    if (2 + 2 == 4) and (3 > 1):
        print("Loop always true:", i)

# 2. Always false predicate (never executes)
for j in range(3):
    if (5 < 2) or (10 < 3):
        print("This will never print", j)

# 3. Constant comparison with while loop
k = 0
while k < 2:
    if (100 == 100):
        print("While loop always true", k)
    k += 1

# 4. Arithmetic inside comparison
if (2 * 3 == 6) and (4 - 1 == 3):
    print("Inline arithmetic always true")

# 5. Complex but always true condition in function
def check_predicate():
    if (50 - 25 == 25) and (4**2 == 16):
        return "Function always true"
    return "Unreachable"

print(check_predicate())

# 6. Complex but false inside loop
for i in range(2):
    if (9 % 2 == 0) or (7 < 3):
        print("Never executes")

# 7. Nested opaque predicates
if ((10/2) == 5):
    if ((3*3) == 9):
        print("Nested always true")

# 8. Redundant always true inside loop
for i in range(2):
    if (8 > 3) and (2 < 5):
        print("Redundant always true", i)

# 9. Impossible opaque condition
if (1 == 2) or (0 > 10):
    print("Impossible branch")

# 10. Hidden constant compare inside function + loop
def hidden_check(x):
    if (x * 2 == 8) and (16/4 == 4):
        return True
    return False

for val in [4, 5]:
    if hidden_check(val):
        print("Hidden opaque true for", val)"""


# analyzers/opaque_predicate.py
import ast
import re
from typing import List, Dict

# Reuse the same safe AST evaluator from inline_expansion; to avoid circular import, copy minimal evaluator:
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
    if isinstance(node, ast.Compare):
        left = _eval_constant_ast(node.left)
        # single comparator supported
        comp = node.comparators[0]
        right = _eval_constant_ast(comp)
        op = node.ops[0]
        if isinstance(op, ast.Eq): return left == right
        if isinstance(op, ast.NotEq): return left != right
        if isinstance(op, ast.Lt): return left < right
        if isinstance(op, ast.LtE): return left <= right
        if isinstance(op, ast.Gt): return left > right
        if isinstance(op, ast.GtE): return left >= right
    if isinstance(node, ast.BoolOp):
        # evaluate values if possible
        values = [_eval_constant_ast(v) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        else:
            return any(values)
    raise ValueError("Not constant-evaluable")

# ---------------- Python detection/cleaning ----------------
def detect_opaque_predicate_python(code: str) -> List[Dict]:
    findings = []
    try:
        tree = ast.parse(code)
    except Exception as e:
        return [{"type": "parse_error", "reason": str(e)}]
    class V(ast.NodeVisitor):
        def visit_If(self, node):
            # try to evaluate the test
            try:
                val = _eval_constant_ast(node.test)
                findings.append({"type": "opaque_always", "lineno": node.lineno, "value": bool(val), "expr": ast.unparse(node.test)})
            except Exception:
                # check for Compare with constant operands inside BoolOp
                if isinstance(node.test, ast.BoolOp):
                    for v in node.test.values:
                        if isinstance(v, ast.Compare):
                            left = v.left
                            if isinstance(left, ast.BinOp) and isinstance(left.left, ast.Constant) and isinstance(left.right, ast.Constant):
                                findings.append({"type": "opaque_arith", "lineno": node.lineno, "expr": ast.unparse(v)})
            self.generic_visit(node)
    V().visit(tree)
    return findings

def clean_opaque_predicate_python(code: str) -> List[Dict]:
    """
    Replace opaque predicates that evaluate to True with their body,
    remove those that evaluate to False.
    """
    results = []
    try:
        tree = ast.parse(code)
    except Exception as e:
        return [{"original": code, "cleaned": code, "reason": f"parse_error: {e}"}]

    class Transformer(ast.NodeTransformer):
        def __init__(self):
            self.changes = []
        def visit_If(self, node):
            # try eval test
            try:
                val = _eval_constant_ast(node.test)
                orig = ast.unparse(node)
                if bool(val):
                    # keep body (inline)
                    cleaned = "\n".join([ast.unparse(n) for n in node.body])
                    self.changes.append({"original": orig, "cleaned": cleaned, "reason": "Opaque predicate evaluated True -> inlined body"})
                    return node.body
                else:
                    # remove if entirely or keep else if present
                    cleaned = ""
                    if node.orelse:
                        cleaned = "\n".join([ast.unparse(n) for n in node.orelse])
                    self.changes.append({"original": orig, "cleaned": cleaned, "reason": "Opaque predicate evaluated False -> removed or replaced with else"})
                    # replace with else-body if exists
                    return node.orelse or []
            except Exception:
                return self.generic_visit(node)

    t = Transformer()
    new_tree = t.visit(tree)
    try:
        new_code = ast.unparse(new_tree)
    except Exception:
        new_code = code
    results.extend(t.changes)
    results.append({"original": code, "cleaned": new_code, "reason": "Full cleaned file (Python opaque predicate simplification)"})
    return results

# ---------------- C-like detection/cleaning (regex) ----------------
_cmp_re = re.compile(r'\b(\d+(?:\s*[\+\-\*\/]\s*\d+)*)\s*(==|!=|>|<|>=|<=)\s*(\d+(?:\s*[\+\-\*\/]\s*\d+)*)')

def _safe_eval_num_expr(expr: str):
    # only digits, whitespace, and operators allowed
    if not re.fullmatch(r'[0-9\+\-\*\/%\s\(\)]+', expr):
        raise ValueError("unsafe expr")
    # evaluate using Python integer math (floor division)
    # replace / with // for integer division
    expr2 = expr.replace('/', '//')
    return eval(expr2)

def detect_opaque_predicate_clike(code: str, lang="C-like") -> List[Dict]:
    findings = []
    for i, line in enumerate(code.splitlines(), start=1):
        for m in _cmp_re.finditer(line):
            left, op, right = m.groups()
            try:
                lv = _safe_eval_num_expr(left)
                rv = _safe_eval_num_expr(right)
                # compare
                ok = False
                if op == '==': ok = (lv == rv)
                elif op == '!=': ok = (lv != rv)
                elif op == '<': ok = (lv < rv)
                elif op == '<=': ok = (lv <= rv)
                elif op == '>': ok = (lv > rv)
                elif op == '>=': ok = (lv >= rv)
                findings.append({"type": "opaque_cmp_const", "lineno": i, "expr": m.group(0), "value": ok, "lang": lang})
            except Exception:
                findings.append({"type": "opaque_cmp_unknown", "lineno": i, "expr": m.group(0), "lang": lang})
    return findings

def clean_opaque_predicate_clike(code: str) -> List[Dict]:
    """
    For identified constant comparisons, attempt to simplify:
      - if condition is always true: replace `if(cond){block}else{else}` -> keep block
      - if always false: remove block or keep else
    Very conservative textual approach: only handles simple one-line if statements and braced blocks.
    """
    changes = []
    s = code
    # find simple if (...) { ... } else { ... } patterns with constant numeric comparisons inside parentheses
    if_pattern = re.compile(r'if\s*\(\s*([^\)]+)\s*\)\s*(\{(?:[^{}]|\{[^}]*\})*\}|[^\n;]*;)\s*(else\s*(\{(?:[^{}]|\{[^}]*\})*\}|[^\n;]*;))?', re.DOTALL)
    pos = 0
    while True:
        m = if_pattern.search(s, pos)
        if not m:
            break
        cond = m.group(1)
        body = m.group(2)
        else_part = m.group(3) or ""
        try:
            # attempt to evaluate cond if it's a simple arithmetic comparison
            mm = _cmp_re.search(cond)
            if mm:
                left, op, right = mm.groups()
                lv = _safe_eval_num_expr(left)
                rv = _safe_eval_num_expr(right)
                if op == '==': val = (lv == rv)
                elif op == '!=': val = (lv != rv)
                elif op == '<': val = (lv < rv)
                elif op == '<=': val = (lv <= rv)
                elif op == '>': val = (lv > rv)
                elif op == '>=': val = (lv >= rv)
                if val:
                    # keep body, remove if(...) and else
                    cleaned = body
                    changes.append({"original": m.group(0), "cleaned": cleaned, "reason": "Opaque condition evaluated True — inlined body"})
                    s = s[:m.start()] + cleaned + s[m.end():]
                    pos = m.start() + len(cleaned)
                    continue
                else:
                    # remove body, keep else if present
                    cleaned = else_part if else_part else ""
                    changes.append({"original": m.group(0), "cleaned": cleaned, "reason": "Opaque condition evaluated False — removed body / kept else"})
                    s = s[:m.start()] + cleaned + s[m.end():]
                    pos = m.start() + len(cleaned)
                    continue
        except Exception:
            pass
        pos = m.end()
    if changes:
        changes.append({"original": code, "cleaned": s, "reason": "Applied simple opaque predicate simplification (C-like)"})
    return changes
