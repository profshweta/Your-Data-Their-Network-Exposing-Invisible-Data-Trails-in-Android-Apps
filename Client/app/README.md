AppClient — Android Uploader Client

This project is a simple, dedicated Android application designed to serve as a client for the SDK Leak Detection Dashboard (specifically interacting with the main.py Flask server running on port 5000).

It allows a user on a mobile device to remotely submit application details and upload APK files for analysis, and then fetch the resulting PDF report directly to the device.

Features

App Detail Submission: Send the App Name and App Link to the server.

APK File Upload: Select and upload a local APK file to the server's analysis endpoint.

Report Download: Fetch the final generated PDF report from the server and automatically open it on the device using FileProvider.

Clear Server Interaction: Designed to work with the Flask endpoint http://<SERVER_IP>:5000/submit and http://<SERVER_IP>:5000/get_pdf.

Important: Server Configuration

You must modify the hardcoded server IP address in the source code before compiling and running the app.

Open MainActivity.kt and change the following variables to match the IP address of the machine running your Flask server (main.py):

private val serverUrl = "[http://0.0.0.0:5000/submit](http://0.0.0.0:5000/submit)"
private val pdfUrl = "[http://0.0.0.0:5000/get_pdf](http://0.0.0.0:5000/get_pdf)"

// **ACTION REQUIRED:** Replace 0.0.0.0 with your actual machine IP on the same local network.


Android Project Setup (Quick Checklist)

This project requires standard Android development tools (Android Studio) and relies on several configuration files and a networking library.

1. Networking Dependency

Ensure the OkHttp library is included in your app/build.gradle file:

implementation "com.squareup.okhttp3:okhttp:4.11.0"


2. Manifest and Permissions (AndroidManifest.xml)

The manifest defines the app's core components and permissions.

Permission

Purpose

Notes

INTERNET

Required for all HTTP communication with the server.



READ_EXTERNAL_STORAGE

Required for selecting and reading the APK file from storage.

Runtime permission handling is recommended for older Android versions.

WRITE_EXTERNAL_STORAGE

Used for saving the downloaded PDF report.



The manifest also registers FileProvider (for opening downloaded files) and references the network security config.

3. FileProvider Configuration (res/xml/file_paths.xml)

This file is crucial for the app to share the downloaded PDF report safely with the operating system for viewing.

<?xml version="1.0" encoding="utf-8"?>
<paths xmlns:android="[http://schemas.android.com/apk/res/android](http://schemas.android.com/apk/res/android)">
    <external-files-path name="external_files" path="." />
    <cache-path name="cache" path="." />
</paths>


4. Network Security Configuration (res/xml/network_security_config.xml)

Since the server uses local HTTP (not HTTPS), this configuration is necessary to allow non-encrypted (cleartext) traffic, especially for debugging/local testing.

<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
  <base-config cleartextTrafficPermitted="true" />
</network-security-config>


5. Build and Run

Open the project in Android Studio.

Review minSdk and targetSdk settings in your build.gradle.

Ensure your Flask server (main.py) is running on your PC and listening on the IP configured in Step 1.

Install and run the Android app on a physical device or emulator that is connected to the same local Wi-Fi network as your server.

How to Use the App

Once the app is running and the server is active:

Enter an app name in the corresponding field, then tap Send App Name.

Enter an app link (e.g., Google Play link), then tap Send App Link.

Tap Select APK and use the system file picker (ACTION_GET_CONTENT) to choose an .apk file from your device storage.

Tap Upload APK to send the selected file to the Flask server (/submit endpoint).

After the server completes the analysis, tap Fetch PDF to download the report from the server (/get_pdf endpoint). The app will save the file to its external files directory and automatically open it using the system's default PDF viewer.