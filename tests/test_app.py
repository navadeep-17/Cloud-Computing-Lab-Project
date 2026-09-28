import io
from pathlib import Path

import pytest

import app as app_module


@pytest.fixture()
def client(tmp_path):
    original_upload_folder = app_module.UPLOAD_FOLDER
    original_config_folder = app_module.app.config["UPLOAD_FOLDER"]

    app_module.UPLOAD_FOLDER = tmp_path
    app_module.app.config.update(
        TESTING=True,
        UPLOAD_FOLDER=str(tmp_path),
    )

    with app_module.app.test_client() as test_client:
        yield test_client

    app_module.UPLOAD_FOLDER = original_upload_folder
    app_module.app.config["UPLOAD_FOLDER"] = original_config_folder


def upload(client, content: bytes, filename: str, follow_redirects: bool = False):
    return client.post(
        "/upload",
        data={"file": (io.BytesIO(content), filename)},
        content_type="multipart/form-data",
        follow_redirects=follow_redirects,
    )


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Centralized File Storage" in response.data
    assert b"CloudVault" in response.data


def test_upload_list_and_download(client):
    upload_response = upload(client, b"cloud lab test data", "notes.txt", follow_redirects=True)
    assert upload_response.status_code == 200
    assert b"notes.txt uploaded successfully" in upload_response.data

    api_response = client.get("/api/files")
    payload = api_response.get_json()
    assert api_response.status_code == 200
    assert payload["files"][0]["name"] == "notes.txt"
    assert payload["files"][0]["category"] == "document"
    assert payload["files"][0]["previewable"] is True
    assert payload["storage"]["used"] == len(b"cloud lab test data")
    assert payload["storage"]["capacity"] == app_module.STORAGE_CAPACITY

    download_response = client.get("/download/notes.txt")
    assert download_response.status_code == 200
    assert download_response.data == b"cloud lab test data"
    assert "attachment" in download_response.headers["Content-Disposition"]


def test_preview_supported_file(client):
    upload(client, b"preview me", "preview.txt")

    response = client.get("/preview/preview.txt")
    assert response.status_code == 200
    assert response.data == b"preview me"
    assert "attachment" not in response.headers.get("Content-Disposition", "")


def test_preview_rejects_unsupported_file_type(client):
    upload(client, b"binary-ish", "archive.zip")

    response = client.get("/preview/archive.zip")
    assert response.status_code == 415


def test_duplicate_filename_gets_unique_name(client):
    for _ in range(2):
        response = upload(client, b"same name", "report.pdf")
        assert response.status_code == 302

    stored_names = sorted(path.name for path in Path(app_module.UPLOAD_FOLDER).iterdir())
    assert stored_names == ["report.pdf", "report_1.pdf"]


def test_delete_file(client):
    upload(client, b"delete me", "temp.txt")

    delete_response = client.post("/delete/temp.txt", follow_redirects=True)
    assert delete_response.status_code == 200
    assert b"temp.txt deleted" in delete_response.data
    assert not (Path(app_module.UPLOAD_FOLDER) / "temp.txt").exists()


def test_storage_quota_blocks_upload(client, monkeypatch):
    monkeypatch.setattr(app_module, "STORAGE_CAPACITY", 5)

    response = upload(client, b"123456", "too-big.txt", follow_redirects=True)
    assert response.status_code == 200
    assert b"Not enough storage" in response.data
    assert not (Path(app_module.UPLOAD_FOLDER) / "too-big.txt").exists()


def test_health_endpoint(client):
    response = client.get("/health")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["storage_backend"] == "local-directory"
    assert payload["files"] == 0
