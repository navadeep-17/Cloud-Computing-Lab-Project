# Cloud-Based File Upload and Retrieval System

A Cloud Computing lab project that simulates a centralized cloud-storage service using a Flask web application and a server-side local storage directory.

## Problem Statement

Develop a Cloud-Based File Upload and Retrieval System that allows users to upload, list, and download files from a centralized local directory simulating cloud storage.

## Project Status

- **Phase 1 — Core storage workflow:** Complete
- **Phase 2 — Enhanced dashboard and file management:** Complete
- **Phase 3 — Users, database metadata, folders and activity history:** Planned
- **Phase 4 — Real cloud-object storage and deployment:** Planned

See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for the phased roadmap.

## Features

### Phase 1

- Upload files through a browser
- Store files in a centralized `uploads/` directory
- List all stored files
- Download files
- Delete files
- Duplicate filename handling
- Secure filename sanitization
- 25 MB per-file upload limit
- Responsive dashboard
- JSON file-list API
- Health endpoint
- Automated backend tests

### Phase 2

- Upload progress indicator using `XMLHttpRequest` upload progress events
- Client-side upload-size validation
- Search by filename
- Filter by file category
- Sort by name, size, and modified time
- Rich file metadata
- File categories and improved file-type indicators
- Safe inline previews for supported images, PDFs, text, JSON, CSV, and Markdown
- File details modal
- Simulated **250 MB cloud-storage capacity**
- Storage-used, available-space, and percentage visualization
- Server-side quota enforcement
- Expanded automated tests for preview and storage behavior

## Architecture

```text
┌─────────────────────────────┐
│       User / Browser        │
│ HTML + CSS + JavaScript UI  │
└──────────────┬──────────────┘
               │ HTTP
               │ upload / list / preview / download
               ▼
┌─────────────────────────────┐
│       Flask Web Service     │
│                             │
│  Validation                 │
│  Metadata                   │
│  Storage quota              │
│  File-management routes     │
└──────────────┬──────────────┘
               │ File I/O
               ▼
┌─────────────────────────────┐
│ Centralized Local Storage   │
│          uploads/           │
└─────────────────────────────┘
```

The `uploads/` directory acts as the centralized storage layer. Users never need to access that directory directly; they interact with the storage through the Flask service over HTTP, which simulates the basic architecture of a cloud file-storage application.

## Tech Stack

- Python 3.10+
- Flask
- Werkzeug
- HTML5
- CSS3
- Vanilla JavaScript
- Pytest

## Project Structure

```text
Cloud-Computing-Lab-Project/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── docs/
│   └── IMPLEMENTATION_PLAN.md
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── script.js
├── uploads/
│   └── .gitkeep
└── tests/
    └── test_app.py
```

## Run Locally

```bash
git clone https://github.com/navadeep-17/Cloud-Computing-Lab-Project.git
cd Cloud-Computing-Lab-Project
python -m venv .venv
```

Activate the virtual environment.

### Windows

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Run Tests

```bash
pytest
```

## Main Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Dashboard and stored-file list |
| POST | `/upload` | Upload a file |
| GET | `/preview/<filename>` | Preview a supported file inline |
| GET | `/download/<filename>` | Download a stored file |
| POST | `/delete/<filename>` | Delete a stored file |
| GET | `/api/files` | Return file metadata and storage summary as JSON |
| GET | `/health` | Service health check |

## Preview Support

Inline previews are intentionally restricted to a safe subset of file types:

- Images: JPG, JPEG, PNG, GIF, BMP, WEBP
- Documents: PDF, TXT, Markdown
- Data/text: CSV, JSON

Other file types can still be stored and downloaded but are not rendered inline.

## Simulated Storage Capacity

The application currently simulates a **250 MB centralized cloud-storage allocation**. The dashboard shows:

- Total storage used
- Remaining storage
- Percentage consumed
- Total stored-file count

The backend rejects a new upload when it would exceed the simulated capacity.

## Cloud Computing Concepts Demonstrated

- Centralized storage
- Client-server architecture
- HTTP-based resource access
- Storage abstraction through service endpoints
- Upload and retrieval on demand
- Resource-capacity management
- Metadata-driven file management
- Health monitoring
- Separation between client UI, service layer, and storage layer

## Future Cloud Extension

The local storage implementation is deliberately isolated behind Flask routes. In a later phase, the storage layer can be replaced with a real object-storage service such as:

- Amazon S3
- Azure Blob Storage
- Google Cloud Storage

The browser workflow can remain nearly identical while the backend changes from local filesystem operations to cloud-object-storage API calls.
