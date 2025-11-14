from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for
import json
import os
import csv
import io
from datetime import datetime
from collections import Counter
from werkzeug.utils import secure_filename
from sdk_risk import compute_risk_from_logs
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


from werkzeug.middleware.dispatcher import DispatcherMiddleware


from obfuscation import app as obf_app

app = Flask(__name__)
LOG_FILE = "sdk_logs.json"


UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"apk"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def load_logs():
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except:
                logs = []
        for item in logs:
            if "Timestamp" not in item:
                item["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return logs


app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/obfuscation': obf_app
})

# ---------------- SDK Dashboard ----------------
@app.route("/")
def index():
    logs = load_logs()
    search = request.args.get("search", "").lower()
    sdk_filter = request.args.get("sdk", "")

    if search:
        logs = [
            d for d in logs
            if search in d['App Domain'].lower()
               or any(search in key.lower() for key in d.get("Data Sent", {}).keys())
        ]

    if sdk_filter and sdk_filter != "All":
        logs = [d for d in logs if d['App Domain'] == sdk_filter]

    sdk_list = sorted(set(d['App Domain'] for d in load_logs()))
    total_requests = len(load_logs())
    sdk_counter = Counter(d['App Domain'] for d in load_logs())
    unique_sdks = len(sdk_counter)

    return render_template(
        "index.html",
        logs=logs,
        sdk_list=sdk_list,
        search=search,
        sdk_filter=sdk_filter,
        total_requests=total_requests,
        unique_sdks=unique_sdks,
        sdk_counter=sdk_counter
    )


@app.route("/obfuscation")
def obfuscation_redirect():

    return redirect("/obfuscation/")

# ---------------- Manifest Analyzer ----------------
@app.route("/manifest", methods=["GET", "POST"])
def manifest_dashboard():
    report = None
    if request.method == "POST":
        if "apk_file" not in request.files:
            return redirect(request.url)
        file = request.files["apk_file"]
        if file.filename == "":
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            from manifest_analyzer import analyze_manifest
            report = analyze_manifest(filepath)

    return render_template("manifest_index.html", report=report)



@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    report_data = request.form.to_dict()
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("APK Manifest Report")

    pdf.drawString(100, 800, "📦 APK Manifest Analyzer Report")
    y = 770

    def write_line(text):
        nonlocal y
        pdf.drawString(60, y, text)
        y -= 20

    write_line(f"Overall Risk Score: {report_data.get('risk_score')}/100")
    write_line(f"Permission Risk: {report_data.get('permission_risk')}/60")
    write_line(f"Vulnerability Risk: {report_data.get('vulnerability_risk')}/40")

    pdf.setFont("Helvetica-Bold", 12)
    y -= 15
    write_line("Permissions:")
    pdf.setFont("Helvetica", 11)
    for p in report_data.get('permissions', '').split(','):
        if y < 80:
            pdf.showPage()
            y = 800
        write_line(f"- {p.strip()}")

    y -= 15
    pdf.setFont("Helvetica-Bold", 12)
    write_line("Vulnerabilities:")
    pdf.setFont("Helvetica", 11)
    for v in report_data.get('vulnerabilities', '').split(','):
        if y < 80:
            pdf.showPage()
            y = 800
        write_line(f"- {v.strip()}")

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="apk_manifest_report.pdf", mimetype="application/pdf")



@app.route("/risk")
def risk_analysis():
    final_score, details, total_logs = compute_risk_from_logs()
    return render_template("risk.html", final_score=final_score, details=details, total_logs=total_logs)

@app.route("/api/logs")
def api_logs():
    return jsonify(load_logs())

@app.route("/download")
def download():
    return send_file(LOG_FILE, as_attachment=True)

@app.route("/export")
def export():
    export_file = "sdk_export.csv"
    logs = load_logs()
    with open(export_file, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["App Domain", "Data Sent", "Timestamp"])
        for item in logs:
            writer.writerow([
                item.get("App Domain", ""),
                ", ".join([f"{k}: {v}" for k, v in item.get("Data Sent", {}).items()]),
                item.get("Timestamp", "")
            ])
    return send_file(export_file, as_attachment=True)

if __name__ == "__main__":
    # run main app on port 5050
    app.run(debug=True, port=5050)
