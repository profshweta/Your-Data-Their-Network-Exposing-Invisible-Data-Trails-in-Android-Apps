"""import ast
import sys
import os

# --- Your analyzers here ---
class DeadCodeDetector(ast.NodeVisitor):
    def visit_If(self, node):
        if isinstance(node.test, ast.Constant):
            if node.test.value is True:
                print(f"[Dead Code] Else branch is unreachable at line {node.lineno}")
            elif node.test.value is False:
                print(f"[Dead Code] If branch is unreachable at line {node.lineno}")
        self.generic_visit(node)

class InlineExpansionDetector(ast.NodeVisitor):
    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Mult):
            if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                print(f"[Inline Expansion] Constant multiplication at line {node.lineno}: {ast.unparse(node)}")

        if isinstance(node.op, ast.Add):
            if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                print(f"[Inline Expansion] Constant addition at line {node.lineno}: {ast.unparse(node)}")

        if isinstance(node.op, ast.Pow):
            if isinstance(node.right, ast.Constant) and node.right.value == 2:
                print(f"[Inline Expansion] Squaring detected at line {node.lineno}: {ast.unparse(node)}")

        self.generic_visit(node)

class OpaquePredicateDetector(ast.NodeVisitor):
    def visit_If(self, node):
        if isinstance(node.test, ast.BoolOp):
            for value in node.test.values:
                if isinstance(value, ast.Compare):
                    if isinstance(value.left, ast.Constant):
                        print(f"[Opaque Predicate] Constant comparison at line {node.lineno}: {ast.unparse(value)}")

                    if isinstance(value.left, ast.BinOp) and all(
                        isinstance(child, ast.Constant) for child in [value.left.left, value.left.right]
                    ):
                        print(f"[Opaque Predicate] Arithmetic constant comparison at line {node.lineno}: {ast.unparse(value)}")
        self.generic_visit(node)


def analyze_code(code):
    try:
        tree = ast.parse(code)
        print("\n--- Analysis Results ---\n")
        DeadCodeDetector().visit(tree)
        InlineExpansionDetector().visit(tree)
        OpaquePredicateDetector().visit(tree)
        print("\n--- Analysis Completed ---")
    except Exception as e:
        print("Error while analyzing code:", e)


def main():
    if len(sys.argv) < 3:
        print("Usage: python analyzer.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, "r") as f:
        code = f.read()

    # Redirect stdout to output file
    original_stdout = sys.stdout
    with open(output_file, "w") as f:
        sys.stdout = f
        analyze_code(code)
        sys.stdout = original_stdout

    print(f"Analysis complete. Results saved to {output_file}")


if __name__ == "__main__":
    main()
"""





"""

import ast
import sys
import os

# ------------------- DEAD CODE DETECTOR -------------------
class DeadCodeDetector(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.assigned = set()
        self.used = set()

    def visit_If(self, node):
        if isinstance(node.test, ast.Constant):
            if node.test.value is True:
                print(f"[Dead Code] Else branch is unreachable at line {node.lineno}")
            elif node.test.value is False:
                print(f"[Dead Code] If branch is unreachable at line {node.lineno}")
        self.generic_visit(node)

    def visit_While(self, node):
        if isinstance(node.test, ast.Constant) and node.test.value is False:
            print(f"[Dead Code] While loop never executes at line {node.lineno}")
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.Return):
                for later_stmt in node.body[i+1:]:
                    print(f"[Dead Code] Code after return at line {later_stmt.lineno} inside function '{node.name}'")
        self.generic_visit(node)

    def visit_For(self, node):
        for stmt in node.body:
            if isinstance(stmt, ast.Break):
                idx = node.body.index(stmt)
                for later in node.body[idx+1:]:
                    print(f"[Dead Code] Code after break at line {later.lineno} in for loop")
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            self.assigned.add(node.targets[0].id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        self.generic_visit(node)

    def report_unused(self):
        unused = self.assigned - self.used
        for var in unused:
            print(f"[Dead Code] Variable '{var}' assigned but never used")

# ------------------- INLINE EXPANSION DETECTOR -------------------
class InlineExpansionDetector(ast.NodeVisitor):
    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Mult):
            if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                print(f"[Inline Expansion] Constant multiplication at line {node.lineno}: {ast.unparse(node)}")

        if isinstance(node.op, ast.Add):
            if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                print(f"[Inline Expansion] Constant addition at line {node.lineno}: {ast.unparse(node)}")

        if isinstance(node.op, ast.Pow):
            if isinstance(node.right, ast.Constant) and node.right.value == 2:
                print(f"[Inline Expansion] Squaring detected at line {node.lineno}: {ast.unparse(node)}")

        self.generic_visit(node)

# ------------------- OPAQUE PREDICATE DETECTOR -------------------
class OpaquePredicateDetector(ast.NodeVisitor):
    def visit_If(self, node):
        if isinstance(node.test, ast.BoolOp):
            for value in node.test.values:
                if isinstance(value, ast.Compare):
                    if isinstance(value.left, ast.Constant):
                        print(f"[Opaque Predicate] Constant comparison at line {node.lineno}: {ast.unparse(value)}")

                    if isinstance(value.left, ast.BinOp) and all(
                        isinstance(child, ast.Constant) for child in [value.left.left, value.left.right]
                    ):
                        print(f"[Opaque Predicate] Arithmetic constant comparison at line {node.lineno}: {ast.unparse(value)}")
        self.generic_visit(node)

# ------------------- ANALYSIS FUNCTION -------------------
def analyze_code(code, filename):
    try:
        print(f"\n===== Analyzing File: {filename} =====\n")
        tree = ast.parse(code)

        dead_detector = DeadCodeDetector()
        dead_detector.visit(tree)
        dead_detector.report_unused()

        InlineExpansionDetector().visit(tree)
        OpaquePredicateDetector().visit(tree)

        print(f"\n===== Completed: {filename} =====\n")
    except Exception as e:
        print(f"Error analyzing {filename}: {e}")

# ------------------- MAIN -------------------
def main():
    input_folder = "input"
    output_file = "output/combined_results.out"

    if not os.path.exists("output"):
        os.makedirs("output")

    original_stdout = sys.stdout
    with open(output_file, "w") as f:
        sys.stdout = f

        for filename in os.listdir(input_folder):
            if filename.endswith(".py"):
                file_path = os.path.join(input_folder, filename)
                with open(file_path, "r") as infile:
                    code = infile.read()
                analyze_code(code, filename)

        sys.stdout = original_stdout

    print(f"✅ Combined analysis complete. Results saved in {output_file}")


if __name__ == "__main__":
    main()
"""

"""
import os
import sys
import re
import ast

# -------------------- PYTHON ANALYZER (AST) --------------------
class PythonAnalyzer:
    def analyze(self, code, filename):
        print(f"\n===== Analyzing Python File: {filename} =====\n")
        try:
            tree = ast.parse(code)

            dead = DeadCodeDetector()
            dead.visit(tree)
            dead.report_unused()

            InlineExpansionDetector().visit(tree)
            OpaquePredicateDetector().visit(tree)

        except Exception as e:
            print(f"Error analyzing Python file {filename}: {e}")


class DeadCodeDetector(ast.NodeVisitor):
    def __init__(self):
        self.assigned = set()
        self.used = set()

    def visit_If(self, node):
        if isinstance(node.test, ast.Constant):
            if node.test.value is True:
                print(f"[Dead Code] Else branch unreachable at line {node.lineno}")
            elif node.test.value is False:
                print(f"[Dead Code] If branch unreachable at line {node.lineno}")
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            self.assigned.add(node.targets[0].id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)

    def report_unused(self):
        for var in self.assigned - self.used:
            print(f"[Dead Code] Variable '{var}' assigned but never used")


class InlineExpansionDetector(ast.NodeVisitor):
    def visit_BinOp(self, node):
        if isinstance(node.op, (ast.Add, ast.Mult, ast.Pow)):
            if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                print(f"[Inline Expansion] Constant expression at line {node.lineno}: {ast.unparse(node)}")
        self.generic_visit(node)


class OpaquePredicateDetector(ast.NodeVisitor):
    def visit_If(self, node):
        if isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Constant):
            print(f"[Opaque Predicate] Constant condition at line {node.lineno}: {ast.unparse(node)}")
        self.generic_visit(node)


# -------------------- REGEX ANALYZER (C, C++, JAVA, KOTLIN) --------------------
class RegexAnalyzer:
    def analyze(self, code, filename):
        print(f"\n===== Analyzing File: {filename} =====\n")

        lines = code.split("\n")
        for i, line in enumerate(lines, start=1):

            # Dead code detection
            if re.search(r"\bif\s*\(\s*false\s*\)", line) or re.search(r"\bwhile\s*\(\s*false\s*\)", line):
                print(f"[Dead Code] Unreachable branch at line {i}: {line.strip()}")
            if re.search(r"\breturn\b.*;", line) and i < len(lines) and lines[i].strip():
                print(f"[Dead Code] Possible code after return at line {i+1}: {lines[i].strip()}")

            # Inline expansion detection
            if re.search(r"\d+\s*[\+\-\*\/]\s*\d+", line):
                print(f"[Inline Expansion] Constant expression at line {i}: {line.strip()}")
            if re.search(r"\b(\w+)\s*\*\s*\1\b", line):  # x*x
                print(f"[Inline Expansion] Squaring detected at line {i}: {line.strip()}")

            # Opaque predicate detection
            if re.search(r"\bif\s*\(\s*\d+\s*(==|!=|>|<|>=|<=)\s*\d+\s*\)", line):
                print(f"[Opaque Predicate] Constant comparison at line {i}: {line.strip()}")

        print(f"\n===== Completed: {filename} =====\n")


# -------------------- HANDLER --------------------
def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    ext = os.path.splitext(filepath)[1]
    if ext == ".py":
        PythonAnalyzer().analyze(code, filepath)
    elif ext in [".c", ".cpp", ".java", ".kt"]:
        RegexAnalyzer().analyze(code, filepath)
    else:
        print(f"Skipping unsupported file: {filepath}")


def main():
    input_folder = "input"
    output_file = "output/combined_results.out"

    if not os.path.exists("output"):
        os.makedirs("output")

    original_stdout = sys.stdout
    with open(output_file, "w", encoding="utf-8") as f:
        sys.stdout = f
        for filename in os.listdir(input_folder):
            file_path = os.path.join(input_folder, filename)
            analyze_file(file_path)
        sys.stdout = original_stdout

    print(f"✅ Multi-language analysis complete. Results saved in {output_file}")


if __name__ == "__main__":
    main()


"""




