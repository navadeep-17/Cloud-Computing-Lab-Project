from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

import auth
import database
import security
from auth import login_required
from database import get_db

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
DATABASE_PATH = BASE_DIR / "instance" / "cloudvault.db"
MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB per upload
STORAGE_CAPACITY = 250 * 1024 * 1024  # 250 MB per-user simulated cloud capacity

PREVIEWABLE_EXTENSIONS = {
    "bmp", "csv", "gif", "jpeg", "jpg", "json", "md", "pdf", "png", "txt", "webp"
}
IMAGE_EXTENSIONS = {"bmp", "gif", "jpeg", "jpg", "png", "webp"}
DOCUMENT_EXTENSIONS = {"doc", "docx", "odt", "pdf", "rtf", "txt", "md"}
SPREADSHEET_EXTENSIONS = {"csv", "ods", "xls", "xlsx"}
ARCHIVE_EXTENSIONS = {"7z", "gz", "rar", "tar", "zip"}
CODE_EXTENSIONS = {"c", "cpp", "css", "html", "java", "js", "json", "jsx", "py", "ts", "tsx"}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    UPLOAD_FOLDER=str(UPLOAD_FOLDER),
    DATABASE=str(DATABASE_PATH),
    MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
)

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
database.init_app(app)
app.register_blueprint(auth.bp)
security.init_app(app)


def human_readable_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def file_category(extension: str) -> str:
    if extension in IMAGE_EXTENSIONS:
        return "image"
    if extension in DOCUMENT_EXTENSIONS:
        return "document"
    if extension in SPREADSHEET_EXTENSIONS:
        return "spreadsheet"
    if extension in ARCHIVE_EXTENSIONS:
        return "archive"
    if extension in CODE_EXTENSIONS:
        return "code"
    return "file"


def uploaded_file_size(uploaded_file) -> int:
    current_position = uploaded_file.stream.tell()
    uploaded_file.stream.seek(0, os.SEEK_END)
    size = uploaded_file.stream.tell()
    uploaded_file.stream.seek(current_position)
    return size


def user_storage_directory(user_id: int) -> Path:
    directory = UPLOAD_FOLDER / f"user_{user_id}"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def format_database_time(value: str) -> tuple[str, float]:
    parsed = datetime.fromisoformat(value.replace(" ", "T")).replace(tzinfo=timezone.utc).astimezone()
    return parsed.strftime("%d %b %Y, %I:%M %p"), parsed.timestamp()


def file_row_to_dict(row) -> dict:
    uploaded_label, uploaded_timestamp = format_database_time(row["uploaded_at"])
    return {
        "id": row["id"],
        "name": row["original_name"],
        "stored_name": row["stored_name"],
        "size": row["size"],
        "size_label": human_readable_size(row["size"]),
        "modified": row["uploaded_at"],
        "modified_timestamp": uploaded_timestamp,
        "modified_label": uploaded_label,
        "extension": row["extension"],
        "category": row["category"],
        "previewable": row["extension"] in PREVIEWABLE_EXTENSIONS,
        "folder_id": row["folder_id"],
    }


def storage_summary(user_id: int) -> dict:
    row = get_db().execute(
        "SELECT COALESCE(SUM(size), 0) AS used, COUNT(*) AS total_files FROM files WHERE owner_id = ?",
        (user_id,),
    ).fetchone()
    used = int(row["used"])
    percentage = min((used / STORAGE_CAPACITY) * 100, 100) if STORAGE_CAPACITY else 0
    available = max(STORAGE_CAPACITY - used, 0)
    return {
        "used": used,
        "used_label": human_readable_size(used),
        "capacity": STORAGE_CAPACITY,
        "capacity_label": human_readable_size(STORAGE_CAPACITY),
        "available": available,
        "available_label": human_readable_size(available),
        "percentage": round(percentage, 1),
        "total_files": int(row["total_files"]),
    }


def get_owned_folder(folder_id: int | None, user_id: int):
    if folder_id is None:
        return None
    folder = get_db().execute(
        "SELECT * FROM folders WHERE id = ? AND owner_id = ?",
        (folder_id, user_id),
    ).fetchone()
    if folder is None:
        abort(404)
    return folder


def get_owned_file(file_id: int, user_id: int):
    file_record = get_db().execute(
        "SELECT * FROM files WHERE id = ? AND owner_id = ?",
        (file_id, user_id),
    ).fetchone()
    if file_record is None:
        abort(404)
    return file_record


