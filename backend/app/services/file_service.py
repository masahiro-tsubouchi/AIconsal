"""File processing service for handling file uploads and text extraction"""
import os
import tempfile
from typing import Dict, List, Optional
from uuid import uuid4
import aiofiles
import structlog
from fastapi import UploadFile

from app.core.config import get_settings
from app.models.files import UploadedFile, FileProcessingResult

logger = structlog.get_logger()


class FileService:
    """Service for managing file uploads and processing"""
    
    def __init__(self):
        self._files: Dict[str, UploadedFile] = {}
        self._settings = get_settings()
    
    async def process_uploaded_file(
        self, 
        file: UploadFile, 
        session_id: str
    ) -> UploadedFile:
        """Process an uploaded file and extract text content"""
        file_id = str(uuid4())
        
        try:
            # Read file content
            content = await file.read()
            
            # Create temporary file for processing
            file_extension = os.path.splitext(file.filename or "")[1].lower()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Extract text based on file type
                extracted_text = await self._extract_text_from_file(temp_file_path, file_extension)
                
                # Create file record
                uploaded_file = UploadedFile(
                    id=file_id,
                    filename=f"{file_id}{file_extension}",
                    original_filename=file.filename or "unknown",
                    file_type=file_extension,
                    file_size=len(content),
                    content=extracted_text,
                    session_id=session_id
                )
                
                # Store in memory
                self._files[file_id] = uploaded_file
                
                logger.info(
                    "file_processed",
                    file_id=file_id,
                    filename=file.filename,
                    file_type=file_extension,
                    content_length=len(extracted_text or ""),
                    session_id=session_id
                )
                
                return uploaded_file
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(
                "file_processing_error",
                file_id=file_id,
                filename=file.filename,
                error=str(e)
            )
            raise e
    
    async def _extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """Extract text from different file types"""
        try:
            if file_type == '.txt':
                return await self._extract_from_txt(file_path)
            elif file_type == '.pdf':
                return await self._extract_from_pdf(file_path)
            elif file_type == '.docx':
                return await self._extract_from_docx(file_path)
            elif file_type in ['.csv', '.xlsx']:
                return await self._extract_from_spreadsheet(file_path, file_type)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error("text_extraction_error", file_path=file_path, file_type=file_type, error=str(e))
            return f"ファイルの内容を読み取れませんでした: {str(e)}"
    
    async def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            return await f.read()
    
    async def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            text_content = []
            
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())
            
            return '\n'.join(text_content)
        except ImportError:
            return "PDFファイルの処理にはPyPDF2が必要です"
        except Exception as e:
            return f"PDFファイルの読み取りエラー: {str(e)}"
    
    async def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            from docx import Document
            doc = Document(file_path)
            return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        except ImportError:
            return "DOCXファイルの処理にはpython-docxが必要です"
        except Exception as e:
            return f"DOCXファイルの読み取りエラー: {str(e)}"
    
    async def _extract_from_spreadsheet(self, file_path: str, file_type: str) -> str:
        """Extract text from CSV/XLSX file"""
        try:
            import pandas as pd
            
            if file_type == '.csv':
                df = pd.read_csv(file_path)
            else:  # .xlsx
                df = pd.read_excel(file_path)
            
            # Convert to string representation
            return df.to_string(index=False, max_rows=100)  # Limit rows for performance
            
        except ImportError:
            return f"{file_type}ファイルの処理にはpandasが必要です"
        except Exception as e:
            return f"{file_type}ファイルの読み取りエラー: {str(e)}"
    
    async def get_file_info(self, file_id: str) -> Optional[UploadedFile]:
        """Get information about a file"""
        return self._files.get(file_id)
    
    async def get_session_files(self, session_id: str) -> List[UploadedFile]:
        """Get all files for a session"""
        return [
            file_info for file_info in self._files.values() 
            if file_info.session_id == session_id
        ]
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file"""
        if file_id in self._files:
            del self._files[file_id]
            logger.info("file_deleted", file_id=file_id)
            return True
        return False
    
    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """Clean up old files"""
        import datetime
        
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=max_age_hours)
        files_to_remove = []
        
        for file_id, file_info in self._files.items():
            if file_info.upload_time < cutoff_time:
                files_to_remove.append(file_id)
        
        for file_id in files_to_remove:
            del self._files[file_id]
        
        if files_to_remove:
            logger.info(
                "files_cleaned_up",
                cleaned_count=len(files_to_remove),
                remaining_count=len(self._files)
            )
        
        return len(files_to_remove)
