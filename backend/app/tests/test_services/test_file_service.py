"""Tests for FileService"""
import pytest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from fastapi import UploadFile
import io

from app.services.file_service import FileService
from app.models.files import UploadedFile


class TestFileService:
    """Test cases for FileService"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_text_file_success(self, file_service: FileService):
        """Test successful text file processing"""
        # Arrange
        content = b"This is test content"
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.read = Mock(return_value=content)
        session_id = "test-session"
        
        with patch('tempfile.NamedTemporaryFile'), \
             patch.object(file_service, '_extract_text_from_file', return_value="Extracted text"):
            
            # Act
            result = await file_service.process_uploaded_file(mock_file, session_id)
            
            # Assert
            assert isinstance(result, UploadedFile)
            assert result.original_filename == "test.txt"
            assert result.file_type == ".txt"
            assert result.session_id == session_id
            assert result.content == "Extracted text"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_from_txt_file(self, file_service: FileService, sample_text_file):
        """Test text extraction from TXT file"""
        # Act
        result = await file_service._extract_from_txt(sample_text_file)
        
        # Assert
        assert "テスト用のサンプルテキスト" in result
        assert "製造業の改善活動" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_from_unsupported_file_type(self, file_service: FileService):
        """Test extraction from unsupported file type"""
        # Arrange
        temp_file = "/tmp/test.exe"
        
        # Act
        result = await file_service._extract_text_from_file(temp_file, ".exe")
        
        # Assert
        assert "Unsupported file type" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_file_info_existing_file(self, file_service: FileService):
        """Test getting info for existing file"""
        # Arrange
        file_info = UploadedFile(
            id="test-file-id",
            filename="test.txt",
            original_filename="original.txt",
            file_type=".txt",
            file_size=100,
            content="Test content",
            session_id="test-session"
        )
        file_service._files["test-file-id"] = file_info
        
        # Act
        result = await file_service.get_file_info("test-file-id")
        
        # Assert
        assert result == file_info
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_file_info_nonexistent_file(self, file_service: FileService):
        """Test getting info for non-existent file"""
        # Act
        result = await file_service.get_file_info("nonexistent-id")
        
        # Assert
        assert result is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_session_files(self, file_service: FileService):
        """Test getting all files for a session"""
        # Arrange
        session_id = "test-session"
        file1 = UploadedFile(
            id="file1",
            filename="file1.txt",
            original_filename="file1.txt",
            file_type=".txt",
            file_size=100,
            session_id=session_id
        )
        file2 = UploadedFile(
            id="file2",
            filename="file2.txt", 
            original_filename="file2.txt",
            file_type=".txt",
            file_size=200,
            session_id=session_id
        )
        file3 = UploadedFile(
            id="file3",
            filename="file3.txt",
            original_filename="file3.txt", 
            file_type=".txt",
            file_size=150,
            session_id="other-session"
        )
        
        file_service._files.update({
            "file1": file1,
            "file2": file2, 
            "file3": file3
        })
        
        # Act
        result = await file_service.get_session_files(session_id)
        
        # Assert
        assert len(result) == 2
        assert all(f.session_id == session_id for f in result)
        assert {f.id for f in result} == {"file1", "file2"}
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_service: FileService):
        """Test successful file deletion"""
        # Arrange
        file_id = "test-file"
        file_info = UploadedFile(
            id=file_id,
            filename="test.txt",
            original_filename="test.txt",
            file_type=".txt",
            file_size=100,
            session_id="test-session"
        )
        file_service._files[file_id] = file_info
        
        # Act
        result = await file_service.delete_file(file_id)
        
        # Assert
        assert result is True
        assert file_id not in file_service._files
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, file_service: FileService):
        """Test deleting non-existent file"""
        # Act
        result = await file_service.delete_file("nonexistent-id")
        
        # Assert
        assert result is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cleanup_old_files(self, file_service: FileService):
        """Test cleaning up old files"""
        # Arrange
        import datetime
        from unittest.mock import patch
        
        old_time = datetime.datetime.now() - datetime.timedelta(hours=25)
        recent_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        
        old_file = UploadedFile(
            id="old-file",
            filename="old.txt",
            original_filename="old.txt",
            file_type=".txt",
            file_size=100,
            session_id="session1"
        )
        old_file.upload_time = old_time
        
        recent_file = UploadedFile(
            id="recent-file",
            filename="recent.txt",
            original_filename="recent.txt",
            file_type=".txt",
            file_size=100,
            session_id="session2"
        )
        recent_file.upload_time = recent_time
        
        file_service._files.update({
            "old-file": old_file,
            "recent-file": recent_file
        })
        
        # Act
        cleaned_count = await file_service.cleanup_old_files(max_age_hours=24)
        
        # Assert
        assert cleaned_count == 1
        assert "old-file" not in file_service._files
        assert "recent-file" in file_service._files
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_from_csv_file(self, file_service: FileService):
        """Test CSV file text extraction"""
        # Arrange
        csv_content = "名前,年齢,部署\n田中,30,製造\n佐藤,25,品質"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            # Act
            result = await file_service._extract_from_spreadsheet(temp_path, ".csv")
            
            # Assert
            assert "田中" in result
            assert "製造" in result
            assert "佐藤" in result
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_file_processing_error_handling(self, file_service: FileService):
        """Test error handling during file processing"""
        # Arrange
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.read = Mock(side_effect=Exception("Read error"))
        
        # Act & Assert
        with pytest.raises(Exception):
            await file_service.process_uploaded_file(mock_file, "test-session")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_file_processing_workflow(self, file_service: FileService, sample_text_file):
        """Test complete file processing workflow"""
        # Arrange
        session_id = "workflow-test"
        
        # Read the sample file content
        with open(sample_text_file, 'rb') as f:
            content = f.read()
        
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "workflow-test.txt"
        mock_file.read = Mock(return_value=content)
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = sample_text_file
            
            # Act - Process file
            uploaded_file = await file_service.process_uploaded_file(mock_file, session_id)
            
            # Get file info
            retrieved_file = await file_service.get_file_info(uploaded_file.id)
            
            # Get session files
            session_files = await file_service.get_session_files(session_id)
            
            # Delete file
            delete_result = await file_service.delete_file(uploaded_file.id)
            
            # Assert
            assert uploaded_file.session_id == session_id
            assert retrieved_file == uploaded_file
            assert len(session_files) == 1
            assert session_files[0].id == uploaded_file.id
            assert delete_result is True
