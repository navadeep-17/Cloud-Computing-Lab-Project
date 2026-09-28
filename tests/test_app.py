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


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Centralized File Storage" in response.data


def test_upload_list_and_download(client):
    upload_response = client.post(
        "/upload",
        data={"file": (io.BytesIO(b"cloud lab test data"), "notes.txt")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert upload_response.status_code == 200
    assert b"notes.txt uploaded successfully" in upload_response.data

    api_response = client.get("/api/files")
    payload = api_response.get_json()
    assert api_response.status_code == 200
    assert payload["files"][0]["name"] == "notes.txt"

    download_response = client.get("/download/notes.txt")
    assert download_response.status_code == 200
    assert download_response.data == b"cloud lab test data"


def test_duplicate_filename_gets_unique_name(client):
    for _ in range(2):
        response = client.post(
            "/upload",
            data={"file": (io.BytesIO(b"same name"), "report.pdf")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 302

    stored_names = sorted(path.name for path in Path(app_module.UPLOAD_FOLDER).iterdir())
    assert stored_names == ["report.pdf", "report_1.pdf"]


def test_delete_file(client):
    client.post(
        "/upload",
        data={"file": (io.BytesIO(b"delete me"), "temp.txt")},
        content_type="multipart/form-data",
    )

    delete_response = client.post("/delete/temp.txt", follow_redirects=True)
    assert delete_response.status_code == 200
    assert b"temp.txt deleted" in delete_response.data
    assert not (Path(app_module.UPLOAD_FOLDER) / "temp.txt").exists()


def test_health_endpoint(client):
    response = client.get("/health")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
