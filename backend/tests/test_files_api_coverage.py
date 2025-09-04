import io
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import get_settings
from app.services.file_service import FileService


def test_file_upload_txt_success_and_session_listing(client: TestClient):
    # Use a shared FileService instance across requests so in-memory store persists
    shared_service = FileService()
    app.dependency_overrides[FileService] = lambda: shared_service
    try:
        content = "hello world\n品質向上".encode("utf-8")
        files = {"file": ("sample.txt", content, "text/plain")}
        resp = client.post("/api/v1/files/upload", files=files, data={"session_id": "sess-f1"})
        assert resp.status_code == 200
        data = resp.json()
        file_id = data["file"]["id"]
        assert data["file"]["original_filename"] == "sample.txt"
        assert data["file"]["session_id"] == "sess-f1"

        # List session files includes the uploaded one
        resp2 = client.get("/api/v1/files/session/sess-f1")
        assert resp2.status_code == 200
        files_list = resp2.json()
        assert any(f["id"] == file_id for f in files_list)

        # Delete the file
        del_resp = client.delete(f"/api/v1/files/{file_id}")
        assert del_resp.status_code == 200
        # Fetch after delete should be 404
        info_resp = client.get(f"/api/v1/files/{file_id}")
        assert info_resp.status_code == 404
    finally:
        app.dependency_overrides.pop(FileService, None)


def test_file_upload_unsupported_type_returns_400(client: TestClient):
    content = b"binary data"
    files = {"file": ("data.bin", content, "application/octet-stream")}
    resp = client.post("/api/v1/files/upload", files=files, data={"session_id": "sess-f2"})
    assert resp.status_code == 400
    assert "サポートされていないファイル形式" in resp.json().get("detail", "")


def test_get_file_info_not_found_returns_404(client: TestClient):
    resp = client.get("/api/v1/files/nonexistent-id")
    assert resp.status_code == 404


def test_upload_exceeds_size_limit_returns_413(client: TestClient, monkeypatch: "pytest.MonkeyPatch"):
    # Patch the get_settings used inside the files API module directly
    from app.core.config import Settings
    monkeypatch.setattr("app.api.v1.files.get_settings", lambda: Settings(max_file_size=1))
    content = b"abcd"  # 4 bytes
    files = {"file": ("big.txt", content, "text/plain")}
    resp = client.post("/api/v1/files/upload", files=files, data={"session_id": "s-size"})
    assert resp.status_code == 413
    assert "ファイルサイズ" in resp.json().get("detail", "")


def test_upload_generic_exception_returns_500(client: TestClient):
    # Force FileService to raise a generic exception during processing
    class BoomService(FileService):
        async def process_uploaded_file(self, file, session_id: str):  # type: ignore[override]
            raise RuntimeError("boom")

    app.dependency_overrides[FileService] = BoomService
    try:
        content = b"ok"
        files = {"file": ("ok.txt", content, "text/plain")}
        resp = client.post("/api/v1/files/upload", files=files, data={"session_id": "s-err"})
        assert resp.status_code == 500
        assert "ファイル処理エラー" in resp.json().get("detail", "")
    finally:
        app.dependency_overrides.pop(FileService, None)


def test_get_file_info_generic_exception_returns_500(client: TestClient):
    class BoomInfoService(FileService):
        async def get_file_info(self, file_id: str):  # type: ignore[override]
            raise RuntimeError("get-info-broke")

    app.dependency_overrides[FileService] = BoomInfoService
    try:
        resp = client.get("/api/v1/files/some-id")
        assert resp.status_code == 500
        assert "ファイル情報取得エラー" in resp.json().get("detail", "")
    finally:
        app.dependency_overrides.pop(FileService, None)


def test_get_session_files_generic_exception_returns_500(client: TestClient):
    class BoomSessionService(FileService):
        async def get_session_files(self, session_id: str):  # type: ignore[override]
            raise RuntimeError("session-broke")

    app.dependency_overrides[FileService] = BoomSessionService
    try:
        resp = client.get("/api/v1/files/session/some-session")
        assert resp.status_code == 500
        assert "セッションファイル取得エラー" in resp.json().get("detail", "")
    finally:
        app.dependency_overrides.pop(FileService, None)


def test_delete_file_generic_exception_returns_500(client: TestClient):
    class BoomDeleteService(FileService):
        async def delete_file(self, file_id: str):  # type: ignore[override]
            raise RuntimeError("delete-broke")

    app.dependency_overrides[FileService] = BoomDeleteService
    try:
        resp = client.delete("/api/v1/files/any")
        assert resp.status_code == 500
        assert "ファイル削除エラー" in resp.json().get("detail", "")
    finally:
        app.dependency_overrides.pop(FileService, None)


@pytest.mark.asyncio
async def test_file_service_extract_text_variants_no_optional_libs(tmp_path: "os.PathLike[str]"):
    svc = FileService()

    # .txt extraction
    txt_path = tmp_path / "a.txt"
    txt_path.write_text("A\nB\nC", encoding="utf-8")
    txt_text = await svc._extract_text_from_file(str(txt_path), ".txt")
    assert "A\nB\nC" in txt_text

    # .pdf without PyPDF2
    pdf_path = tmp_path / "a.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 dummy")
    pdf_text = await svc._extract_text_from_file(str(pdf_path), ".pdf")
    assert "PDF" in pdf_text  # returns guidance/error string

    # .docx without python-docx
    docx_path = tmp_path / "a.docx"
    docx_path.write_bytes(b"PK\x03\x04dummy")
    docx_text = await svc._extract_text_from_file(str(docx_path), ".docx")
    assert "DOCX" in docx_text  # guidance/error string

    # .xlsx without pandas
    xlsx_path = tmp_path / "a.xlsx"
    xlsx_path.write_bytes(b"PK\x03\x04dummy")
    xlsx_text = await svc._extract_text_from_file(str(xlsx_path), ".xlsx")
    # Depending on environment, may return ImportError guidance mentioning pandas
    # or a general reading error message. Accept either.
    assert ("pandas" in xlsx_text) or ("読み取りエラー" in xlsx_text)


@pytest.mark.asyncio
async def test_file_service_cleanup_and_delete_paths(tmp_path: "os.PathLike[str]"):
    svc = FileService()
    # Simulate a stored file
    from app.models.files import UploadedFile
    uf = UploadedFile(
        id="f-1",
        filename="f-1.txt",
        original_filename="orig.txt",
        file_type=".txt",
        file_size=5,
        content="abc",
        session_id="s-1",
    )
    svc._files[uf.id] = uf

    # delete existing returns True
    deleted = await svc.delete_file("f-1")
    assert deleted is True
    # delete missing returns False
    deleted2 = await svc.delete_file("missing")
    assert deleted2 is False

    # cleanup (no old files -> 0)
    cleaned = await svc.cleanup_old_files(max_age_hours=0)  # none have upload_time in past
    assert isinstance(cleaned, int)
