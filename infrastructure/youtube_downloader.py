"""YouTube video downloader implementation using yt-dlp.

This module provides a concrete implementation of the VideoDownloader
protocol for downloading videos from YouTube and similar platforms.
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Callable, List
import logging

from infrastructure.rich_console_progress import get_active_rich_progress

import yt_dlp

from domain.interfaces import VideoDownloader
from domain.models import VideoFile
from domain.exceptions import DownloadError, UnsupportedURLError


logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Concrete implementation of VideoDownloader using yt-dlp.
    
    This downloader supports YouTube and many other video platforms
    that are compatible with yt-dlp.
    
    Attributes:
        audio_only: Whether to download only audio track.
        format_preference: Preferred video format for download.
        quiet: Whether to suppress yt-dlp output.
    """
    
    # Regex patterns for supported URLs
    YOUTUBE_PATTERNS = [
        re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/'),
        re.compile(r'(https?://)?(www\.)?vimeo\.com/'),
        re.compile(r'(https?://)?(www\.)?dailymotion\.com/'),
    ]
    
    def __init__(
        self,
        audio_only: bool = True,
        format_preference: str = "best",
        quiet: bool = True
    ) -> None:
        """Initialize YouTube downloader.
        
        Args:
            audio_only: Download only audio for faster processing.
            format_preference: yt-dlp format string.
            quiet: Suppress yt-dlp console output.
        """
        self.audio_only = audio_only
        self.format_preference = format_preference
        self.quiet = quiet
        self._ydl_opts = self._create_ydl_options()
        # Prepare progress integration (task id created lazily)
        self._rich_task_id: int | None = None
    
    def _create_ydl_options(self) -> dict[str, Any]:
        """Create yt-dlp options dictionary."""
        opts = {
            'quiet': self.quiet,
            'no_warnings': self.quiet,
            'extract_flat': False,
            'no_color': True,
            'no_check_certificate': True,
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'progress_hooks': [self._progress_hook],
        }
        
        if self.audio_only:
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': '%(title)s.%(ext)s',
            })
        else:
            opts.update({
                'format': self.format_preference,
                'outtmpl': '%(title)s.%(ext)s',
            })
        
        return opts
    
    def is_supported(self, url: str) -> bool:
        """Check if URL is supported by this downloader.
        
        Args:
            url: URL to check.
        
        Returns:
            True if URL matches supported patterns.
        """
        return any(pattern.search(url) for pattern in self.YOUTUBE_PATTERNS)
    
    async def download(self, url: str, output_dir: Path) -> VideoFile:
        """Download video from URL.
        
        Args:
            url: Video URL to download.
            output_dir: Directory to save the video.
        
        Returns:
            VideoFile object with download metadata.
        
        Raises:
            UnsupportedURLError: If URL is not supported.
            DownloadError: If download fails.
        """
        if not self.is_supported(url):
            raise UnsupportedURLError(url)
        
        # Ensure output directory exists
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Update output template with directory
        opts = self._ydl_opts.copy()
        opts['outtmpl'] = str(output_dir / opts['outtmpl'])
        
        try:
            # Run download in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            video_info = await loop.run_in_executor(
                None, 
                self._download_sync, 
                url, 
                opts
            )
            
            return self._create_video_file(url, video_info, output_dir)
            
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp download error: {e}")
            raise DownloadError(
                url, 
                str(e), 
                {"yt_dlp_error": type(e).__name__}
            )
        except Exception as e:
            logger.error(f"Unexpected download error: {e}")
            raise DownloadError(
                url,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def _download_sync(self, url: str, opts: dict[str, Any]) -> dict[str, Any]:
        """Synchronous download function for thread execution."""
        with yt_dlp.YoutubeDL(opts) as ydl:
            # Extract info first to get metadata
            info = ydl.extract_info(url, download=False)
            
            # Then download
            ydl.download([url])
            
            return info
    
    def _create_video_file(
        self, 
        url: str, 
        info: dict[str, Any], 
        output_dir: Path
    ) -> VideoFile:
        """Create VideoFile from yt-dlp info dictionary."""
        # Determine actual filename
        title = self._sanitize_filename(info.get('title', 'video'))
        ext = 'mp3' if self.audio_only else info.get('ext', 'mp4')
        filename = f"{title}.{ext}"
        filepath = output_dir / filename
        
        # Find the actual file (yt-dlp might modify the name)
        if not filepath.exists():
            # Try to find any audio/video files in the directory
            audio_extensions = ['*.mp3', '*.m4a', '*.wav', '*.ogg', '*.aac']
            video_extensions = ['*.mp4', '*.mkv', '*.webm', '*.avi', '*.mov']
            
            all_files = []
            for pattern in audio_extensions + video_extensions:
                all_files.extend(output_dir.glob(pattern))
            
            if all_files:
                # Sort by modification time and take the most recent
                filepath = max(all_files, key=lambda p: p.stat().st_mtime)
            else:
                # Try broader search with title prefix
                pattern = f"*{title[:20]}*"  # Use first 20 chars of title
                files = list(output_dir.glob(pattern))
                if files:
                    filepath = files[0]
                else:
                    raise DownloadError(
                        url,
                        f"Downloaded file not found: {filepath}",
                        {"expected_path": str(filepath), "temp_dir": str(output_dir)}
                    )
        
        return VideoFile(
            path=filepath.resolve(),
            url=url,
            title=info.get('title', 'Unknown'),
            duration=float(info.get('duration', 0)),
            size_bytes=filepath.stat().st_size,
            downloaded_at=datetime.now()
        )
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        max_length = 200
        if len(filename) > max_length:
            filename = filename[:max_length]
        
        return filename.strip()


    # ------------------------------------------------------------------
    # yt-dlp progress → Rich bridge
    # ------------------------------------------------------------------
    def _ensure_rich_task(self, total_bytes: int | None) -> None:
        from rich.progress import Progress  # local import

        if self._rich_task_id is not None:
            return

        progress = get_active_rich_progress()
        if progress is None or total_bytes is None:
            return  # nothing to do

        # Reuse existing task if it exists
        if self._rich_task_id is not None and self._rich_task_id in progress.task_ids:
            return

        self._rich_task_id = progress.add_task(
            "Downloading",
            total=total_bytes,
            stage="Download",
        )

    def _progress_hook(self, d: dict[str, Any]) -> None:  # callback from yt-dlp
        if d.get('status') == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes')
            self._ensure_rich_task(total_bytes)

            progress = get_active_rich_progress()
            if progress is not None and self._rich_task_id is not None and total_bytes:
                progress.update(self._rich_task_id, completed=downloaded)
        elif d.get('status') == 'finished':
            progress = get_active_rich_progress()
            if progress is not None and self._rich_task_id is not None:
                progress.update(self._rich_task_id, completed=progress.tasks[self._rich_task_id].total)


class CachedYouTubeDownloader(YouTubeDownloader):
    """YouTube downloader with caching support.
    
    This implementation caches downloaded videos to avoid
    re-downloading the same content.
    """
    
    def __init__(
        self,
        cache_dir: Path,
        audio_only: bool = True,
        format_preference: str = "best",
        quiet: bool = True
    ) -> None:
        """Initialize cached downloader.
        
        Args:
            cache_dir: Directory for caching videos.
            audio_only: Download only audio.
            format_preference: Video format preference.
            quiet: Suppress output.
        """
        super().__init__(audio_only, format_preference, quiet)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def download(self, url: str, output_dir: Path) -> VideoFile:
        """Download video with caching support."""
        # Check cache first
        cached_file = self._get_cached_file(url)
        if cached_file:
            logger.info(f"Using cached file for {url}")
            return cached_file
        
        # Download to cache directory
        video_file = await super().download(url, self.cache_dir)
        
        # Copy to output directory if different
        if output_dir != self.cache_dir:
            import shutil
            output_path = output_dir / video_file.path.name
            shutil.copy2(video_file.path, output_path)
            
            # Update video file with new path
            video_file = VideoFile(
                path=output_path.resolve(),
                url=video_file.url,
                title=video_file.title,
                duration=video_file.duration,
                size_bytes=video_file.size_bytes,
                downloaded_at=video_file.downloaded_at
            )
        
        return video_file
    
    def _get_cached_file(self, url: str) -> Optional[VideoFile]:
        """Check if URL is already cached."""
        # Simple cache lookup by URL hash
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Look for files with this hash in metadata
        metadata_file = self.cache_dir / f".{url_hash}.json"
        if metadata_file.exists():
            import json
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            video_path = Path(metadata['path'])
            if video_path.exists():
                return VideoFile(
                    path=video_path,
                    url=metadata['url'],
                    title=metadata['title'],
                    duration=metadata['duration'],
                    size_bytes=metadata['size_bytes'],
                    downloaded_at=datetime.fromisoformat(metadata['downloaded_at'])
                )
        
        return None