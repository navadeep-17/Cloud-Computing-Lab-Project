# Implementation Plan

## Goal

Build a lab-ready cloud-file-storage simulator that starts with a centralized local directory and can later evolve into a real cloud-object-storage application without changing the basic user workflow.

## Phase 1 — Core File Storage

**Status: Complete**

### Objectives

- Establish Flask application structure
- Create centralized `uploads/` storage directory
- Implement upload, list, download, and delete operations
- Add secure filename handling
- Prevent accidental overwrite through duplicate-name handling
- Add file metadata and basic search
- Create a responsive browser interface
- Add API and health routes
- Add automated tests

### Main Deliverable

A user can upload a file from a browser, see it in the centralized file list, download it again, and delete it.

---

## Phase 2 — Enhanced File Management

**Status: Complete**

### Objectives

- Add upload progress feedback
- Add client-side upload-size checks
- Add filename search
- Add category filtering
- Add sorting by date, name, and size
- Classify files by category
- Add a details modal
- Add safe inline previews for supported types
- Add storage-usage visualization
- Introduce a simulated storage capacity
- Enforce the storage quota on the backend
- Extend automated tests

### Main Deliverable

A polished mini cloud-drive dashboard that demonstrates both file operations and resource-capacity management.

---

## Phase 3 — Multi-User Application Layer

**Status: Planned**

### Objectives

- Add SQLite database
- Add user registration and login
- Store password hashes rather than plaintext passwords
- Associate files with users
- Add per-user storage views
- Add persistent metadata records
- Add folders or logical collections
- Add upload/download/delete activity history
- Add basic storage statistics per user
- Add authorization checks to every protected file operation

### Proposed Data Model

```text
User
├── id
├── name
├── email
├── password_hash
└── created_at

FileRecord
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
├── name
└── created_at

Activity
├── id
├── user_id
├── file_id
├── action
└── timestamp
```

### Main Deliverable

A multi-user storage application where users only see and manage their own files.

---

## Phase 4 — Real Cloud Storage and Deployment

**Status: Planned**

### Objectives

- Introduce a storage-service abstraction
- Keep local storage as a development backend
- Add one real object-storage backend
  - Amazon S3, or
  - Azure Blob Storage, or
  - Google Cloud Storage
- Move secrets to environment variables
- Add production configuration
- Deploy the Flask service
- Add deployment health checks
- Add architecture and workflow diagrams
- Prepare evaluation/demo documentation

### Target Architecture

```text
Browser
   │
   │ HTTPS
   ▼
Flask Application
   │
   ├── Authentication / metadata database
   │
   └── Storage service interface
          │
          ├── LocalStorageBackend
          └── CloudObjectStorageBackend
                    │
                    ▼
             S3 / Blob / GCS
```

### Main Deliverable

The same end-user workflow backed by actual cloud infrastructure.

---

## Evaluation Preparation

Before the final lab demonstration:

1. Run all automated tests.
2. Test upload, list, preview, sorting, download, and delete manually.
3. Upload multiple file types for the demo.
4. Keep one unsupported preview type to explain controlled preview behavior.
5. Demonstrate the `/api/files` endpoint.
6. Demonstrate the `/health` endpoint.
7. Explain centralized storage and client-server architecture.
8. Explain why the current local storage simulates cloud storage.
9. Explain how the storage backend can later be replaced by S3/Blob/GCS.
10. Keep screenshots and an architecture diagram ready for the lab record/report.