"""
import os
import sys
import re
import ast
from io import StringIO

# -------------------- PDF EXPORT --------------------
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


def save_pdf(results, pdf_path="output/combined_results.pdf"):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=20
    )
    normal_style = ParagraphStyle(
        name="NormalStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
    )

    content = []
    content.append(Paragraph("🔍 Code Analysis Results", title_style))
    content.append(Spacer(1, 12))

    for line in results.split("\n"):
        if line.strip().startswith("====="):  # Add section separator
            content.append(PageBreak())
            content.append(Paragraph(line.strip(), styles["Heading2"]))
            content.append(Spacer(1, 12))
        else:
            content.append(Paragraph(line.replace("→", "->"), normal_style))
            content.append(Spacer(1, 6))

    doc.build(content)
    print(f"📄 PDF saved at {pdf_path}")


# -------------------- PYTHON ANALYZER (AST) --------------------
class PythonAnalyzer:
    def analyze(self, code, filename):
        print(f"\n===== Analyzing Python File: {filename} =====\n")
        try:
            tree = ast.parse(code)

            dead = DeadCodeDetector()
            dead.visit(tree)
            dead.report_unused()

            InlineExpansionDetector().visit(tree)
            OpaquePredicateDetector().visit(tree)

        except Exception as e:
            print(f"Error analyzing Python file {filename}: {e}")


class DeadCodeDetector(ast.NodeVisitor):
    def __init__(self):
        self.assigned = set()
        self.used = set()

    def visit_If(self, node):
        if isinstance(node.test, ast.Constant):
            if node.test.value is True:
                print(f"[Dead Code] Else branch unreachable at line {node.lineno}")
            elif node.test.value is False:
                print(f"[Dead Code] If branch unreachable at line {node.lineno}")
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            self.assigned.add(node.targets[0].id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)

    def report_unused(self):
        for var in self.assigned - self.used:
            print(f"[Dead Code] Variable '{var}' assigned but never used")


class InlineExpansionDetector(ast.NodeVisitor):
    def visit_BinOp(self, node):
        if isinstance(node.op, (ast.Add, ast.Mult, ast.Pow)):
            if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                print(f"[Inline Expansion] Constant expression at line {node.lineno}: {ast.unparse(node)}")
        self.generic_visit(node)


class OpaquePredicateDetector(ast.NodeVisitor):
    def visit_If(self, node):
        if isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Constant):
            print(f"[Opaque Predicate] Constant condition at line {node.lineno}: {ast.unparse(node)}")
        self.generic_visit(node)


# -------------------- REGEX ANALYZER (C, C++, JAVA, KOTLIN) --------------------
class RegexAnalyzer:
    def analyze(self, code, filename):
        print(f"\n===== Analyzing File: {filename} =====\n")

        lines = code.split("\n")
        for i, line in enumerate(lines, start=1):

            # Dead code detection
            if re.search(r"\bif\s*\(\s*false\s*\)", line) or re.search(r"\bwhile\s*\(\s*false\s*\)", line):
                print(f"[Dead Code] Unreachable branch at line {i}: {line.strip()}")
            if re.search(r"\breturn\b.*;", line) and i < len(lines) and lines[i].strip():
                print(f"[Dead Code] Possible code after return at line {i+1}: {lines[i].strip()}")

            # Inline expansion detection
            if re.search(r"\d+\s*[\+\-\*\/]\s*\d+", line):
                print(f"[Inline Expansion] Constant expression at line {i}: {line.strip()}")
            if re.search(r"\b(\w+)\s*\*\s*\1\b", line):  # x*x
                print(f"[Inline Expansion] Squaring detected at line {i}: {line.strip()}")

            # Opaque predicate detection
            if re.search(r"\bif\s*\(\s*\d+\s*(==|!=|>|<|>=|<=)\s*\d+\s*\)", line):
                print(f"[Opaque Predicate] Constant comparison at line {i}: {line.strip()}")

        print(f"\n===== Completed: {filename} =====\n")


# -------------------- HANDLER --------------------
def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    ext = os.path.splitext(filepath)[1]
    if ext == ".py":
        PythonAnalyzer().analyze(code, filepath)
    elif ext in [".c", ".cpp", ".java", ".kt"]:
        RegexAnalyzer().analyze(code, filepath)
    else:
        print(f"Skipping unsupported file: {filepath}")


def main():
    input_folder = "input"
    output_file = "output/combined_results.out"

    if not os.path.exists("output"):
        os.makedirs("output")

    # Capture output in memory
    buffer = StringIO()
    original_stdout = sys.stdout
    sys.stdout = buffer

    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        analyze_file(file_path)

    sys.stdout = original_stdout
    results = buffer.getvalue()

    # Save TXT
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(results)

    # Save PDF
    save_pdf(results)

    print(f"✅ Multi-language analysis complete. Results saved in {output_file} and PDF.")


if __name__ == "__main__":
    main()
"""



"""

import os
import sys
import re
import ast
from io import StringIO

# Your custom modules
from input.nameIdentifier import IdentifierCleaner, detect_language
from input.controlFlow import FakeConditionCleaner
from input.stringEncryption import StringDecryptor

# -------------------- PDF EXPORT --------------------
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def save_pdf(results, pdf_path="output/combined_results.pdf"):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=20
    )
    normal_style = ParagraphStyle(
        name="NormalStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
    )

    content = [Paragraph("🔍 Code Analysis Results", title_style), Spacer(1,12)]
    for line in results.split("\n"):
        if line.strip().startswith("====="):
            content.append(PageBreak())
            content.append(Paragraph(line.strip(), styles["Heading2"]))
            content.append(Spacer(1,12))
        else:
            content.append(Paragraph(line.replace("→","->"), normal_style))
            content.append(Spacer(1,6))

    doc.build(content)
    print(f"📄 PDF saved at {pdf_path}")

# -------------------- ANALYZERS --------------------
class DeadCodeDetector(ast.NodeVisitor):
    def __init__(self):
        self.assigned = set()
        self.used = set()
    def visit_If(self, node):
        if isinstance(node.test, ast.Constant):
            if node.test.value is True:
                print(f"[Dead Code] Else branch unreachable at line {node.lineno}")
            elif node.test.value is False:
                print(f"[Dead Code] If branch unreachable at line {node.lineno}")
        self.generic_visit(node)
    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            self.assigned.add(node.targets[0].id)
        self.generic_visit(node)
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
    def report_unused(self):
        for var in self.assigned - self.used:
            print(f"[Dead Code] Variable '{var}' assigned but never used")

class InlineExpansionDetector(ast.NodeVisitor):
    def visit_BinOp(self, node):
        if isinstance(node.op, (ast.Add, ast.Mult, ast.Pow)):
            if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                print(f"[Inline Expansion] Constant expression at line {node.lineno}: {ast.unparse(node)}")
        self.generic_visit(node)

class OpaquePredicateDetector(ast.NodeVisitor):
    def visit_If(self, node):
        if isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Constant):
            print(f"[Opaque Predicate] Constant condition at line {node.lineno}: {ast.unparse(node)}")
        self.generic_visit(node)

class PythonAnalyzer:
    def analyze(self, code, filename):
        try:
            tree = ast.parse(code)
            DeadCodeDetector().visit(tree)
            InlineExpansionDetector().visit(tree)
            OpaquePredicateDetector().visit(tree)
        except Exception as e:
            print(f"[Python Analysis] Error in {filename}: {e}")

class RegexAnalyzer:
    def analyze(self, code, filename):
        lines = code.split("\n")
        for i, line in enumerate(lines, start=1):
            if re.search(r"\bif\s*\(\s*false\s*\)", line) or re.search(r"\bwhile\s*\(\s*false\s*\)", line):
                print(f"[Dead Code] Unreachable branch at line {i}: {line.strip()}")
            if re.search(r"\d+\s*[\+\-\*\/]\s*\d+", line):
                print(f"[Inline Expansion] Constant expression at line {i}: {line.strip()}")
            if re.search(r"\bif\s*\(\s*\d+\s*(==|!=|>|<|>=|<=)\s*\d+\s*\)", line):
                print(f"[Opaque Predicate] Constant comparison at line {i}: {line.strip()}")

# -------------------- FILE HANDLER --------------------
def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    lang = detect_language(os.path.basename(filepath))

    results = {"String Decryption": [], "Identifier Cleaner": [], "Control Flow": [], "Code Analysis": []}

    # ---------------- String Decryption ----------------
    str_cleaner = StringDecryptor()
    str_changes, code_after_strings = str_cleaner.detect_and_clean(code)
    if str_changes:
        for c in str_changes:
            results["String Decryption"].append(
                f"{filepath}: {c['original']} -> {c['decrypted']} ({c['reason']})"
            )

    # ---------------- Identifier Cleaner ----------------
    id_cleaner = IdentifierCleaner(language=lang)
    try:
        obf_changes, deobf_code = id_cleaner.detect_and_clean(code_after_strings)
    except SyntaxError as e:
        results["Identifier Cleaner"].append(f"{filepath}: Skipped due to syntax error: {e}")
        obf_changes = []
        deobf_code = code_after_strings
    for c in obf_changes:
        results["Identifier Cleaner"].append(
            f"{filepath}: {c['original']} -> {c['cleaned']} ({c['reason']})"
        )

    # ---------------- Control Flow ----------------
    cf_cleaner = FakeConditionCleaner()
    cf_changes = cf_cleaner.clean_code(deobf_code)
    for c in cf_changes:
        results["Control Flow"].append(
            f"{filepath}: {c['original']} -> {c['cleaned']} ({c['reason']})"
        )

    # ---------------- Code Analysis ----------------
    final_code = deobf_code
    for c in cf_changes:
        final_code = final_code.replace(c['original'], c['cleaned'])
    if lang == "python":
        buffer = StringIO()
        sys.stdout = buffer
        PythonAnalyzer().analyze(final_code, filepath)
        sys.stdout = sys.__stdout__
        analysis_output = buffer.getvalue().strip()
        if analysis_output:
            results["Code Analysis"].append(analysis_output)
    elif lang in ["c", "cpp", "java", "kotlin"]:
        buffer = StringIO()
        sys.stdout = buffer
        RegexAnalyzer().analyze(final_code, filepath)
        sys.stdout = sys.__stdout__
        analysis_output = buffer.getvalue().strip()
        if analysis_output:
            results["Code Analysis"].append(analysis_output)

    return results

# -------------------- MAIN --------------------
def main():
    input_folder = "input"
    output_file = "output/combined_results.out"
    os.makedirs("output", exist_ok=True)

    # Dictionary to store aggregated results
    all_results = {"String Decryption": [], "Identifier Cleaner": [], "Control Flow": [], "Code Analysis": []}

    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        if os.path.isdir(file_path):
            continue
        file_results = analyze_file(file_path)
        for key in all_results:
            all_results[key].extend(file_results[key])

    # Prepare final uniform report
    report_lines = []
    for technique, cases in all_results.items():
        report_lines.append(f"\n===== {technique} =====\n")
        if cases:
            report_lines.extend(cases)
        else:
            report_lines.append("No cases detected.")
        report_lines.append("\n")

    final_report = "\n".join(report_lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_report)

    save_pdf(final_report)
    print(f"✅ Multi-language analysis complete. Results saved in {output_file} and PDF.")

if __name__ == "__main__":
    main()

    """

"""

import os
import sys
from io import StringIO

# -------------------- Import all detection modules --------------------
from input.stringEncryption import StringDecryptor
from input.nameIdentifier import IdentifierCleaner, detect_language
from input.controlFlow import FakeConditionCleaner
from input.deadCode import DeadCodeCleaner
from input.inlineExpansion import InlineExpansionCleaner
from input.opaquePredicate import OpaquePredicateCleaner
from input.instructionSubstitution import InstructionSubstitutionCleaner
from input.dynamicLoading import DynamicCodeLoaderCleaner
from input.junkCode import JunkCodeCleaner
from input.apiRedirection import ApiRedirectionCleaner
from input.mixedLanguage import MixedLanguageCleaner
from input.codeFlattening import CodeFlatteningCleaner

# -------------------- PDF EXPORT --------------------
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


def save_pdf(results, pdf_path="output/combined_results.pdf"):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="TitleStyle", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=16, spaceAfter=20
    )
    normal_style = ParagraphStyle(name="NormalStyle", parent=styles["Normal"], fontSize=11, leading=14)

    content = [Paragraph("🔍 Code Analysis Results", title_style), Spacer(1, 12)]
    for line in results.split("\n"):
        if line.strip().startswith("====="):
            content.append(PageBreak())
            content.append(Paragraph(line.strip(), styles["Heading2"]))
            content.append(Spacer(1, 12))
        else:
            content.append(Paragraph(line.replace("→", "->"), normal_style))
            content.append(Spacer(1, 6))
    doc.build(content)
    print(f"📄 PDF saved at {pdf_path}")


# -------------------- FILE ANALYSIS --------------------
def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    lang = detect_language(os.path.basename(filepath))

    # Unified result dictionary for all techniques
    results = {
        "String Encryption": [],
        "Identifier Cleaner": [],
        "Control Flow Flattening": [],
        "Dead Code": [],
        "Inline Expansion": [],
        "Opaque Predicates": [],
        "Instruction Substitution": [],
        "Dynamic Code Loading": [],
        "Junk Code": [],
        "API Redirection": [],
        "Mixed Language Obfuscation": [],
        "Code Flattening": [],
    }

    # Store all transformations in order
    transformations = [
        ("String Encryption", StringDecryptor()),
        ("Identifier Cleaner", IdentifierCleaner(language=lang)),
        ("Control Flow Flattening", FakeConditionCleaner()),
        ("Dead Code", DeadCodeCleaner()),
        ("Inline Expansion", InlineExpansionCleaner()),
        ("Opaque Predicates", OpaquePredicateCleaner()),
        ("Instruction Substitution", InstructionSubstitutionCleaner()),
        ("Dynamic Code Loading", DynamicCodeLoaderCleaner()),
        ("Junk Code", JunkCodeCleaner()),
        ("API Redirection", ApiRedirectionCleaner()),
        ("Mixed Language Obfuscation", MixedLanguageCleaner()),
        ("Code Flattening", CodeFlatteningCleaner()),
    ]

    current_code = code
    for technique, cleaner in transformations:
        try:
            changes = cleaner.clean_code(current_code)
            for c in changes:
                results[technique].append(
                    f"{filepath}: {c['original']} -> {c['cleaned']} ({c['reason']})"
                )
                current_code = current_code.replace(c['original'], c['cleaned'])
        except Exception as e:
            results[technique].append(f"{filepath}: Error while processing {technique}: {e}")

    return results


# -------------------- MAIN --------------------
def main():
    input_folder = "input"
    output_file = "output/combined_results.txt"
    os.makedirs("output", exist_ok=True)

    # Combine results for all files
    all_results = {
        "String Encryption": [],
        "Identifier Cleaner": [],
        "Control Flow Flattening": [],
        "Dead Code": [],
        "Inline Expansion": [],
        "Opaque Predicates": [],
        "Instruction Substitution": [],
        "Dynamic Code Loading": [],
        "Junk Code": [],
        "API Redirection": [],
        "Mixed Language Obfuscation": [],
        "Code Flattening": [],
    }

    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        if os.path.isdir(file_path):
            continue
        file_results = analyze_file(file_path)
        for key in all_results:
            all_results[key].extend(file_results[key])

    # Prepare final text report
    report_lines = []
    for technique, logs in all_results.items():
        report_lines.append(f"\n===== {technique} =====\n")
        if logs:
            report_lines.extend(logs)
        else:
            report_lines.append("No cases detected.\n")

    final_report = "\n".join(report_lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_report)

    save_pdf(final_report)
    print(f"✅ Analysis complete! Results saved in {output_file} and combined_results.pdf.")


if __name__ == "__main__":
    main()

    """


