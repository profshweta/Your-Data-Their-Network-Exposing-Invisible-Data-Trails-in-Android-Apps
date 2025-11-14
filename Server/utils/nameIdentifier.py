import re
import ast
import keyword
import builtins

# ----------------------------------------
# Reserved keywords for multiple languages
# ----------------------------------------
LANG_KEYWORDS = {
    "python": set(keyword.kwlist) | set(dir(builtins)),
    "c": {
        "auto","break","case","char","const","continue","default","do","double",
        "else","enum","extern","float","for","goto","if","inline","int","long",
        "register","restrict","return","short","signed","sizeof","static",
        "struct","switch","typedef","union","unsigned","void","volatile","while"
    },
    "cpp": {
        "asm","auto","bool","break","case","catch","char","class","const","const_cast",
        "continue","default","delete","do","double","dynamic_cast","else","enum","explicit",
        "export","extern","false","float","for","friend","goto","if","inline","int","long",
        "mutable","namespace","new","operator","private","protected","public","register",
        "reinterpret_cast","return","short","signed","sizeof","static","static_cast",
        "struct","switch","template","this","throw","true","try","typedef","typeid",
        "typename","union","unsigned","using","virtual","void","volatile","wchar_t","while"
    },
    "java": {
        "abstract","assert","boolean","break","byte","case","catch","char","class","const",
        "continue","default","do","double","else","enum","extends","final","finally","float",
        "for","goto","if","implements","import","instanceof","int","interface","long",
        "native","new","package","private","protected","public","return","short","static",
        "strictfp","super","switch","synchronized","this","throw","throws","transient","try",
        "void","volatile","while"
    },
    "kotlin": {
        "as","break","class","continue","do","else","false","for","fun","if","in",
        "interface","is","null","object","package","return","super","this","throw",
        "true","try","typealias","typeof","val","var","when","while"
    }
}

# ----------------------------------------
# Identifier Obfuscation Detection
# ----------------------------------------
def is_obfuscated_name(name: str, language: str = "python") -> bool:
    """Detect obfuscated identifiers like x1a3, a1, f2 but exclude language keywords."""
    reserved = LANG_KEYWORDS.get(language, set())
    if name in reserved:
        return False
    # Rule: short name with numbers inside
    return bool(re.fullmatch(r"[a-zA-Z]{1,3}\d+[a-zA-Z0-9]*", name))


# ----------------------------------------
# AST Visitor for Python
# ----------------------------------------
class NameCollector(ast.NodeVisitor):
    """Collects identifiers from Python AST."""
    def __init__(self, language="python"):
        self.funcs = set()
        self.classes = set()
        self.vars = set()
        self.language = language

    def visit_FunctionDef(self, node):
        if is_obfuscated_name(node.name, self.language):
            self.funcs.add(node.name)
        for arg in node.args.args:
            if is_obfuscated_name(arg.arg, self.language):
                self.vars.add(arg.arg)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if is_obfuscated_name(node.name, self.language):
            self.classes.add(node.name)
        self.generic_visit(node)

    def visit_Name(self, node):
        if is_obfuscated_name(node.id, self.language):
            self.vars.add(node.id)


