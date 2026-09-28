# Cloud-Based File Upload and Retrieval System

A Cloud Computing lab project that simulates a centralized cloud storage service using a Flask web application and a local server-side storage directory.

## Problem Statement

Develop a Cloud-Based File Upload and Retrieval System that allows users to upload, list, and download files from a centralized local directory simulating cloud storage.

## Current Features

- Upload files through a web interface
- Store files in a centralized `uploads/` directory
- List stored files with metadata
- Download stored files
- Delete files
- Search/filter the displayed file list
- Duplicate filename handling
- Secure filename handling and upload-size validation
- Responsive dashboard UI

## Architecture

```text
User / Browser
      |
      | HTTP
      v
Flask Web Application
      |
      | File operations
      v
Centralized Local Storage
     uploads/
```

The local `uploads/` directory represents the centralized storage layer. Users access files only through the Flask application, which simulates the basic request/response flow of a cloud file-storage service.

## Tech Stack

- Python 3.10+
- Flask
- HTML5
- CSS3
- JavaScript

## Project Structure

```text
Cloud-Computing-Lab-Project/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── script.js
├── uploads/
│   └── .gitkeep
├── tests/
│   └── test_app.py
└── README.md
```

## Run Locally

```bash
git clone https://github.com/navadeep-17/Cloud-Computing-Lab-Project.git
cd Cloud-Computing-Lab-Project
python -m venv .venv
```

Activate the virtual environment.

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies and run the application:

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Main Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Display dashboard and stored files |
| POST | `/upload` | Upload a file |
| GET | `/download/<filename>` | Download a stored file |
| POST | `/delete/<filename>` | Delete a stored file |
| GET | `/api/files` | Return stored-file metadata as JSON |
| GET | `/health` | Health check |

## Cloud Computing Concepts Demonstrated

- Centralized storage
- Client-server architecture
- Resource access over HTTP
- Storage abstraction through application routes
- File retrieval on demand
- Basic service availability through a health endpoint

## Notes

The project intentionally uses a local directory instead of a real cloud object-storage provider so that the lab can demonstrate cloud-storage concepts without requiring paid infrastructure or credentials. A future version can replace the local storage layer with Amazon S3, Azure Blob Storage, or Google Cloud Storage without changing the overall user flow.