"""

import os
import sys
import re
import ast
from io import StringIO

# ---------------- Custom modules ----------------
from input.nameIdentifier import IdentifierCleaner, detect_language
from input.controlFlow import FakeConditionCleaner
from input.stringEncryption import StringDecryptor
from input.deadCode import clean_deadcode_python, clean_deadcode_clike
from input.inlineExpansion import clean_inline_expansion_python, clean_inline_expansion_clike
from input.opaque_predicate import clean_opaque_predicate_python, clean_opaque_predicate_clike
from input.controlflow_flattening import clean_controlflow_flattening_python, clean_controlflow_flattening_clike
from input.instruction_substitution import clean_instruction_substitution_python, clean_instruction_substitution_clike
from input.dynamic_loading import clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike
from input.junkcode import clean_junk_code_python, clean_junk_code_clike
from input.api_redirection import clean_api_redirection_python, clean_api_redirection_clike
from input.mixed_language import clean_mixed_language_python, clean_mixed_language_clike

# -------------------- PDF EXPORT --------------------
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def save_pdf(results, pdf_path="output/combined_results.pdf"):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=20
    )
    normal_style = ParagraphStyle(
        name="NormalStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
    )

    content = [Paragraph("🔍 Code Analysis Results", title_style), Spacer(1,12)]
    for line in results.split("\n"):
        if line.strip().startswith("====="):
            content.append(PageBreak())
            content.append(Paragraph(line.strip(), styles["Heading2"]))
            content.append(Spacer(1,12))
        else:
            content.append(Paragraph(line.replace("→","->"), normal_style))
            content.append(Spacer(1,6))

    doc.build(content)
    print(f"📄 PDF saved at {pdf_path}")
"""


"""
# -------------------- PDF EXPORT --------------------
def save_pdf(results, pdf_path="output/combined_results.pdf"):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=20
    )
    normal_style = ParagraphStyle(
        name="NormalStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
    )

    content = [Paragraph("🔍 Code Analysis Results", title_style), Spacer(1,12)]

    for line in results.split("\n"):
        line = line.strip()
        if not line:
            continue  # skip empty lines
        if line.startswith("====="):
            content.append(PageBreak())
            content.append(Paragraph(line, styles["Heading2"]))
            content.append(Spacer(1,12))
        else:
            # Only include result lines, ignore full code blocks
            if "->" in line or "No cases detected." in line or "Error" in line:
                content.append(Paragraph(line.replace("→","->"), normal_style))
                content.append(Spacer(1,6))

    doc.build(content)
    print(f"📄 PDF saved at {pdf_path}")

# -------------------- FILE HANDLER --------------------
def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    lang = detect_language(os.path.basename(filepath))

    results = {
        "String Encryption": [],
        "Identifier Cleaner": [],
        "Control Flow": [],
        "Dead Code": [],
        "Inline Expansion": [],
        "Opaque Predicates": [],
        "Control Flow Flattening": [],
        "Instruction Substitution": [],
        "Dynamic Code Loading": [],
        "Junk Code": [],
        "API Redirection": [],
        "Mixed Language Obfuscation": [],
    }

    # ---------------- String Encryption ----------------
    str_cleaner = StringDecryptor()
    str_changes, code = str_cleaner.detect_and_clean(code)
    for c in str_changes:
        results["String Encryption"].append(f"{filepath}: {c['original']} -> {c['decrypted']} ({c['reason']})")

    # ---------------- Identifier Cleaner ----------------
    id_cleaner = IdentifierCleaner(language=lang)
    try:
        id_changes, code = id_cleaner.detect_and_clean(code)
    except SyntaxError as e:
        results["Identifier Cleaner"].append(f"{filepath}: Skipped due to syntax error: {e}")
        id_changes = []
    for c in id_changes:
        results["Identifier Cleaner"].append(f"{filepath}: {c['original']} -> {c['cleaned']} ({c['reason']})")

    # ---------------- Control Flow ----------------
    cf_cleaner = FakeConditionCleaner()
    cf_changes = cf_cleaner.clean_code(code)
    for c in cf_changes:
        results["Control Flow"].append(f"{filepath}: {c['original']} -> {c['cleaned']} ({c['reason']})")
        code = code.replace(c['original'], c['cleaned'])

    # ---------------- Other Techniques ----------------
    tech_map = {
        "Dead Code": (clean_deadcode_python, clean_deadcode_clike),
        "Inline Expansion": (clean_inline_expansion_python, clean_inline_expansion_clike),
        "Opaque Predicates": (clean_opaque_predicate_python, clean_opaque_predicate_clike),
        "Control Flow Flattening": (clean_controlflow_flattening_python, clean_controlflow_flattening_clike),
        "Instruction Substitution": (clean_instruction_substitution_python, clean_instruction_substitution_clike),
        "Dynamic Code Loading": (clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike),
        "Junk Code": (clean_junk_code_python, clean_junk_code_clike),
        "API Redirection": (clean_api_redirection_python, clean_api_redirection_clike),
        "Mixed Language Obfuscation": (clean_mixed_language_python, clean_mixed_language_clike),
    }

    for name, (py_func, clike_func) in tech_map.items():
        try:
            if lang == "python":
                changes = py_func(code)
            else:
                changes = clike_func(code)
            for ch in changes:
                results[name].append(f"{filepath}: {ch['original']} -> {ch['cleaned']} ({ch['reason']})")
                code = code.replace(ch['original'], ch['cleaned'])
        except Exception as e:
            results[name].append(f"{filepath}: Error - {e}")

    return results

# -------------------- MAIN --------------------
def main():
    input_folder = "input"
    output_file = "output/combined_results.txt"
    os.makedirs("output", exist_ok=True)

    all_results = {
        "String Encryption": [],
        "Identifier Cleaner": [],
        "Control Flow": [],
        "Dead Code": [],
        "Inline Expansion": [],
        "Opaque Predicates": [],
        "Control Flow Flattening": [],
        "Instruction Substitution": [],
        "Dynamic Code Loading": [],
        "Junk Code": [],
        "API Redirection": [],
        "Mixed Language Obfuscation": [],
    }

    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        if os.path.isdir(file_path):
            continue
        file_results = analyze_file(file_path)
        for key in all_results:
            all_results[key].extend(file_results[key])

    # Prepare final uniform report
    report_lines = []
    for technique, cases in all_results.items():
        report_lines.append(f"\n===== {technique} =====\n")
        if cases:
            report_lines.extend(cases)
        else:
            report_lines.append("No cases detected.")
        report_lines.append("\n")

    final_report = "\n".join(report_lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_report)

    save_pdf(final_report)
    print(f"✅ Multi-language analysis complete. Results saved in {output_file} and PDF.")

if __name__ == "__main__":
    main()
"""





"""
import os
import subprocess
import re
import ast
from io import StringIO
import sys

# ---------------- Custom modules ----------------
from input.nameIdentifier import IdentifierCleaner, detect_language
from input.controlFlow import FakeConditionCleaner
from input.stringEncryption import StringDecryptor
from input.deadCode import clean_deadcode_python, clean_deadcode_clike
from input.inlineExpansion import clean_inline_expansion_python, clean_inline_expansion_clike
from input.opaque_predicate import clean_opaque_predicate_python, clean_opaque_predicate_clike
from input.controlflow_flattening import clean_controlflow_flattening_python, clean_controlflow_flattening_clike
from input.instruction_substitution import clean_instruction_substitution_python, clean_instruction_substitution_clike
from input.dynamic_loading import clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike
from input.junkcode import clean_junk_code_python, clean_junk_code_clike
from input.api_redirection import clean_api_redirection_python, clean_api_redirection_clike
from input.mixed_language import clean_mixed_language_python, clean_mixed_language_clike


# -------------------- PDF EXPORT --------------------
def save_pdf(results, pdf_path="output/combined_results.pdf"):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=20
    )
    normal_style = ParagraphStyle(
        name="NormalStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
    )

    content = [Paragraph("🔍 Code Analysis Results", title_style), Spacer(1, 12)]

    for line in results.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("====="):
            content.append(PageBreak())
            content.append(Paragraph(line, styles["Heading2"]))
            content.append(Spacer(1, 12))
        else:
            if "->" in line or "No cases detected." in line or "Error" in line:
                content.append(Paragraph(line.replace("→", "->"), normal_style))
                content.append(Spacer(1, 6))

    doc.build(content)
    print(f"📄 PDF saved at {pdf_path}")


# -------------------- FILE HANDLER --------------------
def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    lang = detect_language(os.path.basename(filepath))

    results = {
        "String Encryption": [],
        "Identifier Cleaner": [],
        "Control Flow": [],
        "Dead Code": [],
        "Inline Expansion": [],
        "Opaque Predicates": [],
        "Control Flow Flattening": [],
        "Instruction Substitution": [],
        "Dynamic Code Loading": [],
        "Junk Code": [],
        "API Redirection": [],
        "Mixed Language Obfuscation": [],
    }

    # ---------------- String Encryption ----------------
    str_cleaner = StringDecryptor()
    str_changes, code = str_cleaner.detect_and_clean(code)
    for c in str_changes:
        results["String Encryption"].append(f"{filepath}: {c['original']} -> {c['decrypted']} ({c['reason']})")

    # ---------------- Identifier Cleaner ----------------
    id_cleaner = IdentifierCleaner(language=lang)
    try:
        id_changes, code = id_cleaner.detect_and_clean(code)
    except SyntaxError as e:
        results["Identifier Cleaner"].append(f"{filepath}: Skipped due to syntax error: {e}")
        id_changes = []
    for c in id_changes:
        results["Identifier Cleaner"].append(f"{filepath}: {c['original']} -> {c['cleaned']} ({c['reason']})")

    # ---------------- Control Flow ----------------
    cf_cleaner = FakeConditionCleaner()
    cf_changes = cf_cleaner.clean_code(code)
    for c in cf_changes:
        results["Control Flow"].append(f"{filepath}: {c['original']} -> {c['cleaned']} ({c['reason']})")
        code = code.replace(c['original'], c['cleaned'])

    # ---------------- Other Techniques ----------------
    tech_map = {
        "Dead Code": (clean_deadcode_python, clean_deadcode_clike),
        "Inline Expansion": (clean_inline_expansion_python, clean_inline_expansion_clike),
        "Opaque Predicates": (clean_opaque_predicate_python, clean_opaque_predicate_clike),
        "Control Flow Flattening": (clean_controlflow_flattening_python, clean_controlflow_flattening_clike),
        "Instruction Substitution": (clean_instruction_substitution_python, clean_instruction_substitution_clike),
        "Dynamic Code Loading": (clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike),
        "Junk Code": (clean_junk_code_python, clean_junk_code_clike),
        "API Redirection": (clean_api_redirection_python, clean_api_redirection_clike),
        "Mixed Language Obfuscation": (clean_mixed_language_python, clean_mixed_language_clike),
    }

    for name, (py_func, clike_func) in tech_map.items():
        try:
            if lang == "python":
                changes = py_func(code)
            else:
                changes = clike_func(code)
            for ch in changes:
                results[name].append(f"{filepath}: {ch['original']} -> {ch['cleaned']} ({ch['reason']})")
                code = code.replace(ch['original'], ch['cleaned'])
        except Exception as e:
            results[name].append(f"{filepath}: Error - {e}")

    return results


# -------------------- MAIN DETECTION --------------------
def run_analysis(input_folder="input"):
    output_file = "output/combined_results.txt"
    os.makedirs("output", exist_ok=True)

    all_results = {
        "String Encryption": [],
        "Identifier Cleaner": [],
        "Control Flow": [],
        "Dead Code": [],
        "Inline Expansion": [],
        "Opaque Predicates": [],
        "Control Flow Flattening": [],
        "Instruction Substitution": [],
        "Dynamic Code Loading": [],
        "Junk Code": [],
        "API Redirection": [],
        "Mixed Language Obfuscation": [],
    }

    for root, _, files in os.walk(input_folder):
        for filename in files:
            file_path = os.path.join(root, filename)
            if not filename.endswith((".java", ".py", ".cpp", ".c", ".js")):
                continue
            file_results = analyze_file(file_path)
            for key in all_results:
                all_results[key].extend(file_results[key])

    report_lines = []
    for technique, cases in all_results.items():
        report_lines.append(f"\n===== {technique} =====\n")
        if cases:
            report_lines.extend(cases)
        else:
            report_lines.append("No cases detected.")
        report_lines.append("\n")

    final_report = "\n".join(report_lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_report)

    save_pdf(final_report)
    print(f"✅ Multi-language analysis complete. Results saved in {output_file} and PDF.")


# -------------------- AUTO-INTEGRATION WRAPPER --------------------
def analyze_dex_or_apk(file_path):


    jadx_path = r"C:\jadx\bin\jadx.bat"  # 🔹 Change this if JADX is installed elsewhere
    input_folder = "input"

    if os.path.exists(input_folder):
        import shutil
        shutil.rmtree(input_folder)
    os.makedirs(input_folder, exist_ok=True)

    print(f"🔍 Decompiling {file_path} using JADX...")
    try:
        subprocess.run([jadx_path, "-d", input_folder, file_path], check=True)
        print("✅ Decompiled successfully.")
    except subprocess.CalledProcessError:
        print("❌ Error during decompilation. Make sure JADX is installed correctly.")
        return

    print("🚀 Starting obfuscation detection...")
    run_analysis(input_folder)


# -------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    if len(sys.argv) == 2 and (sys.argv[1].endswith(".dex") or sys.argv[1].endswith(".apk")):
        analyze_dex_or_apk(sys.argv[1])
    else:
        run_analysis()
"""



