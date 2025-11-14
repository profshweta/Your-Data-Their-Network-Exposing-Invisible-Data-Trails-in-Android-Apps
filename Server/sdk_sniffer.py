from mitmproxy import http, ctx
import json
import re
import gzip
from datetime import datetime

LOG_FILE = "sdk_logs.json"

def wrap_keywords(keywords: str, value_regex: str) -> str:
    return rf'(?i)(?:"?\b(?:{keywords})\b"?\s*[:=\- ]*\s*"?({value_regex})"?)'


patterns = {
    "phone": wrap_keywords(
        r'(?:phone|mobile|contact|tel|cell)(?:[_\s-]?number|num|no)?|phoneno|us',
        r'(?:\+?\d{1,3}[\s\-]?)?(?:\d{10,15})'
    ),
    "otp": wrap_keywords(
        r'otp|otpno|otp_number|verification[\s\-]?code|login[\s\-]?code|auth[\s\-]?code|(?:^|\b)code(?:\b|$)',
        r'\d{4,8}'
    ),
    "pincode": wrap_keywords(r'pincode|postal code|zip', r'\d{6}'),
    "address": wrap_keywords(
        r'address|addr|home[_\s]?address|street|street[_\s]?address',
        r'[A-Za-z0-9][A-Za-z0-9 ,.\-\/]{5,100}'
    ),
    "city": wrap_keywords(
        r'city|town|district',
        r'\b(?!company\b|co\b|com\b)[A-Z][a-z]{2,}(?: [A-Z][a-z]{2,})*\b'
    ),
    "email": wrap_keywords(r'email|e-mail|user email', r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    "number": wrap_keywords(r'id number|account number|aadhaar|pan|voter id', r'[\dA-Za-z\-]{6,}'),
    "dob": wrap_keywords(r'dob|date of birth|birth date|birthday', r'\d{1,2}[-/ ]?(?:\d{1,2}|[A-Za-z]+)[-/ ]?\d{2,4}'),
    "gender": wrap_keywords(r'gender|sex|user_gender|profile_gender', r'\b(?:male|female|other|m|f|trans|nonbinary)\b'),
    "android_id": wrap_keywords(r'\b(?:android_id|aid|a_id|androidid|androidId|aId)\b', r'[0-9a-fA-F]{16}'),
    "advertiser_id": wrap_keywords(r'advertiser_id|adid', r'[A-Fa-f0-9\-]{36}'),
    "anonymous_id": wrap_keywords(r'anonymous_id|anon_id', r'[A-Za-z0-9_\-]{8,64}'),
    "mac_address": wrap_keywords(r'mac_address|mac', r'(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}'),
    "idfa": wrap_keywords(r'idfa', r'[A-F0-9\-]{36}'),
    "uuid": wrap_keywords(r'uuid', r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'),
    "name": wrap_keywords(
        r'\b(?:user[_\-]?name|account[_\-]?name|profile[_\-]?name|customer[_\-]?name|full[_\-]?name|first[_\-]?name|last[_\-]?name)\b',
        r'\b[A-Z][a-z]{2,}(?: [A-Z][a-z]{2,}){0,2}\b'
    ),
    "accelerometer": wrap_keywords(r'accelerometer[_\-]?[xyz]', r'-?\d+(?:\.\d+)?(?:E[-+]?\d+)?'),
    "password": wrap_keywords(r'password|pass|passwd|pwd|user_password', r'[A-Za-z0-9@#$%^&+=!?.*_-]{4,}'),
    "latitude": wrap_keywords(r'lat|latitude', r'-?\d{1,3}\.\d{4,}'),
    "longitude": wrap_keywords(r'lon|lng|longitude', r'-?\d{1,3}\.\d{4,}'),
    "device_model": wrap_keywords(r'model|device_model', r'(?!name\b|unknown\b)[A-Za-z0-9][A-Za-z0-9 _\-]{1,60}'),
    "manufacturer": wrap_keywords(r'manufacturer', r'(?!name\b|unknown\b)[A-Za-z0-9][A-Za-z0-9 _\-]{1,60}'),
    "brand": wrap_keywords(r'brand', r'(?!name\b|unknown\b)[A-Za-z0-9][A-Za-z0-9 _\-]{1,60}'),
    "hardware": wrap_keywords(r'hardware', r'[A-Za-z0-9_\-]+'),
    "os_version": wrap_keywords(r'\b(?:os_version|android_version|ios_version|osver|os_ver|system_version|sys_version)\b', r'(?:[1-9]\d?(?:\.\d{1,3}){0,2})'),
    "sdk_level": wrap_keywords(r'sdk|api_level', r'(?:[1-9]\d*)'),
    "os_build": wrap_keywords(r'osBuild|os_build', r'[A-Za-z0-9\._\-]+'),
    "application_package_name": wrap_keywords(r'package_name|application_package_name|bundle|package', r'[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+'),
    "app_version": wrap_keywords(r'\b(?:app[_\-]?version|application[_\-]?version|version[_\-]?name)\b', r'[0-9]+(?:\.[0-9]+){0,3}'),
    "build_number": wrap_keywords(r'build|build_number', r'\d+'),
    "application_build": wrap_keywords(r'applicationBuild|app_build', r'\d+'),
    "source_of_install": wrap_keywords(r'source_of_install|install_source|installer', r'[a-zA-Z0-9\._\-]{2,100}'),
    "locale": wrap_keywords(r'locale|language', r'[a-z]{2,3}(?:[_\-][A-Z]{2})?'),
    "country": wrap_keywords(r'country', r'[A-Z]{2}'),
    "mcc_mnc": wrap_keywords(r'mccMnc|mcc|mnc', r'\d{3,6}'),
    "timezone": wrap_keywords(r'timezone|tz|locale_timezone_offset|timezone_offset', r'(?:[A-Z][a-z]+/[A-Z][a-z_]+|[+-]\d{2}:\d{2})'),
    "screen_width": wrap_keywords(r'screen_width|screen_w|width', r'(?:3[2-9]\d|[4-9]\d{2}|1\d{3}|2[0-5]\d{2})'),
    "screen_height": wrap_keywords(r'screen_height|screen_h|height', r'(?:4\d{2}|[5-9]\d{2}|1\d{3}|2[0-5]\d{2})'),
    "screen_density": wrap_keywords(r'density|dpi|screen_density', r'\b(?:120|160|213|240|320|360|480|560|640|xxxhdpi|xxhdpi|xhdpi|hdpi|mdpi)\b'),
    "app_tracking_enabled": wrap_keywords(r'application_tracking_enabled|tracking_enabled|limit_ad_tracking', r'true|false|0|1'),
    "rooted": wrap_keywords(r'rooted|is_rooted|device_rooted', r'true|false'),
    "debuggable": wrap_keywords(r'debuggable|is_debuggable', r'true|false'),
    "uid": wrap_keywords(r'uid|user_id|unique_id|userid|useridentifier|player_id|device_user_id', r'[a-z0-9\-_]{8,64}'),
    "anon_id": wrap_keywords(r'anon_id', r'[A-Za-z0-9_\-]{8,64}'),
    "attribution": wrap_keywords(r'attribution', r'[0-9a-fA-F\-]{8,36}'),
    "application_tracking_enabled": wrap_keywords(r'application_tracking_enabled|app_tracking_enabled|tracking_enabled|limit_ad_tracking', r"\s*'?(true|false|0|1)'?\s*"),
    "advertiser_id_collection_enabled": wrap_keywords(r'advertiser_id_collection_enabled', r"\s*'?(true|false)'?\s*"),
    "advertiser_tracking_enabled": wrap_keywords(r'advertiser_tracking_enabled', r"\s*'?(true|false)'?\s*"),
    "installer_package": wrap_keywords(r'installer_package', r'[a-zA-Z0-9\._\-]+')
}

JUNK_WORDS = {
    "whatsapp", "name" , "offer", "no offer", "add to cart", "cart", "button",
    "screen", "page", "activity", "fragment", "event", "register",
    "variation", "control", "experiment", "test",
    "true", "false", "yes", "no", "null", "undefined",
    "userid", "id", "none", "wallet", "handholding", "top", "loyal", "ceo"
}

ALLOWED_NAME_KEYS = {
    "user_name", "account_name", "profile_name", "customer_name", "full_name", "name"
}

def check_luhn(number: str) -> bool:
    n_digits = len(number)
    n_sum = 0
    is_second = False
    for i in range(n_digits - 1, -1, -1):
        d = ord(number[i]) - ord('0')
        if is_second:
            d *= 2
        n_sum += d // 10
        n_sum += d % 10
        is_second = not is_second
    return n_sum % 10 == 0

def get_card_type(card_number):
    card_types = {
        "Visa": r"(?<!\.)\b4[0-9]{12}(?:[0-9]{3})?\b(?!\.)",
        "MasterCard": r"(?<!\.)\b5[1-5][0-9]{14}\b(?!\.)",
        "American Express": r"(?<!\.)\b3[47][0-9]{13}\b(?!\.)",
        "Discover": r"(?<!\.)\b6(?:011|5[0-9]{2})[0-9]{12}\b(?!\.)",
        "JCB": r"(?<!\.)\b(?:2131|1800|35\d{3})\d{11}\b(?!\.)",
        "Diners Club": r"(?<!\.)\b3(?:0[0-5]|[68][0-9])[0-9]{11}\b(?!\.)",
        "Maestro": r"(?<!\.)\b(5018|5020|5038|56|57|58|6304|6759|676[1-3])\d{8,15}\b(?!\.)",
        "Verve": r"(?<!\.)\b(506[01]|507[89]|6500)\d{12,15}\b(?!\.)"
    }
    for card_type, pattern in card_types.items():
        if re.match(pattern, card_number):
            return card_type
    return "Unknown"

def detect_imei_from_keyval(key, val_str):
    imei_regex = r'\b\d{15}\b'
    key_match = re.search(r'(?i)\b(imei|imeei|imeid|imei[_\-\.]?(md5|sha1|hash))\b', key)
    valid = set()
    invalid = set()
    if key_match:
        candidates = re.findall(imei_regex, val_str)
        for num in candidates:
            if check_luhn(num):
                valid.add(num)
            else:
                invalid.add(num)
    return valid, invalid

class SDKSniffer:
    def __init__(self):
        self.sdk_data = []
        self.domain_counter = {}

    def load(self, loader):
        self.clear_log()

    def done(self):
        self.clear_log()

    def clear_log(self):
        try:
            with open(LOG_FILE, "w") as f:
                json.dump([], f)
            self.sdk_data = []
            ctx.log.info("Cleared SDK logs.")
        except Exception as e:
            ctx.log.warn(f"Failed to clear log: {e}")

    def request(self, flow: http.HTTPFlow):
        domain = flow.request.host
        self.domain_counter[domain] = self.domain_counter.get(domain, 0) + 1
        ctx.log.info(f"[REQ] {flow.request.method} {flow.request.pretty_url}")

        data_sent = {}


        if flow.request.query:
            try:
                query_dict = dict(flow.request.query)
                ctx.log.info(f"Parsing query params: {list(query_dict.keys())}")
                data_sent.update(self.detect_pii(query_dict))
            except Exception as e:
                ctx.log.warn(f"Query parse error: {e}")


        try:
            raw_bytes = flow.request.get_content()
            content_encoding = flow.request.headers.get("content-encoding", "").lower()
            if "gzip" in content_encoding and raw_bytes[:2] == b'\x1f\x8b':
                body_text = gzip.decompress(raw_bytes).decode("utf-8", errors="replace")
                ctx.log.info("Decompressed GZIP body")
            else:
                body_text = raw_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            ctx.log.warn(f"Body decode error: {e}")
            body_text = ""

        content_type = flow.request.headers.get("content-type", "").lower()


        is_graphql = False
        url = flow.request.pretty_url.lower()
        if "/graphql" in url or url.endswith(".graphql.json") or "graphql" in content_type:
            is_graphql = True

        if is_graphql and body_text.strip():
            ctx.log.info("GraphQL request detected, attempting to parse JSON wrapper")
            try:
                parsed = json.loads(body_text)

                variables = parsed.get("variables", {})
                query_text = parsed.get("query", "")

                if isinstance(variables, dict) and variables:
                    ctx.log.info(f"Scanning GraphQL variables keys: {list(variables.keys())}")
                    data_sent.update(self.detect_pii(variables))

                if query_text:

                    literals = re.findall(r'\"([^"]{2,200})\"', query_text)
                    if literals:
                        ctx.log.info(f"Found {len(literals)} literals in GraphQL query, scanning them")
                        # turn into a simple dict to pass to detect_pii
                        data_sent.update(self.detect_pii({"graphql_literals": literals}))

                data_sent.update(self.detect_pii(parsed))
            except Exception as e:
                ctx.log.warn(f"GraphQL JSON parse error: {e}")

                data_sent.update(self.detect_pii({"raw_body": body_text}))


        elif flow.request.method in ("POST", "PUT") and body_text.strip():
            try:
                if len(body_text) > 1_000_000:
                    ctx.log.info("Large body, scanning truncated")
                    data_sent.update(self.detect_pii({"raw_body": body_text[:1000]}))
                else:
                    parsed_body = None
                    try:
                        parsed_body = json.loads(body_text)
                        ctx.log.info("Parsed body as JSON")
                    except Exception:
                        parsed_body = None

                    if parsed_body is not None:
                        data_sent.update(self.detect_pii(parsed_body))
                    elif "x-www-form-urlencoded" in content_type:
                        try:
                            form_dict = dict(flow.request.urlencoded_form)
                            ctx.log.info(f"Parsed form fields: {list(form_dict.keys())}")
                            data_sent.update(self.detect_pii(form_dict))
                        except Exception as e:
                            ctx.log.warn(f"Form parse error: {e}")
                            data_sent.update(self.detect_pii({"raw_body": body_text}))
                    elif "multipart" in content_type:
                        try:

                            form_dict = dict(flow.request.multipart_form.items())
                            ctx.log.info("Parsed multipart form")
                            data_sent.update(self.detect_pii(form_dict))
                        except Exception as e:
                            ctx.log.warn(f"Multipart parse error: {e}")
                            data_sent.update(self.detect_pii({"raw_body": body_text}))
                    else:
                        ctx.log.info("Treating as raw body")
                        data_sent.update(self.detect_pii({"raw_body": body_text}))
            except Exception as e:
                ctx.log.warn(f"Body parse error: {e}")
                data_sent.update(self.detect_pii({"raw_body": body_text}))


        if not data_sent:
            ctx.log.info("No PII found in this request")
            return

        clean_data = {k: sorted(list(v)) for k, v in data_sent.items()}

        app_info = {
            "App Domain": domain,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Data Sent": clean_data,
            "Request URL": flow.request.pretty_url
        }

        duplicate_found = False
        for existing in self.sdk_data:
            if existing["App Domain"] == domain and existing["Data Sent"] == clean_data:
                duplicate_found = True
                ctx.log.info("Duplicate entry, skipping")
                break

        if not duplicate_found:
            ctx.log.info(f"[+] PII Detected: {clean_data}")
            self.sdk_data.append(app_info)
            self.write_log()

    def detect_pii(self, parsed, parent_key=""):
        result = {}
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                full_key = f"{parent_key}.{key}" if parent_key else key
                if isinstance(value, (dict, list)):
                    nested_result = self.detect_pii(value, full_key)
                    for k, v in nested_result.items():
                        result.setdefault(k, set()).update(v)
                    continue

                val_str = str(value).strip()
                if not val_str or val_str.lower() in JUNK_WORDS:
                    continue

                if val_str.startswith("{") and val_str.endswith("}"):
                    try:
                        nested_json = json.loads(val_str)
                        nested_result = self.detect_pii(nested_json, full_key)
                        for k, v in nested_result.items():
                            result.setdefault(k, set()).update(v)
                        continue
                    except Exception:
                        pass

                valid_imeis, invalid_imeis = detect_imei_from_keyval(key, val_str)
                if valid_imeis:
                    result.setdefault("imei", set()).update(valid_imeis)
                if invalid_imeis:
                    result.setdefault("imei_false_positive", set()).update(invalid_imeis)

                for pii_type, regex in patterns.items():
                    match = re.search(regex, f"{key}:{val_str}")
                    if match:
                        candidate = match.group(1) if match.lastindex else val_str

                        if pii_type == "name" and key.lower() not in ALLOWED_NAME_KEYS and len(candidate) < 2:
                            continue
                        result.setdefault(pii_type, set()).add(candidate)

                cc_candidates = re.findall(r'(?<!\.)\b\d{13,19}\b(?!\.\d)', val_str)
                for num in cc_candidates:
                    if num in result.get("imei", set()):
                        continue
                    if check_luhn(num):
                        card_type = get_card_type(num)
                        if card_type != "Unknown":
                            result.setdefault("credit_card", set()).add(f"{num} ({card_type})")

        elif isinstance(parsed, list):
            for item in parsed:
                nested_result = self.detect_pii(item, parent_key)
                for k, v in nested_result.items():
                    result.setdefault(k, set()).update(v)

        return result

    def write_log(self):
        try:
            with open(LOG_FILE, "w") as f:
                json.dump(self.sdk_data, f, indent=2)
            ctx.log.info("Updated sdk_logs.json")
        except Exception as e:
            ctx.log.warn(f"Failed to write log: {e}")

addons = [SDKSniffer()]