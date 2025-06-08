"""Domain models for video transcription service.

This module contains core business entities that represent
the data structures used throughout the application.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class VideoFile:
    """Represents a downloaded video file.
    
    Attributes:
        path: Absolute path to the video file.
        url: Original URL of the video.
        title: Video title extracted from metadata.
        duration: Video duration in seconds.
        size_bytes: File size in bytes.
        downloaded_at: Timestamp when the file was downloaded.
    
    Example:
        >>> video = VideoFile(
        ...     path=Path("/tmp/video.mp4"),
        ...     url="https://youtube.com/watch?v=123",
        ...     title="Sample Video",
        ...     duration=120.5,
        ...     size_bytes=1024000,
        ...     downloaded_at=datetime.now()
        ... )
    """
    path: Path
    url: str
    title: str
    duration: float
    size_bytes: int
    downloaded_at: datetime
    
    def __post_init__(self) -> None:
        """Validate video file attributes."""
        if not self.path.is_absolute():
            raise ValueError(f"Path must be absolute: {self.path}")
        if self.duration <= 0:
            raise ValueError(f"Duration must be positive: {self.duration}")
        if self.size_bytes <= 0:
            raise ValueError(f"Size must be positive: {self.size_bytes}")


@dataclass(frozen=True)
class TranscriptionSegment:
    """Represents a single segment of transcribed text.
    
    Attributes:
        text: The transcribed text content.
        start_time: Start time of the segment in seconds.
        end_time: End time of the segment in seconds.
        confidence: Confidence score of the transcription (0.0 to 1.0).
    """
    text: str
    start_time: float
    end_time: float
    confidence: float
    
    def __post_init__(self) -> None:
        """Validate segment attributes."""
        if self.start_time < 0:
            raise ValueError(f"Start time must be non-negative: {self.start_time}")
        if self.end_time <= self.start_time:
            raise ValueError(f"End time must be after start time: {self.end_time} <= {self.start_time}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1: {self.confidence}")


@dataclass(frozen=True)
class TranscriptionResult:
    """Represents the complete transcription result.
    
    Attributes:
        video_file: The source video file.
        segments: List of transcribed segments.
        full_text: Complete transcribed text.
        language: Detected or specified language code.
        processing_time: Time taken to transcribe in seconds.
        model_name: Name of the model used for transcription.
        created_at: Timestamp when transcription was created.
    
    Example:
        >>> result = TranscriptionResult(
        ...     video_file=video,
        ...     segments=[segment1, segment2],
        ...     full_text="Hello world",
        ...     language="en",
        ...     processing_time=5.2,
        ...     model_name="whisper-base",
        ...     created_at=datetime.now()
        ... )
    """
    video_file: VideoFile
    segments: list[TranscriptionSegment]
    full_text: str
    language: str
    processing_time: float
    model_name: str
    created_at: datetime
    
    def __post_init__(self) -> None:
        """Validate transcription result attributes."""
        if self.processing_time <= 0:
            raise ValueError(f"Processing time must be positive: {self.processing_time}")
        if not self.language:
            raise ValueError("Language code cannot be empty")
        if not self.model_name:
            raise ValueError("Model name cannot be empty")
    
    def get_text_with_timestamps(self) -> str:
        """Generate formatted text with timestamps.
        
        Returns:
            Formatted string with timestamps for each segment.
        
        Example:
            >>> result.get_text_with_timestamps()
            '[00:00:00] Hello world\\n[00:00:05] How are you?'
        """
        lines = []
        for segment in self.segments:
            timestamp = self._format_timestamp(segment.start_time)
            lines.append(f"[{timestamp}] {segment.text}")
        return "\n".join(lines)
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


@dataclass(frozen=True)
class TranscriptionOptions:
    """Configuration options for transcription.
    
    Attributes:
        model_size: Whisper model size to use.
        language: Specific language code or None for auto-detection.
        device: Device to use for inference ('cpu', 'cuda', etc).
        compute_type: Compute type for faster-whisper.
    """
    model_size: str = "base"
    language: Optional[str] = None
    device: str = "cpu"
    compute_type: str = "int8"
    
    def __post_init__(self) -> None:
        """Validate transcription options."""
        valid_models = {"tiny", "base", "small", "medium", "large", "large-v2", "large-v3"}
        if self.model_size not in valid_models:
            raise ValueError(f"Invalid model size: {self.model_size}. Must be one of {valid_models}")
        
        valid_devices = {"cpu", "cuda", "mps"}
        if self.device not in valid_devices:
            raise ValueError(f"Invalid device: {self.device}. Must be one of {valid_devices}")