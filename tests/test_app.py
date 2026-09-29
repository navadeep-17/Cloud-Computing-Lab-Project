import io
from pathlib import Path

import pytest

import app as app_module
import database


@pytest.fixture()
def client(tmp_path):
    original_upload_folder = app_module.UPLOAD_FOLDER
    original_database = app_module.app.config["DATABASE"]
    original_upload_config = app_module.app.config["UPLOAD_FOLDER"]

    upload_root = tmp_path / "uploads"
    upload_root.mkdir()
    app_module.UPLOAD_FOLDER = upload_root
    app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        DATABASE=str(tmp_path / "test.db"),
        UPLOAD_FOLDER=str(upload_root),
        CSRF_ENABLED=True,
    )

    with app_module.app.app_context():
        database.init_db()

    with app_module.app.test_client() as test_client:
        yield test_client

    app_module.UPLOAD_FOLDER = original_upload_folder
    app_module.app.config["DATABASE"] = original_database
    app_module.app.config["UPLOAD_FOLDER"] = original_upload_config


def csrf_token(client, seed_path="/auth/login"):
    with client.session_transaction() as session:
        token = session.get("_csrf_token")
    if token:
        return token

    client.get(seed_path)
    with client.session_transaction() as session:
        token = session.get("_csrf_token")
    assert token
    return token


def register(client, name="Test User", email="test@example.com", password="secret1"):
    client.get("/auth/register")
    return client.post(
        "/auth/register",
        data={
            "name": name,
            "email": email,
            "password": password,
            "_csrf_token": csrf_token(client, "/auth/register"),
        },
        follow_redirects=True,
    )


def login(client, email="test@example.com", password="secret1"):
    client.get("/auth/login")
    return client.post(
        "/auth/login",
        data={
            "email": email,
            "password": password,
            "_csrf_token": csrf_token(client),
        },
        follow_redirects=True,
    )


def logout(client, follow_redirects=False):
    return client.post(
        "/auth/logout",
        data={"_csrf_token": csrf_token(client)},
        follow_redirects=follow_redirects,
    )


def upload(client, content: bytes, filename: str, folder_id=None, follow_redirects=False):
    data = {
        "file": (io.BytesIO(content), filename),
        "_csrf_token": csrf_token(client),
    }
    if folder_id is not None:
        data["folder_id"] = str(folder_id)
    return client.post(
        "/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=follow_redirects,
    )


def create_folder(client, name, parent_id="", follow_redirects=False):
    return client.post(
        "/folders",
        data={
            "name": name,
            "parent_id": str(parent_id) if parent_id is not None else "",
            "_csrf_token": csrf_token(client),
        },
        follow_redirects=follow_redirects,
    )


def delete_file(client, file_id, follow_redirects=False):
    return client.post(
        f"/delete/{file_id}",
        data={"_csrf_token": csrf_token(client)},
        follow_redirects=follow_redirects,
    )


def delete_folder(client, folder_id, follow_redirects=False):
    return client.post(
        f"/folders/{folder_id}/delete",
        data={"_csrf_token": csrf_token(client)},
        follow_redirects=follow_redirects,
    )


def first_file(client):
    payload = client.get("/api/files").get_json()
    return payload["files"][0]


def test_anonymous_user_is_redirected_to_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_register_creates_session_and_dashboard(client):
    response = register(client)
    assert response.status_code == 200
    assert b"My Drive" in response.data
    assert b"Test User" in response.data


def test_password_is_hashed_not_stored_plaintext(client):
    register(client)
    with app_module.app.app_context():
        row = database.get_db().execute(
            "SELECT password_hash FROM users WHERE email = ?",
            ("test@example.com",),
        ).fetchone()
        assert row is not None
        assert row["password_hash"] != "secret1"
        assert "secret1" not in row["password_hash"]


def test_login_and_logout(client):
    register(client)
    logout(client)

    login_response = login(client)
    assert login_response.status_code == 200
    assert b"My Drive" in login_response.data

    logout_response = logout(client)
    assert logout_response.status_code == 302
    assert "/auth/login" in logout_response.headers["Location"]


def test_duplicate_registration_rolls_back_cleanly(client):
    register(client)
    logout(client)
    duplicate = register(client, name="Other Name")
    assert duplicate.status_code == 200
    assert b"already exists" in duplicate.data

    login_response = login(client)
    assert login_response.status_code == 200
    assert b"My Drive" in login_response.data


def test_csrf_rejects_missing_token(client):
    client.get("/auth/register")
    response = client.post(
        "/auth/register",
        data={"name": "No Token", "email": "notoken@example.com", "password": "secret1"},
    )
    assert response.status_code == 400


def test_security_headers_are_present(client):
    response = client.get("/auth/login")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["Referrer-Policy"] == "same-origin"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"


