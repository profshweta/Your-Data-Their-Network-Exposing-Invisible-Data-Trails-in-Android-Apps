# sdk_risk.py
import json
import os
import math

LOG_FILE = "sdk_logs.json"

CATEGORY_KEYS = {
    "device_info": {
        "device_model", "manufacturer", "brand", "hardware",
        "os_version", "sdk_level", "os_build",
        "screen_width", "screen_height", "screen_density",
        "rooted", "debuggable"
    },

    "app_info": {
        "application_package_name", "app_version", "build_number",
        "application_build", "source_of_install", "installer_package",
        "app_tracking_enabled", "application_tracking_enabled",
        "advertiser_id_collection_enabled", "advertiser_tracking_enabled"

    },

    "sensor_info": {
        "accelerometer"
    },

    "unique_ids": {
        "android_id", "advertiser_id", "anonymous_id", "mac_address", "idfa", "uuid", "uid", "attribution"
    },

    "personal_info": {
        "phone", "otp", "pincode", "address", "city", "email", "number",
        "dob", "gender", "name", "password", "credit_card",
        "latitude", "longitude", "locale", "country", "timezone"
    }
}


CATEGORY_WEIGHTS = {
    "device_info": 0.10,
    "app_info": 0.25,
    "sensor_info": 0.05,
    "unique_ids": 0.20,
    "personal_info": 0.40
}

def load_logs(path=LOG_FILE):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def classify_key(key):
    k = key.lower().strip()
    for cat, keys in CATEGORY_KEYS.items():
        if k in keys:
            return cat
    return None

def tally_categories(logs):

    counts = {c: 0 for c in CATEGORY_KEYS.keys()}
    for entry in logs:
        data = entry.get("Data Sent", {})
        if isinstance(data, dict):
            for key, val in data.items():
                cat = classify_key(key)
                if cat:
                    counts[cat] += 1
        else:
            s = str(data).lower()
            for cat, keys in CATEGORY_KEYS.items():
                for k in keys:
                    if k in s:
                        counts[cat] += 1  # count every match separately
    return counts

def subscore_log_scale(count, max_count):
    if count <= 0 or max_count <= 0:
        return 0.0
    s = (math.log(count + 1) / math.log(max_count + 1)) * 10.0
    return min(10.0, s)

def compute_risk_from_logs(path=LOG_FILE):
    logs = load_logs(path)
    counts = tally_categories(logs)
    max_count = max(counts.values()) if counts else 0

    subs = {c: subscore_log_scale(counts[c], max_count) for c in counts}

    weighted = 0.0
    total_weight = sum(CATEGORY_WEIGHTS.values())
    for c, w in CATEGORY_WEIGHTS.items():
        weighted += (w * subs.get(c, 0.0))

    final_score = (weighted / total_weight) * 10.0
    final_score = round(max(0.0, min(100.0, final_score)), 1)

    details = {}
    for c in counts:
        details[c] = {
            "count": counts[c],
            "subscore": round(subs[c], 2),
            "weight": CATEGORY_WEIGHTS.get(c, 0)
        }

    return final_score, details, len(logs)
