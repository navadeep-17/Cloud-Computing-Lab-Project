from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB

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


def get_file_metadata(path: Path) -> dict:
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).astimezone()
    return {
        "name": path.name,
        "size": stat.st_size,
        "size_label": human_readable_size(stat.st_size),
        "modified": modified.isoformat(),
        "modified_label": modified.strftime("%d %b %Y, %I:%M %p"),
        "extension": path.suffix.lower().lstrip(".") or "file",
    }


def list_stored_files() -> list[dict]:
    files = [
        get_file_metadata(path)
        for path in UPLOAD_FOLDER.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    ]
    return sorted(files, key=lambda item: item["modified"], reverse=True)


@app.get("/")
def index():
    files = list_stored_files()
    total_size = sum(item["size"] for item in files)
    return render_template(
        "index.html",
        files=files,
        total_files=len(files),
        total_size=human_readable_size(total_size),
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

    filename = unique_filename(filename)
    uploaded_file.save(UPLOAD_FOLDER / filename)
    return redirect(url_for("index", status="success", message=f"{filename} uploaded successfully."))


@app.get("/download/<path:filename>")
def download_file(filename: str):
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        abort(404)
    file_path = UPLOAD_FOLDER / safe_name
    if not file_path.is_file():
        abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name, as_attachment=True)


@app.post("/delete/<path:filename>")
def delete_file(filename: str):
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        abort(404)
    file_path = UPLOAD_FOLDER / safe_name
    if not file_path.is_file():
        abort(404)
    file_path.unlink()
    return redirect(url_for("index", status="success", message=f"{safe_name} deleted."))


@app.get("/api/files")
def api_files():
    return jsonify({"files": list_stored_files()})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "storage_directory": str(UPLOAD_FOLDER)})


@app.errorhandler(413)
def request_entity_too_large(_error):
    max_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    return redirect(url_for("index", status="error", message=f"File is too large. Maximum size is {max_mb} MB."))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
