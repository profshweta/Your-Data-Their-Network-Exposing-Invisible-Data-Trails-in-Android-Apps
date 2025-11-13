from flask import Flask, render_template, request, send_file
from androguard.core.apk import APK
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
import math

app = Flask(__name__)

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

PERMISSION_WEIGHTS = {
    "android.permission.INTERNET": 0.10,
    "android.permission.READ_CONTACTS": 0.20,
    "android.permission.ACCESS_FINE_LOCATION": 0.20,
    "android.permission.CAMERA": 0.15,
    "android.permission.RECORD_AUDIO": 0.15,
    "android.permission.READ_SMS": 0.15,
    "android.permission.WRITE_EXTERNAL_STORAGE": 0.10,
    "android.permission.READ_PHONE_STATE": 0.15,
    "android.permission.ACCESS_COARSE_LOCATION": 0.10,
}


def compute_manifest_risk(permissions, vulnerabilities):
    total_weight = sum(PERMISSION_WEIGHTS.values())
    perm_score = sum(PERMISSION_WEIGHTS.get(p, 0.05) for p in permissions)
    perm_score = min(60, (perm_score / total_weight) * 60)
    vuln_score = min(40, len(vulnerabilities) * 10)
    final_score = round(min(100, perm_score + vuln_score), 1)
    return final_score, perm_score, vuln_score


def analyze_manifest(apk_path):
    try:
        apk = APK(apk_path)
        manifest = apk.get_android_manifest_xml()

        app_tag = manifest.find(".//application")
        vulnerabilities = []
        if app_tag is not None and app_tag.get(ANDROID_NS + "debuggable") == "true":
            vulnerabilities.append("Application is debuggable")

        for comp_type, comp_list in [
            ("activity", apk.get_activities()),
            ("service", apk.get_services()),
            ("receiver", apk.get_receivers()),
            ("provider", apk.get_providers())
        ]:
            for comp in comp_list:
                tag = manifest.find(f".//{comp_type}[@{ANDROID_NS}name='{comp}']")
                if tag is not None and tag.get(ANDROID_NS + "exported") == "true":
                    vulnerabilities.append(f"{comp_type.capitalize()} exported: {comp}")

        permissions = apk.get_permissions()
        final_score, perm_score, vuln_score = compute_manifest_risk(permissions, vulnerabilities)

        return {
            "permissions": permissions,
            "vulnerabilities": vulnerabilities,
            "risk_score": final_score,
            "permission_risk": round(perm_score, 1),
            "vulnerability_risk": round(vuln_score, 1)
        }

    except Exception as e:
        return {"error": str(e)}


@app.route("/", methods=["GET", "POST"])
def index():
    report = None
    if request.method == "POST":
        apk_file = request.files["apk_file"]
        if apk_file:
            path = f"temp.apk"
            apk_file.save(path)
            report = analyze_manifest(path)
    return render_template("index.html", report=report)


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


if __name__ == "__main__":
    app.run(debug=True)
