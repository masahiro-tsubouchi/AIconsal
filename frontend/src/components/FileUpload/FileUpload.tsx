/**
 * File Upload Component
 * Manufacturing AI Assistant Frontend
 */

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle } from 'lucide-react';
import Button from '../ui/Button';
import { FileInfo } from '../../types/api';
import { apiService } from '../../services/api';

interface FileUploadProps {
  sessionId: string;
  onFileUploaded?: (file: FileInfo) => void;
  onError?: (error: string) => void;
  maxFileSize?: number; // bytes
  allowedTypes?: string[];
}

const FileUpload: React.FC<FileUploadProps> = ({
  sessionId,
  onFileUploaded,
  onError,
  maxFileSize = 10 * 1024 * 1024, // 10MB default
  allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<FileInfo[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      setIsUploading(true);
      try {
        const response = await apiService.uploadFile(file, sessionId);
        const fileInfo = response.data;
        setUploadedFiles(prev => [...prev, fileInfo]);
        onFileUploaded?.(fileInfo);
      } catch (error: any) {
        console.error('File upload error:', error);
        onError?.(error.response?.data?.detail || `Failed to upload ${file.name}`);
      } finally {
        setIsUploading(false);
      }
    }
  }, [sessionId, onFileUploaded, onError]);

  const removeFile = useCallback(async (fileId: string) => {
    try {
      await apiService.deleteFile(fileId);
      setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    } catch (error: any) {
      console.error('File deletion error:', error);
      onError?.(error.response?.data?.detail || 'Failed to delete file');
    }
  }, [onError]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxSize: maxFileSize,
    disabled: isUploading,
  });

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const dropzoneClasses = `
    border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer
    ${isDragActive && !isDragReject
      ? 'border-primary-400 bg-primary-50'
      : isDragReject
      ? 'border-error-400 bg-error-50'
      : 'border-secondary-300 hover:border-secondary-400'
    }
    ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
  `;

  return (
    <div className="space-y-4">
      <div {...getRootProps()} className={dropzoneClasses}>
        <input {...getInputProps()} />
        <Upload className="mx-auto h-8 w-8 text-secondary-400 mb-2" />
        {isDragActive ? (
          isDragReject ? (
            <p className="text-error-600">File type not supported</p>
          ) : (
            <p className="text-primary-600">Drop files here...</p>
          )
        ) : (
          <>
            <p className="text-secondary-600 mb-1">
              Drag & drop files here, or click to select
            </p>
            <p className="text-sm text-secondary-500">
              Supports PDF, DOCX, TXT, CSV, XLSX (max {formatFileSize(maxFileSize)})
            </p>
          </>
        )}
      </div>

      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-secondary-700">Uploaded Files:</h3>
          {uploadedFiles.map((file) => (
            <div
              key={file.id}
              className="flex items-center justify-between p-3 bg-secondary-50 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <File className="h-5 w-5 text-secondary-500" />
                <div>
                  <p className="text-sm font-medium text-secondary-900">
                    {file.original_filename}
                  </p>
                  <p className="text-xs text-secondary-500">
                    {formatFileSize(file.size)} • {file.processed ? 'Processed' : 'Processing...'}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeFile(file.id)}
                className="text-error-600 hover:text-error-700 hover:bg-error-50"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {isUploading && (
        <div className="flex items-center justify-center space-x-2 text-sm text-secondary-600">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary-600 border-t-transparent"></div>
          <span>Uploading...</span>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
