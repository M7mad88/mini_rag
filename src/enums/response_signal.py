# src/enums/response_signal.py
from enum import Enum


class ResponseSignal(str, Enum):
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    FILE_TOO_LARGE = "file_too_large"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    VALIDATION_ERROR = "validation_error"
    FILE_PROCESS_SUCCESS = "file_process_success"
    FILE_PROCESS_FAILED = "file_process_failed"
    FILE_NOT_FOUND = "file_not_found"
    INDEX_SUCCESS = "index_success"
    INDEX_FAILED = "index_failed"
    SEARCH_SUCCESS = "search_success"
    SEARCH_FAILED = "search_failed"
