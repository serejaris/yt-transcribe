"""Domain interfaces for video transcription service.

This module defines protocols (interfaces) that must be implemented
by infrastructure components, following the Dependency Inversion Principle.
"""

from typing import Protocol, runtime_checkable
from pathlib import Path

from domain.models import VideoFile, TranscriptionResult, TranscriptionOptions


@runtime_checkable
class VideoDownloader(Protocol):
    """Protocol for downloading videos from various sources.
    
    Implementations should handle different video platforms
    and return a unified VideoFile object.
    """
    
    async def download(self, url: str, output_dir: Path) -> VideoFile:
        """Download a video from the given URL.
        
        Args:
            url: The URL of the video to download.
            output_dir: Directory where the video should be saved.
        
        Returns:
            VideoFile object representing the downloaded video.
        
        Raises:
            DownloadError: If the download fails for any reason.
            UnsupportedURLError: If the URL format is not supported.
        
        Example:
            >>> downloader = YouTubeDownloader()
            >>> video = await downloader.download(
            ...     "https://youtube.com/watch?v=123",
            ...     Path("/tmp")
            ... )
        """
        ...
    
    def is_supported(self, url: str) -> bool:
        """Check if the given URL is supported by this downloader.
        
        Args:
            url: The URL to check.
        
        Returns:
            True if the URL can be downloaded by this implementation.
        """
        ...


@runtime_checkable
class Transcriber(Protocol):
    """Protocol for transcribing video/audio files.
    
    Implementations should handle the actual transcription process
    using various speech-to-text engines.
    """
    
    async def transcribe(
        self, 
        video: VideoFile, 
        options: TranscriptionOptions
    ) -> TranscriptionResult:
        """Transcribe the given video file.
        
        Args:
            video: The video file to transcribe.
            options: Configuration options for transcription.
        
        Returns:
            TranscriptionResult containing the transcribed text and metadata.
        
        Raises:
            TranscriptionError: If transcription fails for any reason.
            ModelNotFoundError: If the specified model is not available.
        
        Example:
            >>> transcriber = WhisperTranscriber()
            >>> result = await transcriber.transcribe(
            ...     video,
            ...     TranscriptionOptions(model_size="base")
            ... )
        """
        ...
    
    def get_available_models(self) -> list[str]:
        """Get list of available transcription models.
        
        Returns:
            List of model names that can be used for transcription.
        """
        ...


@runtime_checkable
class FileStorage(Protocol):
    """Protocol for storing transcription results.
    
    Implementations can save results to various destinations
    like local filesystem, cloud storage, databases, etc.
    """
    
    async def save(
        self, 
        result: TranscriptionResult, 
        filename: str
    ) -> Path:
        """Save transcription result to storage.
        
        Args:
            result: The transcription result to save.
            filename: Name of the file to save (without extension).
        
        Returns:
            Path to the saved file.
        
        Raises:
            StorageError: If saving fails for any reason.
        
        Example:
            >>> storage = LocalFileStorage(Path("/output"))
            >>> path = await storage.save(result, "transcript")
        """
        ...
    
    def get_supported_formats(self) -> list[str]:
        """Get list of supported output formats.
        
        Returns:
            List of file extensions (e.g., ['.txt', '.srt', '.vtt']).
        """
        ...


@runtime_checkable
class VideoCleanup(Protocol):
    """Protocol for cleaning up temporary video files.
    
    Implementations should handle safe deletion of downloaded
    video files after processing.
    """
    
    async def cleanup(self, video: VideoFile) -> None:
        """Clean up the video file and any associated resources.
        
        Args:
            video: The video file to clean up.
        
        Raises:
            CleanupError: If cleanup fails but is non-critical.
        
        Example:
            >>> cleanup = TempFileCleanup()
            >>> await cleanup.cleanup(video)
        """
        ...


@runtime_checkable
class ProgressCallback(Protocol):
    """Protocol for reporting progress during long operations."""
    
    def __call__(
        self, 
        stage: str, 
        progress: float, 
        message: str = ""
    ) -> None:
        """Report progress update.
        
        Args:
            stage: Current operation stage (e.g., 'download', 'transcribe').
            progress: Progress percentage (0.0 to 100.0).
            message: Optional descriptive message.
        
        Example:
            >>> callback = ConsoleProgress()
            >>> callback("download", 45.5, "Downloading video...")
        """
        ...