def test_upload_list_preview_download_and_delete(client):
    register(client)
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

    file_id = payload["files"][0]["id"]

    # File responses are streamed. Explicitly buffering/closing them keeps the
    # test portable to Windows, where an open file handle prevents unlink().
    preview_response = client.get(f"/preview/{file_id}", buffered=True)
    assert preview_response.status_code == 200
    assert preview_response.data == b"cloud lab test data"
    preview_response.close()

    download_response = client.get(f"/download/{file_id}", buffered=True)
    assert download_response.status_code == 200
    assert download_response.data == b"cloud lab test data"
    assert "attachment" in download_response.headers["Content-Disposition"]
    download_response.close()

    delete_response = delete_file(client, file_id, follow_redirects=True)
    assert delete_response.status_code == 200
    assert b"notes.txt deleted" in delete_response.data
    assert client.get("/api/files").get_json()["files"] == []


def test_unsupported_preview_returns_415(client):
    register(client)
    upload(client, b"binary-ish", "archive.zip")
    file_id = first_file(client)["id"]
    assert client.get(f"/preview/{file_id}").status_code == 415


def test_duplicate_display_names_are_stored_as_distinct_objects(client):
    register(client)
    upload(client, b"first", "report.pdf")
    upload(client, b"second", "report.pdf")

    payload = client.get("/api/files").get_json()
    assert len(payload["files"]) == 2
    assert [item["name"] for item in payload["files"]].count("report.pdf") == 2
    assert len({item["stored_name"] for item in payload["files"]}) == 2

    user_directory = Path(app_module.UPLOAD_FOLDER) / "user_1"
    assert len(list(user_directory.iterdir())) == 2


def test_folder_creation_navigation_and_file_assignment(client):
    register(client)
    create_response = create_folder(client, "Lab Reports", follow_redirects=True)
    assert create_response.status_code == 200
    assert b"Lab Reports" in create_response.data

    folder = client.get("/api/files").get_json()["folders"][0]
    folder_id = folder["id"]
    upload(client, b"inside folder", "report.txt", folder_id=folder_id)

    folder_page = client.get(f"/?folder={folder_id}")
    assert folder_page.status_code == 200
    assert b"report.txt" in folder_page.data
    assert b"Lab Reports" in folder_page.data


def test_non_empty_folder_cannot_be_deleted(client):
    register(client)
    create_folder(client, "Keep Me")
    folder_id = client.get("/api/files").get_json()["folders"][0]["id"]
    upload(client, b"data", "inside.txt", folder_id=folder_id)

    response = delete_folder(client, folder_id, follow_redirects=True)
    assert response.status_code == 200
    assert b"Only empty folders can be deleted" in response.data


def test_users_cannot_access_each_others_files(client):
    register(client, name="Alice", email="alice@example.com")
    upload(client, b"alice secret", "alice.txt")
    alice_file_id = first_file(client)["id"]
    logout(client)

    register(client, name="Bob", email="bob@example.com")
    assert client.get("/api/files").get_json()["files"] == []
    assert client.get(f"/download/{alice_file_id}").status_code == 404
    assert client.get(f"/preview/{alice_file_id}").status_code == 404
    assert delete_file(client, alice_file_id).status_code == 404


def test_user_cannot_open_another_users_folder(client):
    register(client, name="Alice", email="alice@example.com")
    create_folder(client, "Alice Folder")
    alice_folder_id = client.get("/api/files").get_json()["folders"][0]["id"]
    logout(client)

    register(client, name="Bob", email="bob@example.com")
    assert client.get(f"/?folder={alice_folder_id}").status_code == 404
    response = client.post(
        "/upload",
        data={"folder_id": str(alice_folder_id), "_csrf_token": csrf_token(client)},
    )
    assert response.status_code == 404


def test_activity_history_records_file_events(client):
    register(client)
    upload(client, b"activity", "activity.txt")
    file_id = first_file(client)["id"]

    download_response = client.get(f"/download/{file_id}", buffered=True)
    assert download_response.status_code == 200
    download_response.close()

    delete_file(client, file_id)

    payload = client.get("/api/activity").get_json()
    actions = [item["action"] for item in payload["activities"]]
    assert "upload" in actions
    assert "download" in actions
    assert "delete" in actions
    assert "account_created" in actions


def test_storage_quota_is_per_user(client, monkeypatch):
    monkeypatch.setattr(app_module, "STORAGE_CAPACITY", 5)
    register(client, name="Alice", email="alice@example.com")
    response = upload(client, b"123456", "too-big.txt", follow_redirects=True)
    assert response.status_code == 200
    assert b"Not enough storage" in response.data
    assert client.get("/api/files").get_json()["files"] == []


def test_health_endpoint_is_public_and_reports_phase_3_backends(client):
    response = client.get("/health")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["storage_backend"] == "local-directory"
    assert payload["metadata_backend"] == "sqlite"
    assert payload["authentication"] == "session"
