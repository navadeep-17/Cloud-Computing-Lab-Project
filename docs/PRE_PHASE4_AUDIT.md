# Pre-Phase 4 Audit

This review was performed after Phase 3 and before introducing real cloud storage or deployment.

## Result

The Phase 3 architecture is functionally sound for the lab project. File ownership checks are enforced using both the requested object ID and the authenticated `owner_id`, and the automated tests cover cross-user isolation.

The audit identified several hardening items that should be completed before deployment. These are addressed by the `pre-phase4-hardening` change set.

## Fixed Before Phase 4

- Added CSRF protection for every state-changing request.
- Added CSRF tokens to registration, login, logout, upload, folder, and delete forms.
- Added browser security headers:
  - Content-Security-Policy
  - X-Content-Type-Options
  - X-Frame-Options
  - Referrer-Policy
  - Permissions-Policy
- Removed inline JavaScript confirmation handlers so the CSP can keep `script-src 'self'`.
- Replaced the known development fallback secret with a cryptographically random process-local fallback.
- Added `HttpOnly` and `SameSite=Lax` session cookie settings.
- Added an environment-controlled secure-cookie option for HTTPS deployment.
- Disabled Flask debug mode by default; it now requires `FLASK_DEBUG=1`.
- Removed the external `Referer` redirect from the 413 upload-size handler.
- Added an explicit database rollback after duplicate-registration integrity errors.
- Added server-side and client-side bounds for account fields.
- Loaded Phase 3 dashboard CSS directly from HTML rather than relying on JavaScript.
- Expanded automated tests for CSRF, browser headers, duplicate-registration recovery, and all existing Phase 3 flows.

## Verified Existing Design

- Passwords are stored with Werkzeug password hashing rather than plaintext.
- Session state is cleared when authentication identity changes.
- File preview, download, and deletion require authenticated ownership.
- Folder access requires authenticated ownership.
- User files are physically separated into per-user directories.
- Stored object names use random UUID values, preventing path and filename collisions.
- SQLite queries use parameter binding rather than string interpolation.
- File metadata and physical object storage are separated.
- Deleting a file preserves its activity record because the activity foreign key uses `ON DELETE SET NULL`.
- Unsupported file types are stored/downloadable but are not rendered inline.

## Phase 4 Work Still Intentionally Deferred

These are architectural/deployment tasks rather than Phase 3 errors:

1. **Storage abstraction** — introduce a storage interface before adding S3, Azure Blob Storage, or Google Cloud Storage.
2. **Production server** — use a production WSGI server instead of Flask's development server.
3. **Stable deployment secret** — set `SECRET_KEY` through the deployment environment. The random fallback is suitable only for local development because sessions are invalidated after process restarts and cannot be shared across multiple workers.
4. **HTTPS cookie mode** — enable `SESSION_COOKIE_SECURE=1` once the application is behind HTTPS.
5. **Database deployment strategy** — SQLite is appropriate for the lab/demo, but a hosted relational database may be preferable for multi-instance production deployment.
6. **Schema migrations** — the current lab application creates missing schema objects on startup; a real deployed service should use a migration workflow as the schema evolves.
7. **Object/content inspection** — extension-based preview controls are sufficient for this lab, but production file-storage services commonly add MIME inspection, malware scanning, and configurable allowed-file policies.
8. **Observability** — production logging, error monitoring, and storage/database health metrics belong in the deployment phase.

## Acceptance Gate

Before merging this audit into `main`:

- the full automated suite must pass with CSRF enabled;
- existing upload/list/preview/download/delete behavior must remain intact;
- multi-user isolation tests must remain green;
- the security regression tests must pass.
