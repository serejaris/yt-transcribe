"""Custom exceptions for the transcription service.

This module defines a hierarchy of exceptions for better error handling
and debugging throughout the application.
"""

from typing import Optional


class TranscriptionServiceError(Exception):
    """Base exception for all transcription service errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        """Initialize exception with message and optional details.
        
        Args:
            message: Error message.
            details: Additional error details for debugging.
        """
        super().__init__(message)
        self.details = details or {}


class DownloadError(TranscriptionServiceError):
    """Raised when video download fails."""
    
    def __init__(
        self, 
        url: str, 
        message: str, 
        details: Optional[dict] = None
    ) -> None:
        """Initialize download error.
        
        Args:
            url: The URL that failed to download.
            message: Error message.
            details: Additional error details.
        """
        super().__init__(f"Failed to download {url}: {message}", details)
        self.url = url


class UnsupportedURLError(DownloadError):
    """Raised when URL format is not supported."""
    
    def __init__(self, url: str) -> None:
        """Initialize unsupported URL error."""
        super().__init__(
            url, 
            "URL format is not supported",
            {"supported_formats": ["youtube.com", "youtu.be"]}
        )


class TranscriptionError(TranscriptionServiceError):
    """Raised when transcription fails."""
    
    def __init__(
        self, 
        video_path: str, 
        message: str, 
        details: Optional[dict] = None
    ) -> None:
        """Initialize transcription error.
        
        Args:
            video_path: Path to the video that failed to transcribe.
            message: Error message.
            details: Additional error details.
        """
        super().__init__(
            f"Failed to transcribe {video_path}: {message}", 
            details
        )
        self.video_path = video_path


class ModelNotFoundError(TranscriptionError):
    """Raised when specified model is not available."""
    
    def __init__(self, model_name: str, available_models: list[str]) -> None:
        """Initialize model not found error."""
        super().__init__(
            "",
            f"Model '{model_name}' not found",
            {
                "requested_model": model_name,
                "available_models": available_models
            }
        )
        self.model_name = model_name
        self.available_models = available_models


class StorageError(TranscriptionServiceError):
    """Raised when saving transcription fails."""
    
    def __init__(
        self, 
        filename: str, 
        message: str, 
        details: Optional[dict] = None
    ) -> None:
        """Initialize storage error.
        
        Args:
            filename: The filename that failed to save.
            message: Error message.
            details: Additional error details.
        """
        super().__init__(f"Failed to save {filename}: {message}", details)
        self.filename = filename


class CleanupError(TranscriptionServiceError):
    """Raised when cleanup fails (non-critical)."""
    
    def __init__(
        self, 
        path: str, 
        message: str, 
        details: Optional[dict] = None
    ) -> None:
        """Initialize cleanup error.
        
        Args:
            path: The path that failed to clean up.
            message: Error message.
            details: Additional error details.
        """
        super().__init__(f"Failed to cleanup {path}: {message}", details)
        self.path = path


class ConfigurationError(TranscriptionServiceError):
    """Raised when configuration is invalid."""
    
    def __init__(
        self, 
        parameter: str, 
        message: str, 
        details: Optional[dict] = None
    ) -> None:
        """Initialize configuration error.
        
        Args:
            parameter: The configuration parameter that is invalid.
            message: Error message.
            details: Additional error details.
        """
        super().__init__(
            f"Invalid configuration for {parameter}: {message}", 
            details
        )
        self.parameter = parameter