"""
import os
import subprocess
import re
import ast
from io import StringIO
import sys
import traceback

# ---------------- Custom modules ----------------
from input.nameIdentifier import IdentifierCleaner, detect_language
from input.controlFlow import FakeConditionCleaner
from input.stringEncryption import StringDecryptor
from input.deadCode import clean_deadcode_python, clean_deadcode_clike
from input.inlineExpansion import clean_inline_expansion_python, clean_inline_expansion_clike
from input.opaque_predicate import clean_opaque_predicate_python, clean_opaque_predicate_clike
from input.controlflow_flattening import clean_controlflow_flattening_python, clean_controlflow_flattening_clike
from input.instruction_substitution import clean_instruction_substitution_python, clean_instruction_substitution_clike
from input.dynamic_loading import clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike
from input.junkcode import clean_junk_code_python, clean_junk_code_clike
from input.api_redirection import clean_api_redirection_python, clean_api_redirection_clike
from input.mixed_language import clean_mixed_language_python, clean_mixed_language_clike

# -------------------- PDF EXPORT --------------------
def save_pdf(results, pdf_path="output/combined_results.pdf"):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=20
    )
    normal_style = ParagraphStyle(
        name="NormalStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
    )

    content = [Paragraph("🔍 Code Analysis Results", title_style), Spacer(1, 12)]

    for line in results.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("====="):
            content.append(PageBreak())
            content.append(Paragraph(line, styles["Heading2"]))
            content.append(Spacer(1, 12))
        else:
            # include only findings / summary lines (no full code)
            if "->" in line or "No cases detected." in line or "Error" in line or line.startswith("- "):
                content.append(Paragraph(line.replace("→", "->"), normal_style))
                content.append(Spacer(1, 6))

    doc.build(content)
    print(f"📄 PDF saved at {pdf_path}")

# -------------------- FILE ANALYSIS --------------------
SCANNABLE_EXTS = (
    ".java", ".py", ".cpp", ".c", ".js", ".smali", ".kt", ".xml", ".txt"
)

def safe_read_text_file(path):
   
    errors = []
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except Exception as e:
            errors.append((enc, str(e)))
            continue
    # if we get here, raise last error
    raise UnicodeError(f"Unable to read file {path} (tried encodings): {errors}")

def analyze_file(filepath):
  
    try:
        code = safe_read_text_file(filepath)
    except Exception as e:
        return {"__error__": [f"{filepath}: Error reading file: {e}"]}

    lang = detect_language(os.path.basename(filepath))

    results = {
        "String Encryption": [],
        "Identifier Cleaner": [],
        "Control Flow": [],
        "Dead Code": [],
        "Inline Expansion": [],
        "Opaque Predicates": [],
        "Control Flow Flattening": [],
        "Instruction Substitution": [],
        "Dynamic Code Loading": [],
        "Junk Code": [],
        "API Redirection": [],
        "Mixed Language Obfuscation": [],
    }

    # ---------------- String Encryption ----------------
    try:
        str_cleaner = StringDecryptor()
        str_changes, code = str_cleaner.detect_and_clean(code)
        for c in str_changes:
            results["String Encryption"].append(f"{filepath}: {c.get('original','')} -> {c.get('decrypted','')} ({c.get('reason','')})")
    except Exception as e:
        results["String Encryption"].append(f"{filepath}: Error - {e}")

    # ---------------- Identifier Cleaner ----------------
    try:
        id_cleaner = IdentifierCleaner(language=lang)
        id_changes, code = id_cleaner.detect_and_clean(code)
        for c in id_changes:
            results["Identifier Cleaner"].append(f"{filepath}: {c.get('original','')} -> {c.get('cleaned','')} ({c.get('reason','')})")
    except SyntaxError as e:
        results["Identifier Cleaner"].append(f"{filepath}: Skipped due to syntax error: {e}")
    except Exception as e:
        results["Identifier Cleaner"].append(f"{filepath}: Error - {e}")

    # ---------------- Control Flow ----------------
    try:
        cf_cleaner = FakeConditionCleaner()
        cf_changes = cf_cleaner.clean_code(code)
        for c in cf_changes:
            results["Control Flow"].append(f"{filepath}: {c.get('original','')} -> {c.get('cleaned','')} ({c.get('reason','')})")
            code = code.replace(c.get('original',''), c.get('cleaned',''))
    except Exception as e:
        results["Control Flow"].append(f"{filepath}: Error - {e}")

    # ---------------- Other Techniques ----------------
    tech_map = {
        "Dead Code": (clean_deadcode_python, clean_deadcode_clike),
        "Inline Expansion": (clean_inline_expansion_python, clean_inline_expansion_clike),
        "Opaque Predicates": (clean_opaque_predicate_python, clean_opaque_predicate_clike),
        "Control Flow Flattening": (clean_controlflow_flattening_python, clean_controlflow_flattening_clike),
        "Instruction Substitution": (clean_instruction_substitution_python, clean_instruction_substitution_clike),
        "Dynamic Code Loading": (clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike),
        "Junk Code": (clean_junk_code_python, clean_junk_code_clike),
        "API Redirection": (clean_api_redirection_python, clean_api_redirection_clike),
        "Mixed Language Obfuscation": (clean_mixed_language_python, clean_mixed_language_clike),
    }

    for name, (py_func, clike_func) in tech_map.items():
        try:
            if lang == "python":
                changes = py_func(code)
            else:
                changes = clike_func(code)
            # ensure changes is a list of dicts
            if not isinstance(changes, (list, tuple)):
                results[name].append(f"{filepath}: {name} function returned non-list result.")
                continue
            for ch in changes:
                orig = ch.get("original", "")
                cleaned = ch.get("cleaned", "")
                reason = ch.get("reason", "")
                results[name].append(f"{filepath}: {orig} -> {cleaned} ({reason})")
                if orig:
                    code = code.replace(orig, cleaned)
        except Exception:
            results[name].append(f"{filepath}: Error - {traceback.format_exc()}")

    return results

# -------------------- MAIN DETECTION --------------------
def run_analysis(input_folder="input"):
    output_file = "output/combined_results.txt"
    os.makedirs("output", exist_ok=True)

    # prepare aggregated buckets
    all_results = {
        "String Encryption": [],
        "Identifier Cleaner": [],
        "Control Flow": [],
        "Dead Code": [],
        "Inline Expansion": [],
        "Opaque Predicates": [],
        "Control Flow Flattening": [],
        "Instruction Substitution": [],
        "Dynamic Code Loading": [],
        "Junk Code": [],
        "API Redirection": [],
        "Mixed Language Obfuscation": [],
    }

    scanned_files = []
    skipped_files = []
    read_errors = []

    # Walk folder recursively and pick files with supported extensions
    for root, _, files in os.walk(input_folder):
        for filename in files:
            f_lower = filename.lower()
            if not f_lower.endswith(SCANNABLE_EXTS):
                # skip binary-like files, but record
                skipped_files.append(os.path.join(root, filename))
                continue
            file_path = os.path.join(root, filename)
            scanned_files.append(file_path)

    # If nothing found, warn and still attempt one-level listing
    if not scanned_files:
        print(f"⚠️ No scannable files found under '{input_folder}'. Make sure jadx produced .java files or add extensions to SCANNABLE_EXTS.")
    else:
        print(f"🗂️ Found {len(scanned_files)} scannable files under '{input_folder}'. Beginning analysis...")

    # analyze each file and merge results
    for fp in scanned_files:
        try:
            per_file_results = analyze_file(fp)
            # if file read error
            if "__error__" in per_file_results:
                read_errors.extend(per_file_results["__error__"])
                continue
            for key in all_results:
                # extend lists with per-file findings for that technique
                vals = per_file_results.get(key, [])
                if vals:
                    all_results[key].extend(vals)
        except Exception:
            print(f"Unexpected error analyzing {fp}:\n{traceback.format_exc()}")

    # Prepare final uniform report
    report_lines = []
    report_lines.append(f"Analysis summary:\n- Scanned files: {len(scanned_files)}\n- Skipped files (unrecognized ext): {len(skipped_files)}\n- Read errors: {len(read_errors)}\n")
    if read_errors:
        report_lines.append("Read errors (first 10):")
        report_lines.extend(read_errors[:10])
    for technique, cases in all_results.items():
        report_lines.append(f"\n===== {technique} =====\n")
        if cases:
            report_lines.extend(cases)
        else:
            report_lines.append("No cases detected.")
        report_lines.append("\n")

    final_report = "\n".join(report_lines)

    # Save TXT
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_report)

    # Save PDF (only findings)
    save_pdf(final_report)

    # Print compact summary
    total_findings = sum(len(v) for v in all_results.values())
    print(f"\n✅ Done. Scanned {len(scanned_files)} files, found {total_findings} findings across {len(all_results)} techniques.")
    print(f"Results written to: {output_file} and output/combined_results.pdf")

# -------------------- AUTO-INTEGRATION WRAPPER --------------------
def analyze_dex_or_apk(file_path):

    # set this to your jadx binary path (or 'jadx' if on PATH)
    jadx_path = r"C:\jadx\bin\jadx.bat"
    input_folder = "input"

    if os.path.exists(input_folder):
        import shutil
        shutil.rmtree(input_folder)
    # ensure input exists
    os.makedirs(input_folder, exist_ok=True)

    print(f"🔍 Decompiling {file_path} using JADX...")
    try:
        subprocess.run([jadx_path, "-d", input_folder, file_path], check=True)
        print("✅ Decompiled successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ Error during decompilation. Make sure JADX is installed correctly.")
        print(e)
        return

    print("🚀 Starting obfuscation detection...")
    run_analysis(input_folder)

# -------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    # If user provides a .dex or .apk argument, run decompile+analysis automatically
    if len(sys.argv) == 2 and (sys.argv[1].endswith(".dex") or sys.argv[1].endswith(".apk")):
        analyze_dex_or_apk(sys.argv[1])
    else:
        # default: analyze whatever is in input/ (recursively)
        run_analysis("input")




"""

