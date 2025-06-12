#!/usr/bin/env python3
"""Video transcription CLI.

Simple command-line interface for transcribing videos from URLs.
Usage: python transcribe.py "https://youtube.com/watch?v=..."
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Optional

from domain import TranscriptionOptions
from infrastructure import YouTubeDownloader, WhisperTranscriber, RichConsoleProgress
from application import (
    TranscriptionService,
    SimpleFileStorage,
    TempFileCleanup,
)
from application.service import SimpleFileStorage as Storage, SimpleConsoleProgress as _FallbackProgress  # For accessing formatter


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suppress verbose libraries
    logging.getLogger('yt_dlp').setLevel(logging.WARNING)
    logging.getLogger('whisper').setLevel(logging.WARNING)


async def main(url: str, output_name: Optional[str] = None) -> None:
    """Main transcription workflow.
    
    Args:
        url: Video URL to transcribe.
        output_name: Optional output filename.
    """
    # Configure components with dependency injection
    downloader = YouTubeDownloader(
        audio_only=True,
        format_preference="best",
        quiet=True
    )
    
    transcriber = WhisperTranscriber(
        model_size="small",  # Use small model for good balance
        device=None  # Auto-detect
    )
    
    transcripts_dir = Path.cwd() / "transcripts"
    storage = SimpleFileStorage(transcripts_dir)
    cleanup = TempFileCleanup()
    # Prefer rich progress if available, else fallback to simple
    try:
        progress = RichConsoleProgress()  # type: ignore[assignment]
    except Exception:
        progress = _FallbackProgress()  # noqa: S110
    
    # Create service with injected dependencies
    service = TranscriptionService(
        downloader=downloader,
        transcriber=transcriber,
        storage=storage,
        cleanup=cleanup
    )
    
    try:
        print(f"Starting transcription of: {url}")
        
        # First process to get the result
        result = await service.process_url(
            url=url,
            options=TranscriptionOptions(
                model_size="small",
                device="cpu"
            ),
            progress_callback=progress
        )
        
        # Use video title as filename if not specified
        if not output_name:
            # Sanitize title for filename
            title = result.video_file.title
            # Remove invalid filename characters
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                title = title.replace(char, '_')
            # Limit length
            output_name = title[:100] if len(title) > 100 else title
        
        # Save with determined filename
        if progress:
            progress("save", 0.0, "Saving transcription...")
        
        output_path = await storage.save(result, output_name)
        
        if progress:
            progress("save", 100.0, "Save complete")
        
        print(f"\n✓ Transcription saved to: {output_path}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def cli() -> None:
    """Command-line interface entry point."""
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <video_url> [output_name]")
        print("Example: python transcribe.py \"https://youtube.com/watch?v=...\" my_video")
        sys.exit(1)
    
    url = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Setup logging
    setup_logging(verbose=False)
    
    # Run async main
    asyncio.run(main(url, output_name))


if __name__ == "__main__":
    cli()