package com.example.appclient

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.OpenableColumns
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.io.FileOutputStream
import java.io.IOException

class MainActivity : AppCompatActivity() {

    private val PICK_APK_REQUEST = 1
    private var apkUri: Uri? = null
    private lateinit var selectedFileText: TextView

    //  Change this IP to your Flask server's local IP
    private val serverUrl = "http://0.0.0.0:5000/submit"
    private val pdfUrl = "http://0.0.0.0:5000/get_pdf"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val appNameInput = findViewById<EditText>(R.id.appNameInput)
        val appLinkInput = findViewById<EditText>(R.id.appLinkInput)
        val submitAppName = findViewById<Button>(R.id.submitAppName)
        val submitAppLink = findViewById<Button>(R.id.submitAppLink)
        val selectApk = findViewById<Button>(R.id.selectApk)
        val uploadApk = findViewById<Button>(R.id.uploadApk)
        val fetchPdfBtn = findViewById<Button>(R.id.fetchJsonButton)
        selectedFileText = findViewById(R.id.selectedFileText)


        submitAppName.setOnClickListener {
            val name = appNameInput.text.toString().trim()
            if (name.isNotEmpty()) sendAppName(name)
            else Toast.makeText(this, "Enter app name", Toast.LENGTH_SHORT).show()
        }


        submitAppLink.setOnClickListener {
            val link = appLinkInput.text.toString().trim()
            if (link.isNotEmpty()) sendAppLink(link)
            else Toast.makeText(this, "Enter app link", Toast.LENGTH_SHORT).show()
        }


        selectApk.setOnClickListener {
            val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                type = "application/vnd.android.package-archive"
            }
            startActivityForResult(Intent.createChooser(intent, "Select APK"), PICK_APK_REQUEST)
        }


        uploadApk.setOnClickListener {
            apkUri?.let {
                uploadApkFile(it)
            } ?: Toast.makeText(this, "Select APK first", Toast.LENGTH_SHORT).show()
        }


        fetchPdfBtn.setOnClickListener {
            fetchPdfReport()
        }
    }


    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == PICK_APK_REQUEST && resultCode == Activity.RESULT_OK) {
            apkUri = data?.data
            apkUri?.let {
                selectedFileText.text = "Selected: ${getFileName(it)}"
            }
        }
    }


    private fun sendAppName(name: String) {
        val client = OkHttpClient()
        val formBody = FormBody.Builder()
            .add("app_name", name)
            .build()

        val request = Request.Builder()
            .url(serverUrl)
            .post(formBody)
            .build()

        sendRequest(client, request, "App name sent successfully")
    }


    private fun sendAppLink(link: String) {
        val client = OkHttpClient()
        val formBody = FormBody.Builder()
            .add("app_link", link)
            .build()

        val request = Request.Builder()
            .url(serverUrl)
            .post(formBody)
            .build()

        sendRequest(client, request, "App link sent successfully")
    }


    private fun uploadApkFile(uri: Uri) {
        val fileName = getFileName(uri)
        val file = File(cacheDir, fileName)

        try {
            contentResolver.openInputStream(uri)?.use { input ->
                FileOutputStream(file).use { output ->
                    input.copyTo(output)
                }
            }
        } catch (e: Exception) {
            Toast.makeText(this, "Error reading file: ${e.message}", Toast.LENGTH_SHORT).show()
            return
        }

        val requestBody = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart(
                "apk_file",
                file.name,
                file.asRequestBody("application/octet-stream".toMediaType())
            )
            .build()

        val request = Request.Builder()
            .url(serverUrl)
            .post(requestBody)
            .build()

        sendRequest(OkHttpClient(), request, "APK uploaded successfully")
    }


    private fun sendRequest(client: OkHttpClient, request: Request, successMessage: String) {
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    Toast.makeText(
                        this@MainActivity,
                        "Failed: ${e.message}",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            }

            override fun onResponse(call: Call, response: Response) {
                runOnUiThread {
                    if (response.isSuccessful) {
                        Toast.makeText(
                            this@MainActivity,
                            successMessage,
                            Toast.LENGTH_SHORT
                        ).show()
                    } else {
                        Toast.makeText(
                            this@MainActivity,
                            "Server error: ${response.code}",
                            Toast.LENGTH_SHORT
                        ).show()
                    }
                }
            }
        })
    }


    private fun getFileName(uri: Uri): String {
        var result = "file.apk"
        val cursor = contentResolver.query(uri, null, null, null, null)
        cursor?.use {
            val nameIndex = it.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if (it.moveToFirst() && nameIndex != -1) {
                result = it.getString(nameIndex)
            }
        }
        return result
    }


    private fun fetchPdfReport() {
        val client = OkHttpClient()
        val request = Request.Builder().url(pdfUrl).build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    Toast.makeText(
                        this@MainActivity,
                        "Failed: ${e.message}",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            }

            override fun onResponse(call: Call, response: Response) {
                if (response.isSuccessful) {
                    val pdfBytes = response.body?.bytes()
                    if (pdfBytes != null) {
                        val file = File(getExternalFilesDir(null), "report.pdf")
                        FileOutputStream(file).use { it.write(pdfBytes) }

                        runOnUiThread {
                            Toast.makeText(
                                this@MainActivity,
                                "PDF downloaded successfully!",
                                Toast.LENGTH_SHORT
                            ).show()
                            openPdf(file)
                        }
                    }
                } else {
                    runOnUiThread {
                        Toast.makeText(
                            this@MainActivity,
                            "Server error: ${response.code}",
                            Toast.LENGTH_SHORT
                        ).show()
                    }
                }
            }
        })
    }


    private fun openPdf(file: File) {
        try {
            val uri = FileProvider.getUriForFile(
                this,
                "${packageName}.provider",
                file
            )
            val intent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(uri, "application/pdf")
                flags = Intent.FLAG_ACTIVITY_NO_HISTORY or Intent.FLAG_GRANT_READ_URI_PERMISSION
            }
            startActivity(intent)
        } catch (e: Exception) {
            Toast.makeText(this, "No PDF viewer found!", Toast.LENGTH_SHORT).show()
        }
    }
}