# # merged_verbose_merge.py
# import os
# import subprocess
# import re
# import ast
# from io import StringIO
# import sys
# import traceback

# # ---------------- Custom modules (unchanged) ----------------
# from utils.nameIdentifier import IdentifierCleaner, detect_language
# from utils.controlFlow import FakeConditionCleaner
# from utils.stringEncryption import StringDecryptor
# from utils.deadcode import clean_deadcode_python, clean_deadcode_clike
# from utils.inlineExpansion import clean_inline_expansion_python, clean_inline_expansion_clike
# from utils.opaque_predicate import clean_opaque_predicate_python, clean_opaque_predicate_clike
# from utils.controlflow_flattening import clean_controlflow_flattening_python, clean_controlflow_flattening_clike
# from utils.instruction_substitution import clean_instruction_substitution_python, clean_instruction_substitution_clike
# from utils.dynamic_loading import clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike
# from utils.junkcode import clean_junk_code_python, clean_junk_code_clike
# from utils.api_redirection import clean_api_redirection_python, clean_api_redirection_clike
# from utils.mixed_language import clean_mixed_language_python, clean_mixed_language_clike

# # -------------------- PDF EXPORT (fixed for Java code) --------------------
# def save_pdf(results, pdf_path="output/combined_results.pdf"):
#     from reportlab.lib.pagesizes import letter
#     from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
#     from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
#     from reportlab.lib.enums import TA_CENTER
#     from xml.sax.saxutils import escape  # ✅ added for escaping < > &

#     doc = SimpleDocTemplate(pdf_path, pagesize=letter)
#     styles = getSampleStyleSheet()
#     title_style = ParagraphStyle(
#         name="TitleStyle",
#         parent=styles["Heading1"],
#         alignment=TA_CENTER,
#         fontSize=16,
#         spaceAfter=20
#     )
#     normal_style = ParagraphStyle(
#         name="NormalStyle",
#         parent=styles["Normal"],
#         fontSize=10,
#         leading=12,
#     )

#     content = [Paragraph("🔍 Code Analysis Results", title_style), Spacer(1, 12)]

#     for line in results.split("\n"):
#         line = line.strip()
#         if not line:
#             continue

#         # ✅ Escape HTML-sensitive characters and fix arrow symbol
#         safe_line = escape(line.replace("→", "->"))

#         if line.startswith("====="):
#             content.append(PageBreak())
#             content.append(Paragraph(safe_line, styles["Heading2"]))
#             content.append(Spacer(1, 12))
#         else:
#             if "->" in line or "No cases detected." in line or "Error" in line or line.startswith("- "):
#                 content.append(Paragraph(safe_line, normal_style))
#                 content.append(Spacer(1, 6))

#     doc.build(content)
#     print(f"📄 PDF saved at {pdf_path}")

# # -------------------- Helpers --------------------
# SCANNABLE_EXTS = (".java", ".py", ".cpp", ".c", ".js", ".smali", ".kt", ".xml", ".txt")
# VERBOSE = True

# def safe_read_text_file(path):
#     for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
#         try:
#             with open(path, "r", encoding=enc) as f:
#                 return f.read()
#         except Exception:
#             continue
#     raise UnicodeError(f"Unable to read file {path} with common encodings")

# # Extra heuristics tuned for decompiled/proguard-like code
# _proguard_shortname_re = re.compile(r'\b([a-zA-Z]{1,2}\d{0,2}|[a-zA-Z]\d{1,3})\b')
# _wrapper_function_re = re.compile(r'\breturn\s+[a-zA-Z0-9_]+\s*\(', re.IGNORECASE)
# _reflection_re = re.compile(r'\b(Class\.forName|forName\(|getMethod\(|invoke\(|loadLibrary\(|loadClass\()', re.IGNORECASE)
# _junk_nop_re_smali = re.compile(r'\bnop\b', re.IGNORECASE)
# _junk_add_zero_re = re.compile(r'\b([A-Za-z_]\w*)\s*=\s*\1\s*[\+\-]\s*0\b')
# _constant_arith_re = re.compile(r'\b\d+\s*[\+\-\*\/%]\s*\d+\b')
# _switch_state_re = re.compile(r'\bswitch\b|\bcase\b|\bstate\b', re.IGNORECASE)
# _goto_like_re = re.compile(r'\bgoto\b|\bif-?eqz\b|\bif-?nez\b', re.IGNORECASE)

# # -------------------- Per-file extra heuristic scanner --------------------
# def extra_heuristics_scan(text, filepath):
  
#     findings = {
#         "Dead Code": [],
#         "Inline Expansion": [],
#         "Opaque Predicates": [],
#         "Control Flow Flattening": [],
#         "Instruction Substitution": [],
#         "Dynamic Code Loading": [],
#         "Junk Code": [],
#         "API Redirection": [],
#         "Identifier Obfuscation": [],
#     }

#     # Dead code heuristics (if false / if (0) or obvious returns)
#     for m in re.finditer(r'\bif\s*\(\s*(false|0|0x0|0x00)\s*\)', text, re.IGNORECASE):
#         findings["Dead Code"].append(f"constant-if at {m.start()} -> {m.group(0)[:80]}")

#     # code after return inside function (simple heuristic)
#     for m in re.finditer(r'\breturn\b[^;{]*[;}]', text):
#         # search a bit after the return for another statement — naive
#         pos = m.end()
#         following = text[pos:pos+200]
#         if following.strip():
#             findings["Dead Code"].append(f"code_after_return at {pos}")

#     # Inline expansion / constant fold
#     for m in _constant_arith_re.finditer(text):
#         findings["Inline Expansion"].append(f"const-arith '{m.group(0)}'")

#     # Opaque predicate heuristics: constant comparisons like 3*3 == 9 or 2+2 == 4
#     for m in re.finditer(r'(\d+\s*[\+\-\*\/]\s*\d+)\s*==\s*\d+', text):
#         findings["Opaque Predicates"].append(f"constant-compare '{m.group(0)}'")

#     # ProGuard-like name obfuscation (very short class/var names) — count unique short ids
#     short_ids = set(re.findall(r'\b[a-zA-Z]\b|\b[a-zA-Z]{1,2}\d?\b', text))
#     # if there are many short ids, flag
#     if len(short_ids) > 30:
#         findings["Identifier Obfuscation"].append(f"many short identifiers ({len(short_ids)}) — possible ProGuard renames")

#     # wrapper functions: simple API redirection patterns
#     for m in _wrapper_function_re.finditer(text):
#         findings["API Redirection"].append(f"wrapper-call-like: {m.group(0)[:60]}")

#     # Reflection / dynamic load detection
#     for m in _reflection_re.finditer(text):
#         findings["Dynamic Code Loading"].append(f"reflection/dynamic API: {m.group(0)}")

#     # Junk code NOP or x = x + 0
#     if _junk_nop_re_smali.search(text):
#         findings["Junk Code"].append("smali NOP found")
#     for m in _junk_add_zero_re.finditer(text):
#         findings["Junk Code"].append(f"add-zero: {m.group(0)}")

#     # Control flow flattening hints (many goto/labels/switch-state)
#     if _goto_like_re.search(text) or _switch_state_re.search(text):
#         findings["Control Flow Flattening"].append("goto/switch/state-like patterns present")

#     # Instruction substitution: arithmetic expressed oddly (x - (-1)) etc.
#     if re.search(r'\b-\s*\(-\d+\)|\b\+\s*0\b|\b-\s*0\b', text):
#         findings["Instruction Substitution"].append("possible instruction substitution expression")

#     # API redirection: multiple small functions that return other function calls
#     if len(re.findall(r'\breturn\b.*\(', text)) > 50:
#         findings["API Redirection"].append("many small wrappers returning other calls (>50)")

#     # Filter empty lists
#     return {k: v for k, v in findings.items() if v}

# # -------------------- FILE ANALYSIS --------------------
# def analyze_file(filepath):
#     try:
#         text = safe_read_text_file(filepath)
#     except Exception as e:
#         return {"__error__": [f"{filepath}: read error: {e}"]}

#     # base analysis buckets
#     per_file = {
#         "String Encryption": [],
#         "Identifier Cleaner": [],
#         "Control Flow": [],
#         "Dead Code": [],
#         "Inline Expansion": [],
#         "Opaque Predicates": [],
#         "Control Flow Flattening": [],
#         "Instruction Substitution": [],
#         "Dynamic Code Loading": [],
#         "Junk Code": [],
#         "API Redirection": [],
#         "Mixed Language Obfuscation": [],
#         "Identifier Obfuscation": [],
#     }

#     # quick verbose notification
#     if VERBOSE:
#         print(f"[*] Analyzing: {filepath}")

#     lang = detect_language(os.path.basename(filepath))

#     # # String decryption
#     # try:
#     #     str_cleaner = StringDecryptor()
#     #     str_changes, text = str_cleaner.detect_and_clean(text)
#     #     for c in str_changes:
#     #         per_file["String Encryption"].append(f"{filepath}: {c.get('original','')} -> {c.get('decrypted','')} ({c.get('reason','')})")
#     # except Exception as e:
#     #     per_file["String Encryption"].append(f"{filepath}: Error - {e}")
#         # String decryption (now include original source line + deobfuscated line in reporting)
#     try:
#         str_cleaner = StringDecryptor()
#         str_changes, text = str_cleaner.detect_and_clean(text)
#         for c in str_changes:
#             # include the source line that contained the obfuscated literal and the cleaned version
#             orig_line = c.get('original_line', '').strip()
#             cleaned_line = c.get('cleaned_line', '').strip()
#             # trim very long lines for report readability
#             maxlen = 400
#             if len(orig_line) > maxlen:
#                 orig_line = orig_line[:maxlen] + '...'
#             if len(cleaned_line) > maxlen:
#                 cleaned_line = cleaned_line[:maxlen] + '...'
#             per_file["String Encryption"].append(
#                 f"{filepath}: obf-line: {orig_line} -> deobf-line: {cleaned_line} ({c.get('reason','')})"
#             )
#     except Exception as e:
#         per_file["String Encryption"].append(f"{filepath}: Error - {e}")
#     # try:
#     #     str_cleaner = StringDecryptor()
#     #     str_changes, text = str_cleaner.detect_and_clean(text)

#     #     for c in str_changes:
#     #     # Extract context
#     #         orig_line = c.get('original_line', '').strip()
#     #         cleaned_line = c.get('cleaned_line', '').strip()
#     #         reason = c.get('reason', '').strip()

#     #     # Limit line lengths for readability
#     #         maxlen = 120
#     #         if len(orig_line) > maxlen:
#     #             orig_line = orig_line[:maxlen] + '...'
#     #         if len(cleaned_line) > maxlen:
#     #             cleaned_line = cleaned_line[:maxlen] + '...'

#     #     # Organize output for clarity
#     #         formatted_output = (
#     #             f"\n📄 File: {filepath}\n"
#     #             f" ├─ 🔹 Obfuscated Line : {orig_line}\n"
#     #             f" ├─ 🔸 Deobfuscated    : {cleaned_line}\n"
#     #             f" └─ 💬 Reason          : {reason}\n"
#     #         )

#     #         per_file["String Encryption"].append(formatted_output)

#     # except Exception as e:
#     #     per_file["String Encryption"].append(
#     #         f"\n📄 File: {filepath}\n └─ ❌ Error: {e}\n"
#     #     )



#     # Identifier cleaner
#     try:
#         id_cleaner = IdentifierCleaner(language=lang)
#         id_changes, text = id_cleaner.detect_and_clean(text)
#         for c in id_changes:
#             per_file["Identifier Cleaner"].append(f"{filepath}: {c.get('original','')} -> {c.get('cleaned','')} ({c.get('reason','')})")
#     except Exception as e:
#         per_file["Identifier Cleaner"].append(f"{filepath}: Error - {e}")

#     # Control flow fake conditions
#     try:
#         cf = FakeConditionCleaner()
#         cf_changes = cf.clean_code(text)
#         for c in cf_changes:
#             per_file["Control Flow"].append(f"{filepath}: {c.get('original','')} -> {c.get('cleaned','')} ({c.get('reason','')})")
#             text = text.replace(c.get('original',''), c.get('cleaned',''))
#     except Exception as e:
#         per_file["Control Flow"].append(f"{filepath}: Error - {e}")

