"""Tests for file upload API endpoints"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
import io
import tempfile
import os


class TestFileAPI:
    """Test cases for file upload API endpoints"""
    
    @pytest.mark.unit
    def test_upload_text_file_success(self, client: TestClient, sample_text_file):
        """Test successful text file upload"""
        # Arrange
        with open(sample_text_file, 'rb') as f:
            files = {"file": ("test.txt", f, "text/plain")}
            data = {"session_id": "test-session"}
            
            # Act
            response = client.post("/api/v1/files/upload", files=files, data=data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "file" in data
        assert "message" in data
        
        file_info = data["file"]
        assert file_info["original_filename"] == "test.txt"
        assert file_info["file_type"] == ".txt"
        assert "content" in file_info
        assert len(file_info["content"]) > 0
    
    @pytest.mark.unit
    def test_upload_file_without_session_id(self, client: TestClient):
        """Test file upload without session_id"""
        # Arrange
        file_content = b"Test file content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        # Act
        response = client.post("/api/v1/files/upload", files=files)
        
        # Assert
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_upload_large_file_fails(self, client: TestClient):
        """Test uploading file that exceeds size limit"""
        # Arrange - Create large file content (11MB)
        large_content = b"a" * (11 * 1024 * 1024)
        files = {"file": ("large.txt", io.BytesIO(large_content), "text/plain")}
        data = {"session_id": "test-session"}
        
        # Act
        response = client.post("/api/v1/files/upload", files=files, data=data)
        
        # Assert
        assert response.status_code == 413  # Payload Too Large
    
    @pytest.mark.unit
    def test_upload_unsupported_file_type_fails(self, client: TestClient):
        """Test uploading unsupported file type"""
        # Arrange
        file_content = b"Binary content"
        files = {"file": ("test.exe", io.BytesIO(file_content), "application/octet-stream")}
        data = {"session_id": "test-session"}
        
        # Act
        response = client.post("/api/v1/files/upload", files=files, data=data)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "サポートされていないファイル形式" in data["detail"]
    
    @pytest.mark.unit
    def test_get_file_info_success(self, client: TestClient, sample_text_file):
        """Test getting file information"""
        # Arrange - First upload a file
        with open(sample_text_file, 'rb') as f:
            files = {"file": ("test.txt", f, "text/plain")}
            data = {"session_id": "test-session"}
            upload_response = client.post("/api/v1/files/upload", files=files, data=data)
        
        file_id = upload_response.json()["file"]["id"]
        
        # Act
        response = client.get(f"/api/v1/files/{file_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == file_id
        assert data["original_filename"] == "test.txt"
        assert "content" in data
    
    @pytest.mark.unit
    def test_get_file_info_nonexistent_file(self, client: TestClient):
        """Test getting info for non-existent file"""
        # Act
        response = client.get("/api/v1/files/nonexistent-file-id")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "ファイルが見つかりません" in data["detail"]
    
    @pytest.mark.integration
    def test_get_session_files(self, client: TestClient, sample_text_file):
        """Test getting all files for a session"""
        # Arrange - Upload multiple files for the same session
        session_id = "multi-file-session"
        
        with open(sample_text_file, 'rb') as f:
            files1 = {"file": ("test1.txt", f, "text/plain")}
            data1 = {"session_id": session_id}
            client.post("/api/v1/files/upload", files=files1, data=data1)
        
        with open(sample_text_file, 'rb') as f:
            files2 = {"file": ("test2.txt", f, "text/plain")}
            data2 = {"session_id": session_id}
            client.post("/api/v1/files/upload", files=files2, data=data2)
        
        # Act
        response = client.get(f"/api/v1/files/session/{session_id}")
        
        # Assert
        assert response.status_code == 200
        files_list = response.json()
        assert len(files_list) == 2
        assert all(file_info["session_id"] == session_id for file_info in files_list)
    
    @pytest.mark.unit
    def test_get_session_files_empty_session(self, client: TestClient):
        """Test getting files for session with no files"""
        # Act
        response = client.get("/api/v1/files/session/empty-session")
        
        # Assert
        assert response.status_code == 200
        files_list = response.json()
        assert files_list == []
    
    @pytest.mark.integration
    def test_delete_file_success(self, client: TestClient, sample_text_file):
        """Test successful file deletion"""
        # Arrange - First upload a file
        with open(sample_text_file, 'rb') as f:
            files = {"file": ("test.txt", f, "text/plain")}
            data = {"session_id": "test-session"}
            upload_response = client.post("/api/v1/files/upload", files=files, data=data)
        
        file_id = upload_response.json()["file"]["id"]
        
        # Act
        response = client.delete(f"/api/v1/files/{file_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == file_id
        assert "削除されました" in data["message"]
        
        # Verify file is actually deleted
        get_response = client.get(f"/api/v1/files/{file_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.unit
    def test_delete_nonexistent_file(self, client: TestClient):
        """Test deleting non-existent file"""
        # Act
        response = client.delete("/api/v1/files/nonexistent-file-id")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "ファイルが見つかりません" in data["detail"]
    
    @pytest.mark.unit
    def test_upload_csv_file(self, client: TestClient):
        """Test uploading CSV file"""
        # Arrange
        csv_content = "名前,年齢,部署\n田中,30,製造\n佐藤,25,品質管理"
        files = {"file": ("data.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {"session_id": "csv-test-session"}
        
        # Act
        response = client.post("/api/v1/files/upload", files=files, data=data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        file_info = data["file"]
        assert file_info["file_type"] == ".csv"
        assert "田中" in file_info["content"]
    
    @pytest.mark.unit
    def test_file_upload_response_structure(self, client: TestClient):
        """Test file upload response structure"""
        # Arrange
        file_content = b"Test content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        data = {"session_id": "structure-test"}
        
        # Act
        response = client.post("/api/v1/files/upload", files=files, data=data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "file" in data
        assert "message" in data
        
        file_info = data["file"]
        required_fields = ["id", "filename", "original_filename", "file_type", 
                          "file_size", "content", "upload_time", "session_id"]
        for field in required_fields:
            assert field in file_info
