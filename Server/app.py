from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for
import json
import os
import csv
import io
from datetime import datetime
from collections import Counter
from werkzeug.utils import secure_filename


from sdk_risk import RiskAnalyzer, load_logs
from manifest_analyzer import analyze_manifest

app = Flask(__name__)


LOG_FILE = "sdk_logs.json"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"apk"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def index():
    
    report = None

    
    if request.method == "POST":
        file = request.files.get("apk_file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            try:
                data = analyze_manifest(filepath)
                report = {
                    "permissions": data.get('permissions', []),
                    "vulnerabilities": data.get('vulnerabilities', []),
                    "filename": filename
                }
            except Exception as e:
                print(f"Manifest Analysis Error: {e}")

    
    logs = load_logs()
    search = request.args.get("search", "").lower()
    sdk_filter = request.args.get("sdk", "All")

    
    if search:
        logs = [
            d for d in logs
            if search in d.get('App Domain', '').lower()
            or any(search in str(v).lower() for v in d.get("Data Sent", {}).values())
        ]

    if sdk_filter != "All":
        logs = [d for d in logs if d.get('App Domain') == sdk_filter]

    
    all_logs = load_logs()
    sdk_list = sorted(set(d.get('App Domain', 'Unknown') for d in all_logs))
    total_requests = len(all_logs)
    unique_sdks = len(sdk_list)
    sdk_counter = Counter(d.get('App Domain', 'Unknown') for d in all_logs)

    
    return render_template(
        "index.html",
        logs=logs,
        sdk_list=sdk_list,
        total_requests=total_requests,
        unique_sdks=unique_sdks,
        sdk_counter=sdk_counter,
        report=report
    )



@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("apk_file")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        try:
            data = analyze_manifest(filepath)
            report = {
                "permissions": data.get('permissions', []),
                "vulnerabilities": data.get('vulnerabilities', []),
                "filename": filename
            }
            return render_template(
                "analyze.html",
                report=report,
                logs=load_logs(),
                sdk_list=[],
                total_requests=0,
                unique_sdks=0
            )
        except Exception as e:
            return f"Error: {e}"
    return redirect(url_for('index'))



@app.route("/risk", methods=["GET", "POST"])
def risk_analysis():
    analyzer = RiskAnalyzer()
    dynamic_logs = load_logs()
    dynamic_details = analyzer.get_dynamic_details(dynamic_logs)

    report = {"dynamic": dynamic_details, "static": None, "final": None}

    if request.method == "POST":
        file = request.files.get("apk_file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            try:
                manifest_data = analyze_manifest(filepath)
                static_details = analyzer.get_static_details(
                    manifest_data.get('permissions', []),
                    manifest_data.get('vulnerabilities', [])
                )
               
                final_score, classification, method = analyzer.get_final_assessment(
                    dynamic_details['score'],
                    static_details['score']
                )
                report["static"] = static_details
                report["final"] = {
                    "score": final_score,
                    "status": classification,
                    "method": method       
                }
            except Exception as e:
                print(f"Risk Error: {e}")

    return render_template("risk.html", report=report)



@app.route("/api/logs")
def api_logs():
    return jsonify(load_logs())


@app.route("/download")
def download():
    if os.path.exists(LOG_FILE):
        return send_file(LOG_FILE, as_attachment=True)
    return "No logs found", 404


@app.route("/export")
def export_csv():
    logs = load_logs()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["App Domain", "Data Sent", "Timestamp"])
    for item in logs:
        data_str = "; ".join([f"{k}: {v}" for k, v in item.get("Data Sent", {}).items()])
        cw.writerow([item.get("App Domain", ""), data_str, item.get("Timestamp", "")])
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="leak_report.csv")


if __name__ == "__main__":
    app.run(debug=True, port=5050)