#     # Existing modular detectors (call appropriate one per language)
#     tech_map = {
#         "Dead Code": (clean_deadcode_python, clean_deadcode_clike),
#         "Inline Expansion": (clean_inline_expansion_python, clean_inline_expansion_clike),
#         "Opaque Predicates": (clean_opaque_predicate_python, clean_opaque_predicate_clike),
#         "Control Flow Flattening": (clean_controlflow_flattening_python, clean_controlflow_flattening_clike),
#         "Instruction Substitution": (clean_instruction_substitution_python, clean_instruction_substitution_clike),
#         "Dynamic Code Loading": (clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike),
#         "Junk Code": (clean_junk_code_python, clean_junk_code_clike),
#         "API Redirection": (clean_api_redirection_python, clean_api_redirection_clike),
#         "Mixed Language Obfuscation": (clean_mixed_language_python, clean_mixed_language_clike),
#     }

#     for name, (py_fn, clike_fn) in tech_map.items():
#         try:
#             changes = py_fn(text) if lang == "python" else clike_fn(text)
#             if isinstance(changes, (list, tuple)):
#                 for ch in changes:
#                     orig = ch.get("original", "") if isinstance(ch, dict) else str(ch)
#                     clean = ch.get("cleaned", "") if isinstance(ch, dict) else ""
#                     reason = ch.get("reason", "") if isinstance(ch, dict) else ""
#                     per_file[name].append(f"{filepath}: {orig[:140]} -> {clean[:140]} ({reason})")
#                     if orig:
#                         text = text.replace(orig, clean)
#             else:
#                 per_file[name].append(f"{filepath}: detector returned non-list result")
#         except Exception:
#             per_file[name].append(f"{filepath}: Error - {traceback.format_exc()}")

#     # Extra heuristics for decompiled/proguard-like code
#     heur = extra_heuristics_scan(text, filepath)
#     for k, vs in heur.items():
#         bucket = "Identifier Obfuscation" if k == "Identifier Obfuscation" else k
#         per_file.setdefault(bucket, [])
#         for v in vs:
#             per_file[bucket].append(f"{filepath}: {v}")

#     return per_file

# # -------------------- RUNNER --------------------
# def run_analysis(input_folder="input"):
#     output_file = "output/combined_results.txt"
#     os.makedirs("output", exist_ok=True)

#     # aggregated buckets
#     all_results = {
#         "String Encryption": [],
#         "Identifier Cleaner": [],
#         "Control Flow": [],
#         "Dead Code": [],
#         "Inline Expansion": [],
#         "Opaque Predicates": [],
#         "Control Flow Flattening": [],
#         "Instruction Substitution": [],
#         "Dynamic Code Loading": [],
#         "Junk Code": [],
#         "API Redirection": [],
#         "Mixed Language Obfuscation": [],
#         "Identifier Obfuscation": [],
#     }

#     files_to_scan = []
#     for root, _, files in os.walk(input_folder):
#         for fn in files:
#             if fn.lower().endswith(SCANNABLE_EXTS):
#                 files_to_scan.append(os.path.join(root, fn))

#     print(f"Found {len(files_to_scan)} scannable files under '{input_folder}'")

#     # scan each file, collect per-file counts
#     per_file_summary = []
#     for idx, fp in enumerate(files_to_scan, start=1):
#         try:
#             per_file = analyze_file(fp)
#         except Exception:
#             per_file = {"__error__": [f"{fp}: unexpected analyzer error\n{traceback.format_exc()}"]}

#         # record errors
#         if "__error__" in per_file:
#             all_results.setdefault("Errors", []).extend(per_file["__error__"])
#             per_file_summary.append((fp, 0, True))
#             continue

#         # count findings per technique for this file
#         counts = {k: len(v) for k, v in per_file.items()}
#         total = sum(counts.values())
#         per_file_summary.append((fp, total, False))
#         if VERBOSE:
#             print(f"[{idx}/{len(files_to_scan)}] {os.path.relpath(fp)} -> findings: {total} (breakdown: {counts})")

#         # append per-file findings to aggregated buckets
#         for k, vs in per_file.items():
#             if not vs:
#                 continue
#             # normalize name if needed
#             key = k
#             if key not in all_results:
#                 all_results[key] = []
#             all_results[key].extend(vs)

#     # prepare report lines
#     report_lines = []
#     report_lines.append("Analysis summary:")
#     report_lines.append(f"- scanned files: {len(files_to_scan)}")
#     total_findings = sum(len(v) for v in all_results.values())
#     report_lines.append(f"- total findings: {total_findings}")
#     report_lines.append("\nPer-file summary (first 40 entries):")
#     for fp, tot, is_err in per_file_summary[:40]:
#         status = "ERROR" if is_err else f"{tot} findings"
#         report_lines.append(f"- {fp} : {status}")

#     # detailed technique sections
#     for technique, findings in all_results.items():
#         report_lines.append(f"\n===== {technique} =====\n")
#         if findings:
#             report_lines.extend(findings)
#         else:
#             report_lines.append("No cases detected.")
#         report_lines.append("\n")

#     final_report = "\n".join(report_lines)

#     with open(output_file, "w", encoding="utf-8") as f:
#         f.write(final_report)

#     save_pdf(final_report)
#     print(f"\n✅ Done. Scanned {len(files_to_scan)} files, found {total_findings} findings.")
#     print(f"Results saved: {output_file} and output/combined_results.pdf")

# # -------------------- AUTO-INTEGRATION WRAPPER --------------------
# def analyze_dex_or_apk(file_path):
#     jadx_path = r"C:\jadx\bin\jadx.bat"  # change if needed
#     input_folder = "input"

#     if os.path.exists(input_folder):
#         import shutil
#         shutil.rmtree(input_folder)
#     os.makedirs(input_folder, exist_ok=True)

#     print(f"Decompiling {file_path} with JADX...")
#     try:
#         subprocess.run([jadx_path, "-d", input_folder, file_path], check=True)
#         print("Decompiled OK.")
#     except Exception as e:
#         print("JADX failed:", e)
#         return

#     run_analysis(input_folder)

# # -------------------- ENTRY POINT --------------------
# if __name__ == "__main__":
#     if len(sys.argv) == 2 and (sys.argv[1].endswith(".dex") or sys.argv[1].endswith(".apk")):
#         analyze_dex_or_apk(sys.argv[1])
#     else:
#         # run_analysis("input")
#         script_dir = os.path.dirname(os.path.abspath(__file__))
#         input_path = os.path.join(script_dir, "..", "input")
#         run_analysis(os.path.abspath(input_path))


# import os
# import subprocess
# import re
# import sys
# import traceback
# from io import StringIO

# # ---------------- Custom modules ----------------
# from utils.nameIdentifier import IdentifierCleaner
# try:
#     from utils.nameIdentifier import detect_language
# except ImportError:
#     # fallback if missing
#     def detect_language(filename):
#         if filename.endswith(".py"):
#             return "python"
#         return "clike"

# from utils.controlFlow import FakeConditionCleaner
# from utils.stringEncryption import StringDecryptor
# from utils.deadcode import clean_deadcode_python, clean_deadcode_clike
# from utils.inlineExpansion import clean_inline_expansion_python, clean_inline_expansion_clike
# from utils.opaque_predicate import clean_opaque_predicate_python, clean_opaque_predicate_clike
# from utils.controlflow_flattening import clean_controlflow_flattening_python, clean_controlflow_flattening_clike
# from utils.instruction_substitution import clean_instruction_substitution_python, clean_instruction_substitution_clike
# from utils.dynamic_loading import clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike
# from utils.junkcode import clean_junk_code_python, clean_junk_code_clike
# from utils.api_redirection import clean_api_redirection_python, clean_api_redirection_clike
# from utils.mixed_language import clean_mixed_language_python, clean_mixed_language_clike

# # -------------------- PDF EXPORT --------------------
# def save_pdf(results, pdf_path):
#     from reportlab.lib.pagesizes import letter
#     from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
#     from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
#     from reportlab.lib.enums import TA_CENTER
#     from xml.sax.saxutils import escape

#     os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
#     doc = SimpleDocTemplate(pdf_path, pagesize=letter)
#     styles = getSampleStyleSheet()
#     title_style = ParagraphStyle(
#         name="TitleStyle",
#         parent=styles["Heading1"],
#         alignment=TA_CENTER,
#         fontSize=16,
#         spaceAfter=20
#     )
#     normal_style = ParagraphStyle(
#         name="NormalStyle",
#         parent=styles["Normal"],
#         fontSize=10,
#         leading=12,
#     )

#     content = [Paragraph("🔍 Code Analysis Results", title_style), Spacer(1, 12)]

#     for line in results.split("\n"):
#         line = line.strip()
#         if not line:
#             continue
#         safe_line = escape(line.replace("→", "->"))
#         if line.startswith("====="):
#             content.append(PageBreak())
#             content.append(Paragraph(safe_line, styles["Heading2"]))
#             content.append(Spacer(1, 12))
#         else:
#             content.append(Paragraph(safe_line, normal_style))
#             content.append(Spacer(1, 6))

#     doc.build(content)
#     print(f"📄 PDF saved at {os.path.abspath(pdf_path)}")

# # -------------------- Helpers --------------------
# SCANNABLE_EXTS = (".java", ".py", ".cpp", ".c", ".js", ".smali", ".kt", ".xml", ".txt")
# VERBOSE = True

# def safe_read_text_file(path):
#     for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
#         try:
#             with open(path, "r", encoding=enc) as f:
#                 return f.read()
#         except Exception:
#             continue
#     raise UnicodeError(f"Unable to read file {path} with common encodings")

# # -------------------- Extra Heuristics --------------------
# def extra_heuristics_scan(text, filepath):
#     findings = {
#         "Dead Code": [],
#         "Inline Expansion": [],
#         "Opaque Predicates": [],
#         "Control Flow Flattening": [],
#         "Instruction Substitution": [],
#         "Dynamic Code Loading": [],
#         "Junk Code": [],
#         "API Redirection": [],
#         "Identifier Obfuscation": [],
#     }

#     _constant_arith_re = re.compile(r'\b\d+\s*[\+\-\*\/%]\s*\d+\b')
#     _wrapper_function_re = re.compile(r'\breturn\s+[a-zA-Z0-9_]+\s*\(', re.IGNORECASE)
#     _reflection_re = re.compile(r'\b(Class\.forName|forName\(|getMethod\(|invoke\(|loadLibrary\(|loadClass\()', re.IGNORECASE)
#     _junk_nop_re_smali = re.compile(r'\bnop\b', re.IGNORECASE)
#     _junk_add_zero_re = re.compile(r'\b([A-Za-z_]\w*)\s*=\s*\1\s*[\+\-]\s*0\b')
#     _switch_state_re = re.compile(r'\bswitch\b|\bcase\b|\bstate\b', re.IGNORECASE)
#     _goto_like_re = re.compile(r'\bgoto\b|\bif-?eqz\b|\bif-?nez\b', re.IGNORECASE)

#     for m in re.finditer(r'\bif\s*\(\s*(false|0|0x0|0x00)\s*\)', text, re.IGNORECASE):
#         findings["Dead Code"].append(f"{filepath}: constant-if -> {m.group(0)}")

#     for m in _constant_arith_re.finditer(text):
#         findings["Inline Expansion"].append(f"{filepath}: const-arith '{m.group(0)}'")

#     for m in re.finditer(r'(\d+\s*[\+\-\*\/]\s*\d+)\s*==\s*\d+', text):
#         findings["Opaque Predicates"].append(f"{filepath}: constant-compare '{m.group(0)}'")

#     short_ids = set(re.findall(r'\b[a-zA-Z]\b|\b[a-zA-Z]{1,2}\d?\b', text))
#     if len(short_ids) > 30:
#         findings["Identifier Obfuscation"].append(f"{filepath}: many short identifiers ({len(short_ids)})")

#     for m in _wrapper_function_re.finditer(text):
#         findings["API Redirection"].append(f"{filepath}: wrapper-call-like {m.group(0)}")

#     for m in _reflection_re.finditer(text):
#         findings["Dynamic Code Loading"].append(f"{filepath}: reflection/dynamic API {m.group(0)}")

#     if _junk_nop_re_smali.search(text):
#         findings["Junk Code"].append(f"{filepath}: smali NOP found")
#     for m in _junk_add_zero_re.finditer(text):
#         findings["Junk Code"].append(f"{filepath}: add-zero {m.group(0)}")

#     if _goto_like_re.search(text) or _switch_state_re.search(text):
#         findings["Control Flow Flattening"].append(f"{filepath}: goto/switch/state-like patterns")

