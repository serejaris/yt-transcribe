"""Application service layer for video transcription.

This module contains the main service that orchestrates the transcription
process, coordinating between domain interfaces and infrastructure.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional
import logging

from domain.interfaces import (
    VideoDownloader,
    Transcriber,
    FileStorage,
    VideoCleanup,
    ProgressCallback
)
from domain.models import TranscriptionOptions, TranscriptionResult, VideoFile
from domain.exceptions import TranscriptionServiceError, CleanupError


logger = logging.getLogger(__name__)


class TranscriptionService:
    """Main service for video transcription workflow.
    
    This service orchestrates the complete transcription process:
    downloading videos, transcribing them, and saving results.
    
    Attributes:
        downloader: Video downloader implementation.
        transcriber: Transcription engine implementation.
        storage: Optional storage implementation.
        cleanup: Optional cleanup implementation.
        temp_dir: Temporary directory for downloads.
    """
    
    def __init__(
        self,
        downloader: VideoDownloader,
        transcriber: Transcriber,
        storage: Optional[FileStorage] = None,
        cleanup: Optional[VideoCleanup] = None,
        temp_dir: Optional[Path] = None
    ) -> None:
        """Initialize transcription service.
        
        Args:
            downloader: Video downloader to use.
            transcriber: Transcriber to use.
            storage: Optional storage for results.
            cleanup: Optional cleanup handler.
            temp_dir: Temporary directory for downloads.
        """
        self._downloader = downloader
        self._transcriber = transcriber
        self._storage = storage
        self._cleanup = cleanup
        self._temp_dir = Path(temp_dir) if temp_dir else None
        
        logger.info("Initialized TranscriptionService")
    
    async def process_url(
        self,
        url: str,
        options: Optional[TranscriptionOptions] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> TranscriptionResult:
        """Process a video URL through complete transcription pipeline.
        
        Args:
            url: Video URL to process.
            options: Transcription options.
            progress_callback: Optional progress reporting callback.
        
        Returns:
            TranscriptionResult with transcribed content.
        
        Raises:
            TranscriptionServiceError: If any step fails.
        """
        options = options or TranscriptionOptions()
        video_file = None
        
        try:
            # Create temporary directory
            temp_dir = self._get_temp_directory()
            
            # Download video
            if progress_callback:
                progress_callback("download", 0.0, "Starting download...")
            
            video_file = await self._downloader.download(url, temp_dir)
            
            if progress_callback:
                progress_callback("download", 100.0, "Download complete")
            
            logger.info(f"Downloaded video: {video_file.title}")
            
            # Transcribe video
            if progress_callback:
                progress_callback("transcribe", 0.0, "Starting transcription...")
            
            result = await self._transcriber.transcribe(video_file, options)
            
            if progress_callback:
                progress_callback("transcribe", 100.0, "Transcription complete")
            
            logger.info(
                f"Transcribed video: {len(result.segments)} segments, "
                f"{result.processing_time:.1f}s processing time"
            )
            
            return result
            
        finally:
            # Clean up video file
            if video_file and self._cleanup:
                try:
                    await self._cleanup.cleanup(video_file)
                except CleanupError as e:
                    logger.warning(f"Cleanup failed: {e}")
    
    async def process_url_and_save(
        self,
        url: str,
        output_filename: str,
        options: Optional[TranscriptionOptions] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> Path:
        """Process URL and save transcription to file.
        
        Args:
            url: Video URL to process.
            output_filename: Name for output file.
            options: Transcription options.
            progress_callback: Progress callback.
        
        Returns:
            Path to saved transcription file.
        
        Raises:
            TranscriptionServiceError: If processing fails.
            StorageError: If saving fails.
        """
        # Process URL
        result = await self.process_url(url, options, progress_callback)
        
        # Save result
        if self._storage:
            if progress_callback:
                progress_callback("save", 0.0, "Saving transcription...")
            
            output_path = await self._storage.save(result, output_filename)
            
            if progress_callback:
                progress_callback("save", 100.0, "Save complete")
            
            logger.info(f"Saved transcription to: {output_path}")
            return output_path
        else:
            # Default: save to current directory as text
            output_path = Path(f"{output_filename}.txt")
            output_path.write_text(result.full_text, encoding='utf-8')
            
            if progress_callback:
                progress_callback("save", 100.0, "Save complete")
            
            return output_path
    
    def _get_temp_directory(self) -> Path:
        """Get or create temporary directory."""
        if self._temp_dir:
            self._temp_dir.mkdir(parents=True, exist_ok=True)
            return self._temp_dir
        else:
            return Path(tempfile.mkdtemp(prefix="transcribe_"))
    
    async def process_batch(
        self,
        urls: list[str],
        options: Optional[TranscriptionOptions] = None,
        max_concurrent: int = 3
    ) -> list[TranscriptionResult]:
        """Process multiple URLs concurrently.
        
        Args:
            urls: List of video URLs.
            options: Transcription options for all videos.
            max_concurrent: Maximum concurrent operations.
        
        Returns:
            List of transcription results.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_limit(url: str) -> TranscriptionResult:
            async with semaphore:
                return await self.process_url(url, options)
        
        tasks = [process_with_limit(url) for url in urls]
        return await asyncio.gather(*tasks)


class SimpleFileStorage:
    """Simple file storage implementation.
    
    This storage saves transcriptions as plain text files
    in a specified directory.
    """
    
    def __init__(self, output_dir: Path) -> None:
        """Initialize file storage.
        
        Args:
            output_dir: Directory for saving files.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def save(
        self,
        result: TranscriptionResult,
        filename: str
    ) -> Path:
        """Save transcription as text file."""
        # Ensure .txt extension
        if not filename.endswith('.txt'):
            filename = f"{filename}.txt"
        
        output_path = self.output_dir / filename
        
        # Write content
        content = self._format_content(result)
        output_path.write_text(content, encoding='utf-8')
        
        return output_path
    
    def get_supported_formats(self) -> list[str]:
        """Get supported formats."""
        return ['.txt']
    
    def _format_content(self, result: TranscriptionResult) -> str:
        """Format transcription result as text."""
        lines = [
            f"Transcription of: {result.video_file.title}",
            f"URL: {result.video_file.url}",
            f"Duration: {result.video_file.duration:.1f} seconds",
            f"Language: {result.language}",
            f"Model: {result.model_name}",
            f"Processing time: {result.processing_time:.1f} seconds",
            "",
            "=" * 80,
            "",
            result.full_text
        ]
        
        return "\n".join(lines)


class TempFileCleanup:
    """Simple cleanup implementation for temporary files."""
    
    async def cleanup(self, video: VideoFile) -> None:
        """Remove video file if it exists."""
        try:
            if video.path.exists():
                video.path.unlink()
                logger.debug(f"Cleaned up: {video.path}")
        except Exception as e:
            raise CleanupError(
                str(video.path),
                f"Failed to delete file: {e}",
                {"error": str(e)}
            )


class ConsoleProgress:
    """Console progress callback implementation."""
    
    def __call__(
        self,
        stage: str,
        progress: float,
        message: str = ""
    ) -> None:
        """Print progress to console."""
        bar_length = 30
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"\r{stage.capitalize()}: [{bar}] {progress:.1f}% {message}", end="")
        
        if progress >= 100:
            print()  # New line when complete