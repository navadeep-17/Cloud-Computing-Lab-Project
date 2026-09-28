# Cloud-Based File Upload and Retrieval System

A Cloud Computing lab project that simulates a centralized cloud-storage service using Flask, SQLite metadata, authenticated users, and isolated server-side file storage.

## Problem Statement

Develop a Cloud-Based File Upload and Retrieval System that allows users to upload, list, and download files from a centralized local directory simulating cloud storage.

## Project Status

- **Phase 1 — Core storage workflow:** Complete
- **Phase 2 — Enhanced dashboard and file management:** Complete
- **Phase 3 — Multi-user application layer:** Complete
- **Phase 4 — Real cloud-object storage and deployment:** Planned

See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for the phased roadmap.

## Phase 3 Features

- User registration, login, and logout
- Session-based authentication
- Password hashing with Werkzeug
- SQLite metadata database
- Per-user physical storage directories
- File ownership and authorization checks
- Persistent file metadata
- Nested logical folders
- Per-user 250 MB simulated cloud quota
- Upload, preview, download, and delete activity history
- Account and folder activity history
- Per-user storage statistics
- Protected JSON APIs
- Cross-user access isolation tests

Phase 1 and Phase 2 functionality is retained, including upload progress, drag-and-drop upload, search, file-type filtering, sorting, file previews, details, quota visualization, duplicate display-name support, and automated testing.

## Phase 3 Architecture

```text
┌──────────────────────────────┐
│        User / Browser        │
│ Login + Cloud Drive UI       │
└───────────────┬──────────────┘
                │ HTTP + session cookie
                ▼
┌──────────────────────────────┐
│       Flask Application      │
│                              │
│ Authentication               │
│ Authorization                │
│ Upload / Preview / Download  │
│ Folder management            │
│ Quota enforcement            │
│ Activity logging             │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌──────────────────┐
│ SQLite DB    │  │ Local Storage    │
│              │  │ uploads/         │
│ users        │  │ ├── user_1/      │
│ files        │  │ ├── user_2/      │
│ folders      │  │ └── ...          │
│ activities   │  │                  │
└──────────────┘  └──────────────────┘
```

The filesystem stores file bytes while SQLite stores identity, ownership, logical folder relationships, metadata, and activity history. File access is performed through database IDs and every protected operation verifies that the signed-in user owns the requested object.

## Tech Stack

- Python 3.10+
- Flask 3
- SQLite (`sqlite3`, Python standard library)
- Werkzeug password hashing
- HTML5
- CSS3
- Vanilla JavaScript
- Pytest
- GitHub Actions

## Project Structure

```text
Cloud-Computing-Lab-Project/
├── app.py
├── auth.py
├── database.py
├── schema.sql
├── pytest.ini
├── requirements.txt
├── README.md
├── .gitignore
├── instance/                  # generated locally, ignored by Git
│   └── cloudvault.db
├── docs/
│   └── IMPLEMENTATION_PLAN.md
├── templates/
│   ├── index.html
│   ├── login.html
│   └── register.html
├── static/
│   ├── style.css
│   ├── phase3.css
│   └── script.js
├── uploads/
│   ├── .gitkeep
│   ├── user_1/                # generated at runtime
│   └── user_2/
├── tests/
│   └── test_app.py
└── .github/
    └── workflows/
        └── tests.yml
```

## Run Locally

```bash
git clone https://github.com/navadeep-17/Cloud-Computing-Lab-Project.git
cd Cloud-Computing-Lab-Project
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

Install dependencies and run:

```bash
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

On first launch the SQLite database is created automatically at `instance/cloudvault.db`.

## First Demo Flow

1. Create an account.
2. Create a folder such as `CC Lab`.
3. Open that folder.
4. Upload a PDF, image, or text file.
5. Preview the supported file.
6. Download it.
7. Open the Recent Activity section.
8. Log out and create a second account to demonstrate storage isolation.

## Run Tests

```bash
pytest -q
```

The test suite covers authentication, password hashing, file CRUD, previews, folders, quota enforcement, activity history, and cross-user authorization.

## Main Routes

| Method | Route | Purpose |
|---|---|---|
| GET/POST | `/auth/register` | Create a user account |
| GET/POST | `/auth/login` | Sign in |
| POST | `/auth/logout` | Sign out |
| GET | `/` | Authenticated drive dashboard |
| POST | `/upload` | Upload a file owned by the current user |
| GET | `/preview/<file_id>` | Preview an owned supported file |
| GET | `/download/<file_id>` | Download an owned file |
| POST | `/delete/<file_id>` | Delete an owned file |
| POST | `/folders` | Create a logical folder |
| POST | `/folders/<folder_id>/delete` | Delete an empty owned folder |
| GET | `/api/files` | Current user's file, folder, and storage metadata |
| GET | `/api/activity` | Current user's recent activity |
| GET | `/health` | Public service health check |

## Database Model

```text
User
├── id
├── name
├── email
├── password_hash
└── created_at

Folder
├── id
├── owner_id
├── parent_id
├── name
└── created_at

File
├── id
├── owner_id
├── folder_id
├── stored_name
├── original_name
├── size
├── extension
├── category
└── uploaded_at

Activity
├── id
├── user_id
├── file_id
├── action
├── details
└── timestamp
```

## Security and Isolation

- Passwords are hashed before being stored.
- Protected routes require an authenticated session.
- Files are looked up using both file ID and current user ID.
- Folder access is validated against the current user.
- Physical file names are random UUID-based object names rather than user-controlled paths.
- Upload filenames are sanitized.
- SQLite and runtime uploads are ignored by Git.

This is a lab simulator, not a production authentication system. For public deployment, Phase 4 should add production secret management, secure cookies/HTTPS settings, CSRF protection, stronger validation, and a production WSGI server.

## Cloud Computing Concepts Demonstrated

- Centralized storage
- Multi-tenancy simulation
- Client-server architecture
- Authentication and authorization
- Metadata/data separation
- Resource quotas
- HTTP-based resource access
- On-demand upload and retrieval
- Activity/audit logging
- Storage abstraction
- Health monitoring

## Phase 4 Direction

The next phase will introduce a storage-service abstraction so the current local user directories can be replaced by Amazon S3, Azure Blob Storage, or Google Cloud Storage while retaining the same UI, authentication, metadata database, and user workflow.
