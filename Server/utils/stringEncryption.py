import re

def xor_decrypt(enc_list, key=42):
    """XOR decrypt a list of integers to a string."""
    try:
        return ''.join(chr(c ^ key) for c in enc_list)
    except Exception:
        return None


class StringDecryptor:
    """Detects and decrypts XOR-encrypted strings in code."""

    def __init__(self, key=42):
        self.key = key

    def detect_strings(self, code: str):
        """Detect candidate encrypted strings as list of integers and return contextual lines."""
        # Match only well-formed numeric arrays like [65, 66, 67]
        pattern = re.compile(r'\[([0-9,\s]+)\]')
        results = []

        for match in pattern.finditer(code):
            str_bytes = match.group(1)
            try:
                enc_list = [int(b.strip()) for b in str_bytes.split(',') if b.strip().isdigit()]
                if not enc_list or len(enc_list) < 2:
                    continue  # skip single numbers like [0]

                decrypted = xor_decrypt(enc_list, self.key)
                if not decrypted:
                    continue

                # ensure all chars printable
                if not all(32 <= ord(ch) <= 126 for ch in decrypted):
                    continue

                # filter out suspicious garbage (too short / punctuation-heavy)
                if len(decrypted.strip()) < 3:
                    continue
                if sum(ch.isalnum() for ch in decrypted) / len(decrypted) < 0.6:
                    continue  # ignore random punctuation-only strings

                pos = match.start()
                line_start = code.rfind('\n', 0, pos) + 1
                line_end = code.find('\n', pos)
                if line_end == -1:
                    line_end = len(code)

                original_line = code[line_start:line_end].rstrip()
                cleaned_line = original_line.replace(match.group(0), f'"{decrypted}"')

                results.append({
                    "original": match.group(0),
                    "decrypted": decrypted,
                    "position": pos,
                    "reason": "XOR-encrypted string detected and decrypted",
                    "original_line": original_line,
                    "cleaned_line": cleaned_line
                })
            except Exception:
                continue
        return results

    def detect_and_clean(self, code: str):
        """Detect encrypted strings, replace them in the code, and return changes + final code."""
        results = self.detect_strings(code)
        cleaned_code = code

        for res in reversed(results):
            original_literal = res['original']
            start_idx = cleaned_code.find(original_literal)
            if start_idx != -1:
                cleaned_code = (
                    cleaned_code[:start_idx]
                    + f'"{res["decrypted"]}"'
                    + cleaned_code[start_idx + len(original_literal):]
                )
                res['cleaned'] = f'"{res["decrypted"]}"'
        return results, cleaned_code
