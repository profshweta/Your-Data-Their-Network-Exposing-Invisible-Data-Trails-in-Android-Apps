from flask import Flask, request, render_template, send_from_directory, send_file
import os
from collections import defaultdict
import urllib.parse

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

client_data = defaultdict(list)
client_alias = {}
client_counter = 1

# store last uploaded PDF name
last_uploaded_pdf = None


def get_client_label():
    global client_counter
    ip = request.remote_addr
    if ip not in client_alias:
        client_alias[ip] = f"Client {client_counter}"
        print(f"🆕 New client connected: {client_alias[ip]} (IP hidden)")
        client_counter += 1
    return client_alias[ip]


@app.route("/")
def dashboard():
    files = os.listdir(UPLOAD_FOLDER)
    all_data = []
    for cid, items in client_data.items():
        for item in items:
            all_data.append({"client": cid, "type": item["type"], "value": item["value"]})

    clients = list(client_data.keys()) if client_data else []
    return render_template("dashboard.html", data=all_data, files=files, clients=clients)


@app.route("/submit", methods=["POST"])
def submit_data():
    cid = get_client_label()

    if 'app_name' in request.form:
        name = request.form['app_name']
        print(f"{cid} → App Name: {name}")
        client_data[cid].append({"type": "App Name", "value": name})
        return "App name received", 200

    elif 'app_link' in request.form:
        link = request.form['app_link']
        print(f"{cid} → App Link: {link}")
        client_data[cid].append({"type": "App Link", "value": link})
        return "App link received", 200

    elif 'apk_file' in request.files:
        file = request.files['apk_file']
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        print(f"{cid} → APK Saved: {filepath}")
        client_data[cid].append({"type": "APK File", "value": file.filename})
        return "APK uploaded", 200

    return "No valid data received", 400


@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    global last_uploaded_pdf

    if 'pdf_file' not in request.files:
        return "No file", 400

    file = request.files['pdf_file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    last_uploaded_pdf = file.filename
    print(f"📄 PDF uploaded: {filepath}")
    return "PDF uploaded successfully!", 200



@app.route("/send_pdf/<client>")
def send_pdf_to_client(client):
    global last_uploaded_pdf
    client = urllib.parse.unquote(client)

    if not last_uploaded_pdf:
        return "No PDF uploaded yet", 404

    if client not in client_data:
        return f"❌ Unknown client: {client}", 404

    print(f" PDF '{last_uploaded_pdf}' marked ready for {client}")
    client_data[client].append({"type": "PDF Ready", "value": last_uploaded_pdf})
    return f"PDF ready for {client}", 200


@app.route("/get_pdf")
def get_pdf():
    global last_uploaded_pdf
    if not last_uploaded_pdf:
        return "No PDF uploaded yet", 404

    pdf_path = os.path.join(UPLOAD_FOLDER, last_uploaded_pdf)
    if not os.path.exists(pdf_path):
        return "PDF file not found", 404

    print(" Android client downloaded the PDF")
    return send_file(pdf_path, as_attachment=True)


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route("/go_to_analysis")
def go_to_analysis():
    os.system("start cmd /c python app.py")
    return '<meta http-equiv="refresh" content="2; url=http://127.0.0.1:5050/">'

if __name__ == "__main__":
    app.run(host="x.x.x.x", port=5000)