#     if re.search(r'\b-\s*\(-\d+\)|\b\+\s*0\b|\b-\s*0\b', text):
#         findings["Instruction Substitution"].append(f"{filepath}: possible instruction substitution")

#     return {k: v for k, v in findings.items() if v}

# # -------------------- FILE ANALYSIS --------------------
# def analyze_file(filepath):
#     try:
#         text = safe_read_text_file(filepath)
#     except Exception as e:
#         return {"__error__": [f"{filepath}: read error: {e}"]}

#     per_file = {name: [] for name in [
#         "String Encryption", "Identifier Cleaner", "Control Flow", "Dead Code",
#         "Inline Expansion", "Opaque Predicates", "Control Flow Flattening",
#         "Instruction Substitution", "Dynamic Code Loading", "Junk Code",
#         "API Redirection", "Mixed Language Obfuscation", "Identifier Obfuscation"
#     ]}

#     if VERBOSE:
#         print(f"[*] Analyzing: {filepath}")

#     lang = detect_language(os.path.basename(filepath))

#     # String decryption
#     try:
#         str_cleaner = StringDecryptor()
#         str_changes, text = str_cleaner.detect_and_clean(text)
#         for c in str_changes:
#             orig = c.get('original_line', '').strip()
#             clean = c.get('cleaned_line', '').strip()
#             reason = c.get('reason', '')
#             per_file["String Encryption"].append(f"{filepath}: {orig} -> {clean} ({reason})")
#     except Exception as e:
#         per_file["String Encryption"].append(f"{filepath}: Error - {e}")

#     # Identifier cleaner
#     try:
#         id_cleaner = IdentifierCleaner(language=lang)
#         id_changes, text = id_cleaner.detect_and_clean(text)
#         for c in id_changes:
#             per_file["Identifier Cleaner"].append(f"{filepath}: {c.get('original','')} -> {c.get('cleaned','')} ({c.get('reason','')})")
#     except Exception as e:
#         per_file["Identifier Cleaner"].append(f"{filepath}: Error - {e}")

#     # Control flow
#     try:
#         cf = FakeConditionCleaner()
#         cf_changes = cf.clean_code(text)
#         for c in cf_changes:
#             per_file["Control Flow"].append(f"{filepath}: {c.get('original','')} -> {c.get('cleaned','')} ({c.get('reason','')})")
#     except Exception as e:
#         per_file["Control Flow"].append(f"{filepath}: Error - {e}")

#     # Modular analyzers
#     tech_map = {
#         "Dead Code": (clean_deadcode_python, clean_deadcode_clike),
#         "Inline Expansion": (clean_inline_expansion_python, clean_inline_expansion_clike),
#         "Opaque Predicates": (clean_opaque_predicate_python, clean_opaque_predicate_clike),
#         "Control Flow Flattening": (clean_controlflow_flattening_python, clean_controlflow_flattening_clike),
#         "Instruction Substitution": (clean_instruction_substitution_python, clean_instruction_substitution_clike),
#         "Dynamic Code Loading": (clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike),
#         "Junk Code": (clean_junk_code_python, clean_junk_code_clike),
#         "API Redirection": (clean_api_redirection_python, clean_api_redirection_clike),
#         "Mixed Language Obfuscation": (clean_mixed_language_python, clean_mixed_language_clike),
#     }

#     for name, (py_fn, clike_fn) in tech_map.items():
#         try:
#             fn = py_fn if lang == "python" else clike_fn
#             changes = fn(text)
#             if isinstance(changes, list):
#                 for ch in changes:
#                     per_file[name].append(f"{filepath}: {ch}")
#         except Exception:
#             per_file[name].append(f"{filepath}: Error - {traceback.format_exc()}")

#     # Heuristics
#     heur = extra_heuristics_scan(text, filepath)
#     for k, vs in heur.items():
#         per_file.setdefault(k, []).extend(vs)

#     return per_file

# # -------------------- RUNNER --------------------
# def run_analysis(input_folder):
#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     output_dir = os.path.join(base_dir, "..", "output")
#     os.makedirs(output_dir, exist_ok=True)
#     txt_output = os.path.join(output_dir, "combined_results.txt")
#     pdf_output = os.path.join(output_dir, "combined_results.pdf")

#     files_to_scan = []
#     for root, _, files in os.walk(input_folder):
#         for fn in files:
#             if fn.lower().endswith(SCANNABLE_EXTS):
#                 files_to_scan.append(os.path.join(root, fn))

#     print(f"Found {len(files_to_scan)} scannable files under '{input_folder}'")

#     all_results = {}
#     report_lines = [f"Analysis summary:\n- scanned files: {len(files_to_scan)}\n"]

#     for idx, fp in enumerate(files_to_scan, 1):
#         per_file = analyze_file(fp)
#         report_lines.append(f"\n===== {os.path.basename(fp)} =====\n")
#         for k, v in per_file.items():
#             if v:
#                 report_lines.append(f"--- {k} ---")
#                 report_lines.extend(v)

#     final_report = "\n".join(report_lines)
#     with open(txt_output, "w", encoding="utf-8") as f:
#         f.write(final_report)

#     save_pdf(final_report, pdf_output)
#     print(f"\n✅ Done.\n📄 Text report: {os.path.abspath(txt_output)}\n📘 PDF report: {os.path.abspath(pdf_output)}")

# # -------------------- MAIN --------------------
# if __name__ == "__main__":
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     input_dir = os.path.join(script_dir, "..", "input")
#     run_analysis(os.path.abspath(input_dir))


# import os
# import re
# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from utils.nameIdentifier import IdentifierCleaner, detect_language
# from utils.stringEncryption import StringDecryptor
# from utils.api_redirection import ApiRedirectDetector
# from utils.controlflow_flattening import ControlFlowFlattener
# from utils.deadcode import DeadCodeAnalyzer
# from utils.dynamic_loading import DynamicLoaderAnalyzer
# from utils.inlineExpansion import InlineExpansionAnalyzer
# from utils.instruction_substitution import InstructionSubstitutionAnalyzer
# from utils.junkcode import JunkCodeAnalyzer
# from utils.mixed_language import MixedLanguageAnalyzer
# from utils.opaque_predicate import OpaquePredicateAnalyzer

# # -------------------- SETTINGS --------------------
# SCANNABLE_EXTS = (".java", ".py", ".cpp", ".c", ".js", ".smali", ".kt", ".xml", ".txt")

# # -------------------- HELPER FUNCTIONS --------------------
# def read_file(filepath):
#     """Reads a file and returns its content as a list of lines."""
#     try:
#         with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
#             return f.readlines()
#     except Exception as e:
#         print(f"[!] Error reading {filepath}: {e}")
#         return []

# def collect_files(folder):
#     """Collects all files from a folder (recursively)."""
#     all_files = []
#     for root, _, files in os.walk(folder):
#         for file in files:
#             if file.endswith(SCANNABLE_EXTS):
#                 all_files.append(os.path.join(root, file))
#     return all_files

# def save_pdf(results, pdf_path):
#     """Saves analysis results as a PDF file."""
#     styles = getSampleStyleSheet()
#     doc = SimpleDocTemplate(pdf_path, pagesize=letter)
#     story = []

#     for section in results.split("\n\n"):
#         story.append(Paragraph(section.replace("\n", "<br/>"), styles["Normal"]))
#         story.append(Spacer(1, 12))

#     doc.build(story)

# # -------------------- MAIN ANALYSIS --------------------
# def run_analysis(input_folder):
#     print(f"\n🔍 Starting analysis in folder: {input_folder}")
#     files_to_scan = collect_files(input_folder)
#     print(f"📁 Found {len(files_to_scan)} scannable files under '{input_folder}'")

#     if not files_to_scan:
#         print("⚠️  No files found to scan. Exiting.")
#         return

#     all_findings = []
#     all_errors = []

#     # Process each file
#     for idx, filepath in enumerate(files_to_scan, start=1):
#         print(f"\n[{idx}/{len(files_to_scan)}] Analyzing: {filepath}")
#         try:
#             code_lines = read_file(filepath)
#             code_text = "".join(code_lines)
#             language = detect_language(filepath)

#             # Run all detectors
#             cleaners = [
#                 IdentifierCleaner(),
#                 StringDecryptor(),
#                 ApiRedirectDetector(),
#                 ControlFlowFlattener(),
#                 DeadCodeAnalyzer(),
#                 DynamicLoaderAnalyzer(),
#                 InlineExpansionAnalyzer(),
#                 InstructionSubstitutionAnalyzer(),
#                 JunkCodeAnalyzer(),
#                 MixedLanguageAnalyzer(),
#                 OpaquePredicateAnalyzer(),
#             ]

#             findings = []
#             for cleaner in cleaners:
#                 try:
#                     res = cleaner.analyze(code_text, language)
#                     if res:
#                         findings.append(f"{cleaner.__class__.__name__}:\n{res}")
#                 except Exception as inner_e:
#                     all_errors.append(f"{filepath}: {cleaner.__class__.__name__} - {inner_e}")

#             if findings:
#                 all_findings.append(f"===== {os.path.basename(filepath)} =====\n" + "\n\n".join(findings))
#             else:
#                 all_findings.append(f"===== {os.path.basename(filepath)} =====\nNo significant findings detected.\n")

#         except Exception as e:
#             all_errors.append(f"{filepath}: {e}")

#     # -------------------- OUTPUT SECTION --------------------
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     output_dir = os.path.join(script_dir, "output")
#     os.makedirs(output_dir, exist_ok=True)

#     text_output = os.path.join(output_dir, "combined_results.txt")
#     pdf_output = os.path.join(output_dir, "combined_results.pdf")

#     final_report = "\n\n".join(all_findings)
#     if all_errors:
#         final_report += "\n\n===== Errors =====\n" + "\n".join(all_errors)

#     # Save TXT
#     with open(text_output, "w", encoding="utf-8") as f:
#         f.write(final_report)

#     # Save PDF
#     save_pdf(final_report, pdf_output)

#     print("\n✅ Analysis completed successfully.")
#     print(f"📄 Text report: {os.path.abspath(text_output)}")
#     print(f"📘 PDF report:  {os.path.abspath(pdf_output)}")


# # -------------------- MAIN ENTRY --------------------
# if __name__ == "__main__":
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     input_dir = os.path.join(script_dir, "input")  # ✅ Fixed path
#     run_analysis(os.path.abspath(input_dir))


# merged_verbose_merge.py
import os
import subprocess
import re
import ast
from io import StringIO
import sys
import traceback

# ---------------- Custom modules (unchanged) ----------------
from utils.nameIdentifier import IdentifierCleaner, detect_language
from utils.controlFlow import FakeConditionCleaner
from utils.stringEncryption import StringDecryptor
from utils.deadcode import clean_deadcode_python, clean_deadcode_clike
from utils.inlineExpansion import clean_inline_expansion_python, clean_inline_expansion_clike
from utils.opaque_predicate import clean_opaque_predicate_python, clean_opaque_predicate_clike
from utils.controlflow_flattening import clean_controlflow_flattening_python, clean_controlflow_flattening_clike
from utils.instruction_substitution import clean_instruction_substitution_python, clean_instruction_substitution_clike
from utils.dynamic_loading import clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike
from utils.junkcode import clean_junk_code_python, clean_junk_code_clike
from utils.api_redirection import clean_api_redirection_python, clean_api_redirection_clike
from utils.mixed_language import clean_mixed_language_python, clean_mixed_language_clike

# -------------------- PDF EXPORT (fixed for Java code) --------------------
def save_pdf(results, pdf_path="output/combined_results.pdf"):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from xml.sax.saxutils import escape  # ✅ escape < > & symbols

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=20
    )
    normal_style = ParagraphStyle(
        name="NormalStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
    )

    content = [Paragraph("🔍 Code Analysis Results", title_style), Spacer(1, 12)]

    for line in results.split("\n"):
        line = line.strip()
        if not line:
            continue

        # ✅ Escape HTML-sensitive characters and fix arrow symbol
        safe_line = escape(line.replace("→", "->"))

        if line.startswith("====="):
            content.append(PageBreak())
            content.append(Paragraph(safe_line, styles["Heading2"]))
            content.append(Spacer(1, 12))
        else:
            if "->" in line or "No cases detected." in line or "Error" in line or line.startswith("- "):
                content.append(Paragraph(safe_line, normal_style))
                content.append(Spacer(1, 6))

    doc.build(content)
    print(f"📄 PDF saved at {pdf_path}")