def folder_id_from_value(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        abort(400)


def folder_breadcrumbs(folder, user_id: int) -> list[dict]:
    breadcrumbs = []
    current = folder
    db = get_db()
    while current is not None:
        breadcrumbs.append({"id": current["id"], "name": current["name"]})
        parent_id = current["parent_id"]
        if parent_id is None:
            break
        current = db.execute(
            "SELECT * FROM folders WHERE id = ? AND owner_id = ?",
            (parent_id, user_id),
        ).fetchone()
    breadcrumbs.reverse()
    return breadcrumbs


def log_activity(user_id: int, action: str, details: str, file_id: int | None = None) -> None:
    get_db().execute(
        "INSERT INTO activities (user_id, file_id, action, details) VALUES (?, ?, ?, ?)",
        (user_id, file_id, action, details),
    )


@app.get("/")
@login_required
def index():
    user_id = g.user["id"]
    current_folder_id = folder_id_from_value(request.args.get("folder"))
    current_folder = get_owned_folder(current_folder_id, user_id)
    db = get_db()

    files = [
        file_row_to_dict(row)
        for row in db.execute(
            "SELECT * FROM files WHERE owner_id = ? AND folder_id IS ? ORDER BY uploaded_at DESC, id DESC",
            (user_id, current_folder_id),
        ).fetchall()
    ]
    folders = db.execute(
        "SELECT * FROM folders WHERE owner_id = ? AND parent_id IS ? ORDER BY name COLLATE NOCASE",
        (user_id, current_folder_id),
    ).fetchall()
    activities = db.execute(
        """
        SELECT a.*, f.original_name
        FROM activities a
        LEFT JOIN files f ON f.id = a.file_id
        WHERE a.user_id = ?
        ORDER BY a.timestamp DESC, a.id DESC
        LIMIT 15
        """,
        (user_id,),
    ).fetchall()
    storage = storage_summary(user_id)

    return render_template(
        "index.html",
        files=files,
        folders=folders,
        activities=activities,
        current_folder=current_folder,
        current_folder_id=current_folder_id,
        breadcrumbs=folder_breadcrumbs(current_folder, user_id),
        total_files=storage["total_files"],
        total_size=storage["used_label"],
        storage=storage,
        max_upload_mb=app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024),
    )


