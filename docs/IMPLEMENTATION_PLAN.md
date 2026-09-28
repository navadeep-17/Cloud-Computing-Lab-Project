# Implementation Plan

## Goal

Build a lab-ready cloud-file-storage simulator that starts with centralized local storage and evolves toward a real cloud-object-storage application without changing the basic user workflow.

## Phase 1 — Core File Storage

**Status: Complete**

### Objectives completed

- Flask application structure
- Centralized `uploads/` directory
- Upload, list, download, and delete operations
- Secure filename handling
- Duplicate-name protection
- File metadata and search
- Responsive browser interface
- API and health routes
- Automated tests

### Main deliverable

A user can upload a file from a browser, see it in centralized storage, download it again, and delete it.

---

## Phase 2 — Enhanced File Management

**Status: Complete**

### Objectives completed

- Upload progress feedback
- Client-side upload-size checks
- Filename search
- Category filtering
- Sorting by date, name, and size
- File classification
- Details modal
- Safe inline previews
- Storage-usage visualization
- Simulated storage capacity
- Backend quota enforcement
- Expanded automated tests

### Main deliverable

A polished mini cloud-drive dashboard that demonstrates file operations and resource-capacity management.

---

## Phase 3 — Multi-User Application Layer

**Status: Complete**

### Objectives completed

- SQLite database
- User registration, login, and logout
- Werkzeug password hashing
- Session-based authentication
- Per-user file ownership
- Per-user physical storage directories
- Persistent database metadata records
- Nested logical folders
- Upload/download/delete activity history
- Account and folder activity history
- Per-user storage statistics and quota enforcement
- Authorization checks on every protected file/folder operation
- Cross-user access-isolation tests

### Implemented data model

```text
User
├── id
├── name
├── email
├── password_hash
└── created_at

File
├── id
├── owner_id
├── stored_name
├── original_name
├── size
├── extension
├── category
├── uploaded_at
└── folder_id

Folder
├── id
├── owner_id
├── parent_id
├── name
└── created_at

Activity
├── id
├── user_id
├── file_id
├── action
├── details
└── timestamp
```

### Main deliverable

A multi-user storage application where signed-in users see and manage only their own files and folders, while metadata and activity history persist in SQLite.

---

## Phase 4 — Real Cloud Storage and Deployment

**Status: Planned**

### Objectives

- Introduce a storage-service abstraction
- Keep local storage as a development backend
- Add one real object-storage backend:
  - Amazon S3, or
  - Azure Blob Storage, or
  - Google Cloud Storage
- Move production secrets to environment variables
- Add secure production configuration
- Add CSRF protection and hardened cookies
- Deploy behind a production WSGI server
- Add deployment health checks
- Add architecture and workflow diagrams
- Prepare evaluation/demo documentation

### Target architecture

```text
Browser
   │
   │ HTTPS
   ▼
Flask Application
   │
   ├── Authentication / SQLite metadata
   │
   └── Storage service interface
          │
          ├── LocalStorageBackend
          └── CloudObjectStorageBackend
                    │
                    ▼
             S3 / Blob / GCS
```

### Main deliverable

The same end-user workflow backed by actual cloud infrastructure.

---

## Evaluation Preparation

Before the final lab demonstration:

1. Run all automated tests.
2. Register two users and demonstrate data isolation.
3. Create a nested folder structure.
4. Upload multiple file types.
5. Demonstrate preview, sorting, download, and delete.
6. Show the activity history after download/delete operations.
7. Demonstrate `/api/files`, `/api/activity`, and `/health`.
8. Explain why metadata lives in SQLite while file bytes live in the storage layer.
9. Explain centralized storage, multi-tenancy, authentication, and authorization.
10. Explain how Phase 4 replaces the local storage implementation with S3/Blob/GCS.
11. Keep screenshots and an architecture diagram ready for the lab record/report.