# -------------------- Helpers --------------------
SCANNABLE_EXTS = (".java", ".py", ".cpp", ".c", ".js", ".smali", ".kt", ".xml", ".txt")
VERBOSE = True

def safe_read_text_file(path):
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except Exception:
            continue
    raise UnicodeError(f"Unable to read file {path} with common encodings")

# Heuristics
_proguard_shortname_re = re.compile(r'\b([a-zA-Z]{1,2}\d{0,2}|[a-zA-Z]\d{1,3})\b')
_wrapper_function_re = re.compile(r'\breturn\s+[a-zA-Z0-9_]+\s*\(', re.IGNORECASE)
_reflection_re = re.compile(r'\b(Class\.forName|forName\(|getMethod\(|invoke\(|loadLibrary\(|loadClass\()', re.IGNORECASE)
_junk_nop_re_smali = re.compile(r'\bnop\b', re.IGNORECASE)
_junk_add_zero_re = re.compile(r'\b([A-Za-z_]\w*)\s*=\s*\1\s*[\+\-]\s*0\b')
_constant_arith_re = re.compile(r'\b\d+\s*[\+\-\*\/%]\s*\d+\b')
_switch_state_re = re.compile(r'\bswitch\b|\bcase\b|\bstate\b', re.IGNORECASE)
_goto_like_re = re.compile(r'\bgoto\b|\bif-?eqz\b|\bif-?nez\b', re.IGNORECASE)

# -------------------- Per-file heuristic scan --------------------
def extra_heuristics_scan(text, filepath):
    findings = {
        "Dead Code": [],
        "Inline Expansion": [],
        "Opaque Predicates": [],
        "Control Flow Flattening": [],
        "Instruction Substitution": [],
        "Dynamic Code Loading": [],
        "Junk Code": [],
        "API Redirection": [],
        "Identifier Obfuscation": [],
    }

    for m in re.finditer(r'\bif\s*\(\s*(false|0|0x0|0x00)\s*\)', text, re.IGNORECASE):
        findings["Dead Code"].append(f"constant-if at {m.start()} -> {m.group(0)[:80]}")

    for m in re.finditer(r'\breturn\b[^;{]*[;}]', text):
        pos = m.end()
        following = text[pos:pos+200]
        if following.strip():
            findings["Dead Code"].append(f"code_after_return at {pos}")

    for m in _constant_arith_re.finditer(text):
        findings["Inline Expansion"].append(f"const-arith '{m.group(0)}'")

    for m in re.finditer(r'(\d+\s*[\+\-\*\/]\s*\d+)\s*==\s*\d+', text):
        findings["Opaque Predicates"].append(f"constant-compare '{m.group(0)}'")

    short_ids = set(re.findall(r'\b[a-zA-Z]\b|\b[a-zA-Z]{1,2}\d?\b', text))
    if len(short_ids) > 30:
        findings["Identifier Obfuscation"].append(f"many short identifiers ({len(short_ids)}) — possible ProGuard renames")

    for m in _wrapper_function_re.finditer(text):
        findings["API Redirection"].append(f"wrapper-call-like: {m.group(0)[:60]}")

    for m in _reflection_re.finditer(text):
        findings["Dynamic Code Loading"].append(f"reflection/dynamic API: {m.group(0)}")

    if _junk_nop_re_smali.search(text):
        findings["Junk Code"].append("smali NOP found")
    for m in _junk_add_zero_re.finditer(text):
        findings["Junk Code"].append(f"add-zero: {m.group(0)}")

    if _goto_like_re.search(text) or _switch_state_re.search(text):
        findings["Control Flow Flattening"].append("goto/switch/state-like patterns present")

    if re.search(r'\b-\s*\(-\d+\)|\b\+\s*0\b|\b-\s*0\b', text):
        findings["Instruction Substitution"].append("possible instruction substitution expression")

    if len(re.findall(r'\breturn\b.*\(', text)) > 50:
        findings["API Redirection"].append("many small wrappers returning other calls (>50)")

    return {k: v for k, v in findings.items() if v}

# -------------------- FILE ANALYSIS --------------------
def analyze_file(filepath):
    try:
        text = safe_read_text_file(filepath)
    except Exception as e:
        return {"__error__": [f"{filepath}: read error: {e}"]}

    per_file = {k: [] for k in [
        "String Encryption", "Identifier Cleaner", "Control Flow", "Dead Code", "Inline Expansion",
        "Opaque Predicates", "Control Flow Flattening", "Instruction Substitution", "Dynamic Code Loading",
        "Junk Code", "API Redirection", "Mixed Language Obfuscation", "Identifier Obfuscation"
    ]}

    if VERBOSE:
        print(f"[*] Analyzing: {filepath}")

    lang = detect_language(os.path.basename(filepath))

    # String decryption (fixed)
    try:
        str_cleaner = StringDecryptor()
        str_changes, text = str_cleaner.detect_and_clean(text)
        for c in str_changes:
            orig_line = c.get('original_line', '').strip()
            cleaned_line = c.get('cleaned_line', '').strip()
            reason = c.get('reason', '').strip()
            maxlen = 400
            if len(orig_line) > maxlen:
                orig_line = orig_line[:maxlen] + '...'
            if len(cleaned_line) > maxlen:
                cleaned_line = cleaned_line[:maxlen] + '...'
            per_file["String Encryption"].append(
                f"{filepath}: obf-line: {orig_line} -> deobf-line: {cleaned_line} ({reason})"
            )
    except Exception as e:
        per_file["String Encryption"].append(f"{filepath}: Error - {e}")

    # Identifier cleaner
    try:
        id_cleaner = IdentifierCleaner(language=lang)
        id_changes, text = id_cleaner.detect_and_clean(text)
        # for c in id_changes:
        #     per_file["Identifier Cleaner"].append(
        #         f"{filepath}: {c.get('original','')} (Obfuscated identifier)"
        #     )
        for c in id_changes:
            per_file["Identifier Cleaner"].append(
                f"{filepath}: {c.get('original','')} -> {c.get('cleaned','')} ({c.get('reason','')})"
            )
       
    except Exception as e:
        per_file["Identifier Cleaner"].append(f"{filepath}: Error - {e}")

    # Control flow fake conditions
    try:
        cf = FakeConditionCleaner()
        cf_changes = cf.clean_code(text)
        for c in cf_changes:
            per_file["Control Flow"].append(
                f"{filepath}: {c.get('original','')} -> {c.get('cleaned','')} ({c.get('reason','')})"
            )
            text = text.replace(c.get('original',''), c.get('cleaned',''))
    except Exception as e:
        per_file["Control Flow"].append(f"{filepath}: Error - {e}")

    # Technique mapping
    tech_map = {
        "Dead Code": (clean_deadcode_python, clean_deadcode_clike),
        "Inline Expansion": (clean_inline_expansion_python, clean_inline_expansion_clike),
        "Opaque Predicates": (clean_opaque_predicate_python, clean_opaque_predicate_clike),
        "Control Flow Flattening": (clean_controlflow_flattening_python, clean_controlflow_flattening_clike),
        "Instruction Substitution": (clean_instruction_substitution_python, clean_instruction_substitution_clike),
        "Dynamic Code Loading": (clean_dynamic_code_loading_python, clean_dynamic_code_loading_clike),
        "Junk Code": (clean_junk_code_python, clean_junk_code_clike),
        "API Redirection": (clean_api_redirection_python, clean_api_redirection_clike),
        "Mixed Language Obfuscation": (clean_mixed_language_python, clean_mixed_language_clike),
    }

    for name, (py_fn, clike_fn) in tech_map.items():
        try:
            changes = py_fn(text) if lang == "python" else clike_fn(text)
            if isinstance(changes, (list, tuple)):
                for ch in changes:
                    orig = ch.get("original", "") if isinstance(ch, dict) else str(ch)
                    clean = ch.get("cleaned", "") if isinstance(ch, dict) else ""
                    reason = ch.get("reason", "") if isinstance(ch, dict) else ""
                    per_file[name].append(f"{filepath}: {orig[:140]} -> {clean[:140]} ({reason})")
                    if orig:
                        text = text.replace(orig, clean)
            else:
                per_file[name].append(f"{filepath}: detector returned non-list result")
        except Exception:
            per_file[name].append(f"{filepath}: Error - {traceback.format_exc()}")

    heur = extra_heuristics_scan(text, filepath)
    for k, vs in heur.items():
        bucket = "Identifier Obfuscation" if k == "Identifier Obfuscation" else k
        per_file.setdefault(bucket, [])
        for v in vs:
            per_file[bucket].append(f"{filepath}: {v}")

    return per_file

# -------------------- RUNNER --------------------
def run_analysis(input_folder="input"):
    output_file = "output/combined_results.txt"
    os.makedirs("output", exist_ok=True)

    all_results = {k: [] for k in [
        "String Encryption", "Identifier Cleaner", "Control Flow", "Dead Code", "Inline Expansion",
        "Opaque Predicates", "Control Flow Flattening", "Instruction Substitution", "Dynamic Code Loading",
        "Junk Code", "API Redirection", "Mixed Language Obfuscation", "Identifier Obfuscation"
    ]}

    files_to_scan = []
    for root, _, files in os.walk(input_folder):
        for fn in files:
            if fn.lower().endswith(SCANNABLE_EXTS):
                files_to_scan.append(os.path.join(root, fn))

    print(f"Found {len(files_to_scan)} scannable files under '{input_folder}'")

    per_file_summary = []
    for idx, fp in enumerate(files_to_scan, start=1):
        try:
            per_file = analyze_file(fp)
        except Exception:
            per_file = {"__error__": [f"{fp}: unexpected analyzer error\n{traceback.format_exc()}"]}

        if "__error__" in per_file:
            all_results.setdefault("Errors", []).extend(per_file["__error__"])
            per_file_summary.append((fp, 0, True))
            continue

        counts = {k: len(v) for k, v in per_file.items()}
        total = sum(counts.values())
        per_file_summary.append((fp, total, False))
        if VERBOSE:
            print(f"[{idx}/{len(files_to_scan)}] {os.path.relpath(fp)} -> findings: {total} (breakdown: {counts})")

        for k, vs in per_file.items():
            if not vs:
                continue
            key = k
            if key not in all_results:
                all_results[key] = []
            all_results[key].extend(vs)

    report_lines = [
        "Analysis summary:",
        f"- scanned files: {len(files_to_scan)}",
        f"- total findings: {sum(len(v) for v in all_results.values())}",
        "\nPer-file summary (first 40 entries):"
    ]
    for fp, tot, is_err in per_file_summary[:40]:
        status = "ERROR" if is_err else f"{tot} findings"
        report_lines.append(f"- {fp} : {status}")

    for technique, findings in all_results.items():
        report_lines.append(f"\n===== {technique} =====\n")
        if findings:
            report_lines.extend(findings)
        else:
            report_lines.append("No cases detected.")
        report_lines.append("\n")

    final_report = "\n".join(report_lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_report)

    save_pdf(final_report)
    print(f"\n✅ Done. Scanned {len(files_to_scan)} files.")
    print(f"Results saved: {output_file} and output/combined_results.pdf")

# -------------------- AUTO-INTEGRATION WRAPPER --------------------
def analyze_dex_or_apk(file_path):
    jadx_path = r"C:\jadx\bin\jadx.bat"
    input_folder = "input"

    if os.path.exists(input_folder):
        import shutil
        shutil.rmtree(input_folder)
    os.makedirs(input_folder, exist_ok=True)

    print(f"Decompiling {file_path} with JADX...")
    try:
        subprocess.run([jadx_path, "-d", input_folder, file_path], check=True)
        print("Decompiled OK.")
    except Exception as e:
        print("JADX failed:", e)
        return

    run_analysis(input_folder)

# -------------------- ENTRY POINT --------------------
# if __name__ == "__main__":
#     if len(sys.argv) == 2 and (sys.argv[1].endswith(".dex") or sys.argv[1].endswith(".apk")):
#         analyze_dex_or_apk(sys.argv[1])
#     else:
#         run_analysis("input")

# ---------------- ENTRY POINT ----------------
if __name__ == "__main__":
    # Get absolute path of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input")
    os.makedirs(input_dir, exist_ok=True)  # ensure folder exists

    # Debug print (optional)
    print(f"[+] Scanning input folder: {input_dir}")

    if len(sys.argv) == 2 and (sys.argv[1].endswith(".dex") or sys.argv[1].endswith(".apk")):
        analyze_dex_or_apk(sys.argv[1])
    else:
        run_analysis(input_dir)

