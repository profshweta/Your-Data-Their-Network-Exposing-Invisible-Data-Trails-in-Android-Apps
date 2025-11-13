from flask import Flask, render_template, request, send_file
from PyPDF2 import PdfReader
import os
import math
import io
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

TECHNIQUES = [
    "string encryption",
    "identifier cleaner",
    "control flow",
    "dead code",
    "inline expansion",
    "opaque predicates",
    "control flow flattening",
    "instruction substitution",
    "dynamic code loading",
    "junk code",
    "api redirection",
    "mixed language obfuscation",
    "identifier obfuscation"
]

WEIGHTS = {
    "string encryption": 0.18,
    "identifier cleaner": 0.05,
    "identifier obfuscation": 0.05,
    "control flow": 0.06,
    "dead code": 0.06,
    "inline expansion": 0.04,
    "opaque predicates": 0.10,
    "control flow flattening": 0.08,
    "instruction substitution": 0.06,
    "dynamic code loading": 0.10,
    "junk code": 0.05,
    "api redirection": 0.07,
    "mixed language obfuscation": 0.10
}


def extract_text_from_pdf(path):
    reader = PdfReader(path)
    text = ""
    for p in reader.pages:
        try:
            text += p.extract_text() or ""
        except:
            pass
    return text.lower()

def parse_sections(text):
    counts = {t: 0 for t in TECHNIQUES}
    current = None
    lines = [l.strip() for l in text.splitlines()]
    for line in lines:
        if not line:
            continue
        if line.startswith("=") and line.endswith("="):
            title = line.replace("=", "").strip().lower()
            matched = None
            for t in TECHNIQUES:
                if t in title:
                    matched = t
                    break
            current = matched
            continue
        low = line.lower()
        for t in TECHNIQUES:
            if low == t or (len(low) < 60 and t in low and low.endswith(":")):
                current = t
                break
        if current and len(line) > 2:
            if "no cases detected" in low or "no cases" in low:
                continue
            if line.lower().endswith(".java:") or line.startswith("error") or line.startswith("traceback"):
                continue
            if "->" in line or ":" in line:
                counts[current] += 1
    return counts

def subscore_log_scale(count, max_count):
    if count <= 0 or max_count <= 0:
        return 0.0
    s = (math.log(count + 1) / math.log(max_count + 1)) * 10.0
    return round(min(10.0, s), 2)

def compute_risk_wsm(counts):
    total_weight = sum(WEIGHTS.values())
    weighted_sum = 0.0
    details = {}
    max_count = max(counts.values()) if counts else 0
    for tech, count in counts.items():
        weight = WEIGHTS.get(tech, 0.0)
        sub = subscore_log_scale(count, max_count)
        weighted_sum += weight * sub
        tech_contribution = (weight * sub / total_weight) * 10.0
        details[tech] = {
            "count": count,
            "subscore": sub,
            "weight": weight,
            "tech_score": round(tech_contribution, 2)
        }
    final_score = (weighted_sum / total_weight) * 10.0
    final_score = round(max(0.0, min(100.0, final_score)), 1)
    return final_score, details

def label_from_score(score):
    if score <= 20:
        return "Benign / Low risk"
    elif score <= 50:
        return "Suspicious"
    elif score <= 75:
        return "Risky / Likely malicious"
    return "Highly malicious / Obfuscated"


os.makedirs("uploads1", exist_ok=True)
LAST_REPORT_PATH = os.path.join("uploads1", "last_report.json")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "pdf" not in request.files:
            return render_template("index1.html", error="No file uploaded.")
        file = request.files["pdf"]
        if file.filename == "":
            return render_template("index1.html", error="No file selected.")
        filename = file.filename
        path = os.path.join("uploads1", filename)
        file.save(path)

        text = extract_text_from_pdf(path)
        counts = parse_sections(text)

        score, details = compute_risk_wsm(counts)
        label = label_from_score(score)
        top = sorted(details.items(), key=lambda x: x[1]["tech_score"], reverse=True)[:10]
        malicious_percent = score

        # save a small report so download route can use it
        report_to_save = {
            "score": score,
            "malicious_percent": malicious_percent,
            "label": label,
            "top": [(t, details[t]) for t, _ in top]  # list of (tech, info)
        }
        with open(LAST_REPORT_PATH, "w", encoding="utf-8") as fh:
            json.dump(report_to_save, fh)

        return render_template("result.html",
                               score=score,
                               malicious_percent=malicious_percent,
                               label=label,
                               top=[(t, details[t]) for t, _ in top])
    return render_template("index1.html")

@app.route("/download_pdf", methods=["GET"])
def download_pdf():
    # read last saved report
    if not os.path.exists(LAST_REPORT_PATH):
        # no report yet
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.drawString(60, 800, "No report available. Please run analysis first.")
        pdf.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="pdf_risk_report.pdf", mimetype="application/pdf")

    with open(LAST_REPORT_PATH, "r", encoding="utf-8") as fh:
        report = json.load(fh)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("PDF Obfuscation Risk Report")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(60, 800, "📄 PDF Obfuscation Risk Report")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(60, 780, f"Score: {report.get('score')}")
    pdf.drawString(60, 760, f"Label: {report.get('label')}")
    pdf.drawString(60, 740, f"Malicious Probability: {report.get('malicious_percent')}%")

    y = 720
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(60, y, "Top contributing techniques:")
    y -= 18
    pdf.setFont("Helvetica", 11)

    top = report.get("top", [])
    for item in top:
        if y < 80:
            pdf.showPage()
            y = 800
        tech = item[0]
        info = item[1]
        pdf.drawString(70, y, f"- {tech}: count={info.get('count',0)}, score={info.get('tech_score',0)}")
        y -= 16

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="pdf_risk_report.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
