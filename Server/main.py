from flask import Flask, request, render_template, send_from_directory, send_file
import os
from collections import defaultdict
import urllib.parse

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024    # 500MB uploads
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client_data = defaultdict(list)
client_alias = {}
client_counter = 1

last_uploaded_pdf = None


def get_client_label():
    global client_counter
    ip = request.remote_addr
    if ip not in client_alias:
        client_alias[ip] = f"Client {client_counter}"
        print(f"🆕 Connected: {client_alias[ip]}")
        client_counter += 1
    return client_alias[ip]


@app.route("/")
def dashboard():
    files = os.listdir(UPLOAD_FOLDER)
    all_data = []

    for cid, items in client_data.items():
        for item in items:
            all_data.append({
                "client": cid,
                "type": item["type"],
                "value": item["value"]
            })

    clients = list(client_data.keys())
    return render_template("dashboard.html", data=all_data, files=files, clients=clients)


@app.route("/submit", methods=["POST"])
def submit_data():
    cid = get_client_label()


    if 'app_name' in request.form:
        name = request.form['app_name']
        print(f"{cid} → App Name: {name}")
        client_data[cid].append({"type": "App Name", "value": name})
        return "OK", 200


    if 'app_link' in request.form:
        link = request.form['app_link']
        print(f"{cid} → App Link: {link}")
        client_data[cid].append({"type": "App Link", "value": link})
        return "OK", 200

    #
    if 'apk_file' in request.files:
        file = request.files['apk_file']
        if file.filename == "":
            return "No APK file", 400

        safe_filename = file.filename.replace(" ", "_")
        save_path = os.path.join(UPLOAD_FOLDER, safe_filename)

        try:

            with open(save_path, "wb") as f:
                chunk = file.stream.read(1024 * 1024)
                while chunk:
                    f.write(chunk)
                    chunk = file.stream.read(1024 * 1024)

            print(f"{cid} → APK Saved: {safe_filename}")
            client_data[cid].append({"type": "APK File", "value": safe_filename})
            return "OK", 200

        except Exception as e:
            print(f"{cid} → Save error: {e}")
            return "Save error", 500

    return "No valid data", 400


@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    global last_uploaded_pdf

    if 'pdf_file' not in request.files:
        return "No file", 400

    file = request.files['pdf_file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)

    file.save(filepath)
    last_uploaded_pdf = file.filename

    print(f"📄 PDF uploaded: {file.filename}")
    return "OK", 200


@app.route("/send_pdf/<client>")
def send_pdf_to_client(client):
    global last_uploaded_pdf
    client = urllib.parse.unquote(client)

    if not last_uploaded_pdf:
        return "No PDF", 404

    if client not in client_data:
        return "Unknown client", 404

    client_data[client].append({"type": "PDF Ready", "value": last_uploaded_pdf})
    print(f"📄 PDF ready for {client}")
    return "OK", 200


@app.route("/get_pdf")
def get_pdf():
    global last_uploaded_pdf

    if not last_uploaded_pdf:
        return "No PDF", 404

    pdf_path = os.path.join(UPLOAD_FOLDER, last_uploaded_pdf)
    return send_file(pdf_path, as_attachment=True)


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route("/go_to_analysis")
def go_to_analysis():
    os.system("start cmd /c python app.py")
    return '<meta http-equiv="refresh" content="2; url=http://127.0.0.1:5050/">'


if __name__ == "__main__":
    # 🚀 FAST MODE (NO DEBUG)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
