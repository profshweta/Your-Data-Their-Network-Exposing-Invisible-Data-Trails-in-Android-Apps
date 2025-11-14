🔬 Data Leak Detection and server Dashboard

A powerful, Flask-based web dashboard designed to detect, analyze and report data leaks within Android apps. It works in real-time using mitmproxy to observe network traffic and calculate risk scores from detected leaks, manifest analysis, and obfuscation results.
It also includes a built-in Server Dashboard, which receives app details and APK files from the Android client and sends final PDF reports back to the device, making the full workflow smooth and automatic.

✨ Features

Real-Time Leak Detection: Captures and logs outbound network traffic and identified data leaks (domain, timestamp, specific data fields).

Risk Scoring: Provides unified risk scores based on three vectors:

Network Leaks (Real-time)

Manifest Analysis (Static)

Obfuscation Detection (Static)

Comprehensive Reporting: Exports findings as standard JSON/CSV logs or formatted PDF reports.

Manifest Analysis: Analyzes uploaded APKs using androguard to identify high-risk permissions and vulnerabilities.

Obfuscation Integration: Merges pre-processed obfuscation reports to calculate the obfuscation risk score.

🛠️ Project Created By

Shubhangi Yadav

💻 Tools & Dependencies

This project requires a robust Python environment and specific libraries for web development, network analysis, and reporting.
This project needs a Python environment and several libraries for the dashboard, network sniffing, and report generation.

Python 3.8+
Primary development language
Check version: python --version

Flask
Runs the web dashboard interface
Install → pip install flask

mitmproxy
Captures live network traffic for leak detection
Install → pip install mitmproxy

androguard
Reads APK files and analyzes the manifest
Install → pip install androguard

reportlab
Creates detailed PDF reports
Install → pip install reportlab

PyPDF2
Edits, merges, and reads PDF files
Install → pip install PyPDF2

werkzeug
Provides server utilities used inside Flask
Install → pip install werkzeug

json, re, gzip
Built-in Python modules used for parsing and processing
No installation needed
🚀 Setup & Installation

1. Cloning and Environment Setup

Start by cloning the project and setting up a dedicated Python virtual environment (recommended).

Clone the repository (if applicable)
git clone <repository-url>
cd sdk-leak-dashboard

 Create a virtual environment
python -m venv venv

Activate the virtual environment
Windows
venv\Scripts\activate



2. Install Dependencies

Install all required Python packages:

pip install flask mitmproxy reportlab PyPDF2 werkzeug androguard


🏃 Running the Project

The project requires at least two concurrent processes: the Network Sniffer (mitmproxy) and the Web Dashboard (Flask).

Step A: Start the Real-time Leak Sniffer

Run mitmproxy using your custom Python addon (sdk_sniffer.py). This captures all network traffic and writes/updates the findings to sdk_logs.json.

Open your first terminal window (with the virtual environment active):

mitmproxy -s sdk_sniffer.py


(Ensure your Android device/emulator is configured to use the proxy running on the host machine.)

Step B: Start the Analysis Dashboard

Open your second terminal window (with the virtual environment active) and start the main Flask application:

python app.py


Step C: Access the Dashboard

Open your browser and navigate to the default analysis port:

[http://127.0.0.1:5050/](http://127.0.0.1:5050/)


The main page will immediately display real-time leaks (domain, data sent, timestamp) captured by mitmproxy.

📁📁 Server Dashboard :- Client Reporting and Uploader 

The main.py file runs , dashboard (the Uploader) that streamlines the workflow, especially for generating and sending client reports.

IP Address Configuration for main.py

The Android client and the main.py server communicate directly over your local network. 
Run the Uploader Dashboard

Open your third terminal window (with the virtual environment active) and run the Uploader:

python main.py



Access the Uploader in your browser:




Uploader Functionality

File Upload: Use this dashboard to upload necessary files (like APKs for manifest analysis).

Report Delivery: Provides features to Save and send reports to client (including showing the client alias in the UI).

PDF Generation: Use the Send PDF / download features for final report delivery.

Windows Auto-Start: On Windows systems, the uploader page includes an "Open Analysis Dashboard" button that automatically executes python app.py for convenience (start cmd /c python app.py).

📊 Static Analysis Components

To get a complete risk score, you must process and integrate static analysis results:

1. Manifest Risk Score(permission based)

Access the Analyze APK Manifest section on the main dashboard (/manifest route) or use the Uploader to Upload the target APK file.

The system uses androguard to analyze permissions and vulnerabilities, generating the Manifest Risk Score.

2. Obfuscation Risk Score

Ensure your obfuscation reports (generated by a separate tool) are placed inside the input/ directory.

Run the merging script to consolidate results:

python merge.py


The merged output will be saved in the output/ directory.

Access the /obfuscation route on the dashboard to upload this merged output and view the Obfuscation Risk Score.

⚡ Quick Commands (Copy-Paste)

For quickly launching the essential parts of the project:

# 1. Run mitmproxy sniffer (captures data to sdk_logs.json)
mitmproxy -s sdk_sniffer.py

# 2. Run main analysis dashboard (port 5050)
python app.py

# 3. Run uploader/reporting  server dashboard (port 5000)
python main.py

# 4. Run obfuscation merge script
python merge.py
