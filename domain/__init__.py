"""Domain layer for video transcription service.

This package contains the core business logic, models, and interfaces
that define the application's behavior independently of infrastructure.
"""

from domain.models import (
    VideoFile,
    TranscriptionSegment,
    TranscriptionResult,
    TranscriptionOptions,
)
from domain.interfaces import (
    VideoDownloader,
    Transcriber,
    FileStorage,
    VideoCleanup,
    ProgressCallback,
)
from domain.exceptions import (
    TranscriptionServiceError,
    DownloadError,
    UnsupportedURLError,
    TranscriptionError,
    ModelNotFoundError,
    StorageError,
    CleanupError,
    ConfigurationError,
)

__all__ = [
    # Models
    "VideoFile",
    "TranscriptionSegment",
    "TranscriptionResult",
    "TranscriptionOptions",
    # Interfaces
    "VideoDownloader",
    "Transcriber",
    "FileStorage",
    "VideoCleanup",
    "ProgressCallback",
    # Exceptions
    "TranscriptionServiceError",
    "DownloadError",
    "UnsupportedURLError",
    "TranscriptionError",
    "ModelNotFoundError",
    "StorageError",
    "CleanupError",
    "ConfigurationError",
]