# ----------------------------------------
# Main Cleaner Class (like FakeConditionCleaner)
# ----------------------------------------
class IdentifierCleaner:
    """Detects obfuscated identifiers and returns original, cleaned, reason."""

    def __init__(self, language="python"):
        self.language = language

    def detect_and_clean(self, code):
        """
        Returns:
            changes: list of dicts with keys ['original', 'cleaned', 'reason']
            cleaned_code: code after replacing obfuscated identifiers
        """
        mapping = {}
        changes = []
        func_count, class_count, var_count = 1, 1, 1

        # ----------------------------------------
        # Python AST-based collection
        # ----------------------------------------
        if self.language == "python":
            tree = ast.parse(code)
            collector = NameCollector(self.language)
            collector.visit(tree)

            for f in sorted(collector.funcs):
                mapping[f] = f"func{func_count}"; func_count += 1
            for c in sorted(collector.classes):
                mapping[c] = f"Class{class_count}"; class_count += 1
            for v in sorted(collector.vars):
                mapping[v] = f"var{var_count}"; var_count += 1

        # ----------------------------------------
        # Regex-based collection for other languages
        # ----------------------------------------
        else:
            identifiers = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", code)
            for name in set(identifiers):
                if is_obfuscated_name(name, self.language):
                    if re.match(r"^[A-Z]", name):  # Class
                        mapping[name] = f"Class{class_count}"; class_count += 1
                    elif re.match(r"^[a-z]", name):
                        if re.search(r"\d", name):  # func-like
                            mapping[name] = f"func{func_count}"; func_count += 1
                        else:
                            mapping[name] = f"var{var_count}"; var_count += 1

        # ----------------------------------------
        # Apply mapping and generate change log
        # ----------------------------------------
        def replace_identifier(match):
            word = match.group(0)
            new_word = mapping.get(word, word)
            if word != new_word:
                changes.append({
                    "original": word,
                    "reason": "Obfuscated identifier"
            })

            return new_word

        cleaned_code = re.sub(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", replace_identifier, code)
        return changes, cleaned_code


# ----------------------------------------
# Language Detection Helper
# ----------------------------------------
def detect_language(filename: str) -> str:
    """Detect programming language from file extension."""
    ext = filename.split(".")[-1].lower()
    if ext == "py":
        return "python"
    elif ext in ("c", "h"):
        return "c"
    elif ext == "cpp":
        return "cpp"
    elif ext == "java":
        return "java"
    elif ext == "kt":
        return "kotlin"
    return "unknown"

# import re
# import ast
# import keyword
# import builtins

# # ----------------------------------------
# # Reserved keywords for multiple languages
# # ----------------------------------------
# LANG_KEYWORDS = {
#     "python": set(keyword.kwlist) | set(dir(builtins)),
#     "c": {
#         "auto","break","case","char","const","continue","default","do","double",
#         "else","enum","extern","float","for","goto","if","inline","int","long",
#         "register","restrict","return","short","signed","sizeof","static",
#         "struct","switch","typedef","union","unsigned","void","volatile","while"
#     },
#     "cpp": {
#         "asm","auto","bool","break","case","catch","char","class","const","const_cast",
#         "continue","default","delete","do","double","dynamic_cast","else","enum","explicit",
#         "export","extern","false","float","for","friend","goto","if","inline","int","long",
#         "mutable","namespace","new","operator","private","protected","public","register",
#         "reinterpret_cast","return","short","signed","sizeof","static","static_cast",
#         "struct","switch","template","this","throw","true","try","typedef","typeid",
#         "typename","union","unsigned","using","virtual","void","volatile","wchar_t","while"
#     },
#     "java": {
#         "abstract","assert","boolean","break","byte","case","catch","char","class","const",
#         "continue","default","do","double","else","enum","extends","final","finally","float",
#         "for","goto","if","implements","import","instanceof","int","interface","long",
#         "native","new","package","private","protected","public","return","short","static",
#         "strictfp","super","switch","synchronized","this","throw","throws","transient","try",
#         "void","volatile","while"
#     },
#     "kotlin": {
#         "as","break","class","continue","do","else","false","for","fun","if","in",
#         "interface","is","null","object","package","return","super","this","throw",
#         "true","try","typealias","typeof","val","var","when","while"
#     }
# }

# # ----------------------------------------
# # Identifier Obfuscation Detection
# # ----------------------------------------
# def is_obfuscated_name(name: str, language: str = "python") -> bool:
#     """Detect obfuscated identifiers like x1a3, a1, f2 but exclude language keywords."""
#     reserved = LANG_KEYWORDS.get(language, set())
#     if name in reserved:
#         return False
#     # Rule: short name with numbers inside
#     return bool(re.fullmatch(r"[a-zA-Z]{1,3}\d+[a-zA-Z0-9]*", name))


# # ----------------------------------------
# # AST Visitor for Python
# # ----------------------------------------
# class NameCollector(ast.NodeVisitor):
#     """Collects identifiers from Python AST."""
#     def __init__(self, language="python"):
#         self.funcs = set()
#         self.classes = set()
#         self.vars = set()
#         self.language = language

#     def visit_FunctionDef(self, node):
#         if is_obfuscated_name(node.name, self.language):
#             self.funcs.add(node.name)
#         for arg in node.args.args:
#             if is_obfuscated_name(arg.arg, self.language):
#                 self.vars.add(arg.arg)
#         self.generic_visit(node)

#     def visit_ClassDef(self, node):
#         if is_obfuscated_name(node.name, self.language):
#             self.classes.add(node.name)
#         self.generic_visit(node)

#     def visit_Name(self, node):
#         if is_obfuscated_name(node.id, self.language):
#             self.vars.add(node.id)


# # ----------------------------------------
# # Main Cleaner Class (Detection Only)
# # ----------------------------------------
# class IdentifierCleaner:
#     """Detects obfuscated identifiers and logs them (no renaming)."""

#     def __init__(self, language="python"):
#         self.language = language

#     def detect_and_clean(self, code):
#         """
#         Returns:
#             changes: list of dicts with keys ['original', 'reason']
#             cleaned_code: original code (unchanged)
#         """
#         mapping = {}
#         changes = []
#         func_count, class_count, var_count = 1, 1, 1

#         # ----------------------------------------
#         # Python AST-based collection
#         # ----------------------------------------
#         if self.language == "python":
#             tree = ast.parse(code)
#             collector = NameCollector(self.language)
#             collector.visit(tree)

#             for f in sorted(collector.funcs):
#                 mapping[f] = True
#             for c in sorted(collector.classes):
#                 mapping[c] = True
#             for v in sorted(collector.vars):
#                 mapping[v] = True

#         # ----------------------------------------
#         # Regex-based collection for other languages
#         # ----------------------------------------
#         else:
#             identifiers = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", code)
#             for name in set(identifiers):
#                 if is_obfuscated_name(name, self.language):
#                     mapping[name] = True

#         # ----------------------------------------
#         # Apply detection (no renaming)
#         # ----------------------------------------
#         def detect_identifier(match):
#             word = match.group(0)
#             if word in mapping and not any(ch["original"] == word for ch in changes):
#                 changes.append({
#                     "original": word,
#                     "reason": "Obfuscated identifier"
#                 })
#             return word  # Do not modify code

#         cleaned_code = re.sub(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", detect_identifier, code)
#         return changes, cleaned_code


# # ----------------------------------------
# # Language Detection Helper
# # ----------------------------------------
# def detect_language(filename: str) -> str:
#     """Detect programming language from file extension."""
#     ext = filename.split(".")[-1].lower()
#     if ext == "py":
#         return "python"
#     elif ext in ("c", "h"):
#         return "c"
#     elif ext == "cpp":
#         return "cpp"
#     elif ext == "java":
#         return "java"
#     elif ext == "kt":
#         return "kotlin"
#     return "unknown"