@app.post("/upload")
@login_required
def upload_file():
    user_id = g.user["id"]
    folder_id = folder_id_from_value(request.form.get("folder_id"))
    get_owned_folder(folder_id, user_id)

    uploaded_file = request.files.get("file")
    if uploaded_file is None or uploaded_file.filename == "":
        flash("Please choose a file to upload.", "error")
        return redirect(url_for("index", folder=folder_id) if folder_id else url_for("index"))

    original_name = secure_filename(uploaded_file.filename)
    if not original_name:
        flash("Invalid filename.", "error")
        return redirect(url_for("index", folder=folder_id) if folder_id else url_for("index"))

    file_size = uploaded_file_size(uploaded_file)
    storage = storage_summary(user_id)
    if storage["used"] + file_size > STORAGE_CAPACITY:
        flash(f"Not enough storage. {storage['available_label']} is available.", "error")
        return redirect(url_for("index", folder=folder_id) if folder_id else url_for("index"))

    extension = Path(original_name).suffix.lower().lstrip(".") or "file"
    stored_name = f"{uuid4().hex}{Path(original_name).suffix.lower()}"
    storage_directory = user_storage_directory(user_id)
    destination = storage_directory / stored_name
    uploaded_file.save(destination)

    db = get_db()
    try:
        cursor = db.execute(
            """
            INSERT INTO files (owner_id, folder_id, stored_name, original_name, size, extension, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, folder_id, stored_name, original_name, file_size, extension, file_category(extension)),
        )
        log_activity(user_id, "upload", f"Uploaded {original_name}", cursor.lastrowid)
        db.commit()
    except Exception:
        destination.unlink(missing_ok=True)
        db.rollback()
        raise

    flash(f"{original_name} uploaded successfully.", "success")
    return redirect(url_for("index", folder=folder_id) if folder_id else url_for("index"))


@app.get("/download/<int:file_id>")
@login_required
def download_file(file_id: int):
    user_id = g.user["id"]
    file_record = get_owned_file(file_id, user_id)
    storage_directory = user_storage_directory(user_id)
    if not (storage_directory / file_record["stored_name"]).is_file():
        abort(404)

    log_activity(user_id, "download", f"Downloaded {file_record['original_name']}", file_id)
    get_db().commit()
    return send_from_directory(
        storage_directory,
        file_record["stored_name"],
        as_attachment=True,
        download_name=file_record["original_name"],
    )


@app.get("/preview/<int:file_id>")
@login_required
def preview_file(file_id: int):
    user_id = g.user["id"]
    file_record = get_owned_file(file_id, user_id)
    if file_record["extension"] not in PREVIEWABLE_EXTENSIONS:
        abort(415)

    storage_directory = user_storage_directory(user_id)
    if not (storage_directory / file_record["stored_name"]).is_file():
        abort(404)

    return send_from_directory(
        storage_directory,
        file_record["stored_name"],
        as_attachment=False,
        download_name=file_record["original_name"],
        max_age=0,
    )


@app.post("/delete/<int:file_id>")
@login_required
def delete_file(file_id: int):
    user_id = g.user["id"]
    file_record = get_owned_file(file_id, user_id)
    folder_id = file_record["folder_id"]
    storage_directory = user_storage_directory(user_id)
    (storage_directory / file_record["stored_name"]).unlink(missing_ok=True)

    db = get_db()
    log_activity(user_id, "delete", f"Deleted {file_record['original_name']}", file_id)
    db.execute("DELETE FROM files WHERE id = ? AND owner_id = ?", (file_id, user_id))
    db.commit()

    flash(f"{file_record['original_name']} deleted.", "success")
    return redirect(url_for("index", folder=folder_id) if folder_id else url_for("index"))


@app.post("/folders")
@login_required
def create_folder():
    user_id = g.user["id"]
    parent_id = folder_id_from_value(request.form.get("parent_id"))
    get_owned_folder(parent_id, user_id)

    name = request.form.get("name", "").strip()
    if not name or len(name) > 80 or "/" in name or "\\" in name:
        flash("Folder name must be 1-80 characters and cannot contain slashes.", "error")
        return redirect(url_for("index", folder=parent_id) if parent_id else url_for("index"))

    db = get_db()
    existing = db.execute(
        "SELECT id FROM folders WHERE owner_id = ? AND parent_id IS ? AND lower(name) = lower(?)",
        (user_id, parent_id, name),
    ).fetchone()
    if existing:
        flash("A folder with that name already exists here.", "error")
        return redirect(url_for("index", folder=parent_id) if parent_id else url_for("index"))

    db.execute(
        "INSERT INTO folders (owner_id, name, parent_id) VALUES (?, ?, ?)",
        (user_id, name, parent_id),
    )
    log_activity(user_id, "folder_created", f"Created folder {name}")
    db.commit()
    flash(f"Folder {name} created.", "success")
    return redirect(url_for("index", folder=parent_id) if parent_id else url_for("index"))


@app.post("/folders/<int:folder_id>/delete")
@login_required
def delete_folder(folder_id: int):
    user_id = g.user["id"]
    folder = get_owned_folder(folder_id, user_id)
    db = get_db()
    has_files = db.execute(
        "SELECT 1 FROM files WHERE owner_id = ? AND folder_id = ? LIMIT 1",
        (user_id, folder_id),
    ).fetchone()
    has_children = db.execute(
        "SELECT 1 FROM folders WHERE owner_id = ? AND parent_id = ? LIMIT 1",
        (user_id, folder_id),
    ).fetchone()
    if has_files or has_children:
        flash("Only empty folders can be deleted.", "error")
        return redirect(url_for("index", folder=folder_id))

    parent_id = folder["parent_id"]
    db.execute("DELETE FROM folders WHERE id = ? AND owner_id = ?", (folder_id, user_id))
    log_activity(user_id, "folder_deleted", f"Deleted folder {folder['name']}")
    db.commit()
    flash(f"Folder {folder['name']} deleted.", "success")
    return redirect(url_for("index", folder=parent_id) if parent_id else url_for("index"))


@app.get("/api/files")
@login_required
def api_files():
    user_id = g.user["id"]
    db = get_db()
    files = [file_row_to_dict(row) for row in db.execute(
        "SELECT * FROM files WHERE owner_id = ? ORDER BY uploaded_at DESC, id DESC",
        (user_id,),
    ).fetchall()]
    folders = [dict(row) for row in db.execute(
        "SELECT id, name, parent_id, created_at FROM folders WHERE owner_id = ? ORDER BY name COLLATE NOCASE",
        (user_id,),
    ).fetchall()]
    return jsonify({"files": files, "folders": folders, "storage": storage_summary(user_id)})


@app.get("/api/activity")
@login_required
def api_activity():
    rows = get_db().execute(
        "SELECT id, file_id, action, details, timestamp FROM activities WHERE user_id = ? ORDER BY timestamp DESC, id DESC LIMIT 50",
        (g.user["id"],),
    ).fetchall()
    return jsonify({"activities": [dict(row) for row in rows]})


@app.get("/health")
def health():
    get_db().execute("SELECT 1").fetchone()
    return jsonify({
        "status": "ok",
        "storage_backend": "local-directory",
        "metadata_backend": "sqlite",
        "authentication": "session",
    })


@app.errorhandler(413)
def request_entity_too_large(_error):
    max_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    flash(f"File is too large. Maximum size is {max_mb} MB.", "error")
    if g.get("user") is not None:
        return redirect(url_for("index"))
    return redirect(url_for("auth.login"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
