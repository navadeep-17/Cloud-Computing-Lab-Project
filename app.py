from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB per upload
STORAGE_CAPACITY = 250 * 1024 * 1024  # 250 MB simulated cloud capacity

PREVIEWABLE_EXTENSIONS = {
    "bmp",
    "csv",
    "gif",
    "jpeg",
    "jpg",
    "json",
    "md",
    "pdf",
    "png",
    "txt",
    "webp",
}

IMAGE_EXTENSIONS = {"bmp", "gif", "jpeg", "jpg", "png", "webp"}
DOCUMENT_EXTENSIONS = {"doc", "docx", "odt", "pdf", "rtf", "txt", "md"}
SPREADSHEET_EXTENSIONS = {"csv", "ods", "xls", "xlsx"}
ARCHIVE_EXTENSIONS = {"7z", "gz", "rar", "tar", "zip"}
CODE_EXTENSIONS = {"c", "cpp", "css", "html", "java", "js", "json", "jsx", "py", "ts", "tsx"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def human_readable_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def unique_filename(filename: str) -> str:
    destination = UPLOAD_FOLDER / filename
    if not destination.exists():
        return filename

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = f"{stem}_{counter}{suffix}"
        if not (UPLOAD_FOLDER / candidate).exists():
            return candidate
        counter += 1


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


def get_file_metadata(path: Path) -> dict:
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).astimezone()
    extension = path.suffix.lower().lstrip(".") or "file"
    return {
        "name": path.name,
        "size": stat.st_size,
        "size_label": human_readable_size(stat.st_size),
        "modified": modified.isoformat(),
        "modified_timestamp": stat.st_mtime,
        "modified_label": modified.strftime("%d %b %Y, %I:%M %p"),
        "extension": extension,
        "category": file_category(extension),
        "previewable": extension in PREVIEWABLE_EXTENSIONS,
    }


def list_stored_files() -> list[dict]:
    files = [
        get_file_metadata(path)
        for path in UPLOAD_FOLDER.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    ]
    return sorted(files, key=lambda item: item["modified_timestamp"], reverse=True)


def storage_summary(files: list[dict] | None = None) -> dict:
    files = files if files is not None else list_stored_files()
    used = sum(item["size"] for item in files)
    percentage = min((used / STORAGE_CAPACITY) * 100, 100) if STORAGE_CAPACITY else 0
    return {
        "used": used,
        "used_label": human_readable_size(used),
        "capacity": STORAGE_CAPACITY,
        "capacity_label": human_readable_size(STORAGE_CAPACITY),
        "available": max(STORAGE_CAPACITY - used, 0),
        "available_label": human_readable_size(max(STORAGE_CAPACITY - used, 0)),
        "percentage": round(percentage, 1),
    }


def safe_file_path(filename: str) -> Path:
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        abort(404)
    file_path = UPLOAD_FOLDER / safe_name
    if not file_path.is_file():
        abort(404)
    return file_path


def uploaded_file_size(uploaded_file) -> int:
    current_position = uploaded_file.stream.tell()
    uploaded_file.stream.seek(0, os.SEEK_END)
    size = uploaded_file.stream.tell()
    uploaded_file.stream.seek(current_position)
    return size


@app.get("/")
def index():
    files = list_stored_files()
    storage = storage_summary(files)
    return render_template(
        "index.html",
        files=files,
        total_files=len(files),
        total_size=storage["used_label"],
        storage=storage,
        max_upload_mb=app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024),
    )


@app.post("/upload")
def upload_file():
    uploaded_file = request.files.get("file")
    if uploaded_file is None or uploaded_file.filename == "":
        return redirect(url_for("index", status="error", message="Please choose a file to upload."))

    filename = secure_filename(uploaded_file.filename)
    if not filename:
        return redirect(url_for("index", status="error", message="Invalid filename."))

    file_size = uploaded_file_size(uploaded_file)
    storage = storage_summary()
    if storage["used"] + file_size > STORAGE_CAPACITY:
        return redirect(
            url_for(
                "index",
                status="error",
                message=f"Not enough storage. {storage['available_label']} is available.",
            )
        )

    filename = unique_filename(filename)
    uploaded_file.save(UPLOAD_FOLDER / filename)
    return redirect(url_for("index", status="success", message=f"{filename} uploaded successfully."))


@app.get("/download/<path:filename>")
def download_file(filename: str):
    file_path = safe_file_path(filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], file_path.name, as_attachment=True)


@app.get("/preview/<path:filename>")
def preview_file(filename: str):
    file_path = safe_file_path(filename)
    extension = file_path.suffix.lower().lstrip(".")
    if extension not in PREVIEWABLE_EXTENSIONS:
        abort(415)
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        file_path.name,
        as_attachment=False,
        max_age=0,
    )


@app.post("/delete/<path:filename>")
def delete_file(filename: str):
    file_path = safe_file_path(filename)
    file_path.unlink()
    return redirect(url_for("index", status="success", message=f"{file_path.name} deleted."))


@app.get("/api/files")
def api_files():
    files = list_stored_files()
    return jsonify({"files": files, "storage": storage_summary(files)})


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "storage_backend": "local-directory",
            "files": len(list_stored_files()),
        }
    )


@app.errorhandler(413)
def request_entity_too_large(_error):
    max_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    return redirect(url_for("index", status="error", message=f"File is too large. Maximum size is {max_mb} MB."))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
