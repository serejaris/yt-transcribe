"""Whisper-based transcription implementation.

This module provides a concrete implementation of the Transcriber
protocol using OpenAI's Whisper model for speech-to-text conversion.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import logging
from functools import wraps

import whisper
import torch

from domain.interfaces import Transcriber
from domain.models import (
    VideoFile, 
    TranscriptionResult, 
    TranscriptionSegment,
    TranscriptionOptions
)
from domain.exceptions import TranscriptionError, ModelNotFoundError


logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Concrete implementation of Transcriber using OpenAI Whisper.
    
    This transcriber uses the Whisper model for high-quality
    speech-to-text transcription with automatic language detection.
    
    Attributes:
        model: Loaded Whisper model instance.
        device: Device for model inference.
        compute_type: Computation type for optimization.
    """
    
    AVAILABLE_MODELS = [
        "tiny", "base", "small", "medium", 
        "large", "large-v2", "large-v3"
    ]
    
    def __init__(
        self,
        model_size: str = "base",
        device: Optional[str] = None,
        download_root: Optional[Path] = None
    ) -> None:
        """Initialize Whisper transcriber.
        
        Args:
            model_size: Size of the Whisper model to use.
            device: Device for inference (None for auto-detection).
            download_root: Directory for model downloads.
        
        Raises:
            ModelNotFoundError: If model size is invalid.
        """
        if model_size not in self.AVAILABLE_MODELS:
            raise ModelNotFoundError(model_size, self.AVAILABLE_MODELS)
        
        self.model_size = model_size
        self.device = device or self._detect_device()
        self.download_root = download_root
        self._model: Optional[whisper.Whisper] = None
        
        logger.info(
            f"Initialized WhisperTranscriber: "
            f"model={model_size}, device={self.device}"
        )
    
    def _detect_device(self) -> str:
        """Detect best available device for inference."""
        if torch.cuda.is_available():
            return "cuda"
        # Disable MPS for now due to compatibility issues
        # elif torch.backends.mps.is_available():
        #     return "mps"
        else:
            return "cpu"
    
    def _load_model(self) -> whisper.Whisper:
        """Load Whisper model lazily."""
        # Ensure tqdm progress bars are silenced to avoid conflicting CLI output
        self._patch_whisper_tqdm()
        if self._model is None:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self._model = whisper.load_model(
                self.model_size,
                device=self.device,
                download_root=str(self.download_root) if self.download_root else None
            )
        return self._model
    
    _tqdm_patched: bool = False

    def _patch_whisper_tqdm(self) -> None:
        """Patch Whisper's internal tqdm to disable native progress bars.

        This prevents stdout clutter when Rich progress bars are used.
        The patch is idempotent and affects only the current process.
        """
        if self.__class__._tqdm_patched:
            return

        try:
            import whisper.utils as wutils  # type: ignore
            from tqdm import tqdm as _orig_tqdm  # noqa: N811 (alias)

            # Try to integrate with Rich
            from infrastructure.rich_console_progress import (
                get_active_rich_progress,
            )

            rich_progress = get_active_rich_progress()

            if rich_progress is None:
                # Fallback: silent wrapper (no Rich running)
                def _silent(*a, **kw):  # type: ignore[override]
                    kw.setdefault("disable", True)
                    return _orig_tqdm(*a, **kw)

                wutils.tqdm = _silent  # type: ignore[assignment]
                logger.debug("Patched whisper tqdm -> silent")
            else:
                # Create a tqdm subclass that forwards updates to Rich
                def _rich_tqdm(*a, **kw):  # type: ignore[override]
                    total = kw.get("total") or (a[0].total if a else None)

                    if not hasattr(_rich_tqdm, "_task_id"):
                        _rich_tqdm._task_id = rich_progress.add_task(
                            "Transcribe", total=100.0, start=False, stage="Transcribe"
                        )
                    task_id = _rich_tqdm._task_id  # type: ignore[attr-defined]

                    class _Bridge(_orig_tqdm):
                        def update(self, n=1):  # type: ignore[override]
                            super().update(n)
                            if total:
                                pct = 100 * self.n / total
                                rich_progress.update(task_id, completed=pct)

                    kw["disable"] = True  # fully suppress tqdm output
                    bar = _Bridge(*a, **kw)
                    rich_progress.start_task(task_id)
                    return bar

                wutils.tqdm = _rich_tqdm  # type: ignore[assignment]
                logger.debug("Patched whisper tqdm -> rich bridge")
            self.__class__._tqdm_patched = True
        except Exception as exc:  # pragma: no cover – best-effort patch
            logger.debug(f"Could not patch whisper tqdm: {exc}")
    
    def get_available_models(self) -> list[str]:
        """Get list of available Whisper models."""
        return self.AVAILABLE_MODELS.copy()
    
    async def transcribe(
        self,
        video: VideoFile,
        options: TranscriptionOptions
    ) -> TranscriptionResult:
        """Transcribe video file using Whisper.
        
        Args:
            video: Video file to transcribe.
            options: Transcription options.
        
        Returns:
            TranscriptionResult with transcribed text and segments.
        
        Raises:
            TranscriptionError: If transcription fails.
        """
        start_time = time.time()
        
        try:
            # Load model if needed
            model = self._load_model()
            
            # Prepare transcription options
            whisper_options = self._prepare_options(options)
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                model,
                str(video.path),
                whisper_options
            )
            
            # Convert to domain model
            processing_time = time.time() - start_time
            return self._create_transcription_result(
                video,
                result,
                options,
                processing_time
            )
            
        except FileNotFoundError:
            raise TranscriptionError(
                str(video.path),
                "Video file not found",
                {"path": str(video.path)}
            )
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(
                str(video.path),
                f"Transcription failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def _prepare_options(self, options: TranscriptionOptions) -> dict[str, Any]:
        """Prepare options for Whisper transcribe call."""
        whisper_opts = {
            "verbose": False,
            "task": "transcribe",
            "word_timestamps": True,
        }
        
        if options.language:
            whisper_opts["language"] = options.language
        
        # Add device-specific options
        if self.device == "cuda":
            whisper_opts["fp16"] = True
        else:
            whisper_opts["fp16"] = False
        
        return whisper_opts
    
    def _transcribe_sync(
        self,
        model: whisper.Whisper,
        audio_path: str,
        options: dict[str, Any]
    ) -> dict[str, Any]:
        """Synchronous transcription for thread execution."""
        return model.transcribe(audio_path, **options)
    
    def _create_transcription_result(
        self,
        video: VideoFile,
        whisper_result: dict[str, Any],
        options: TranscriptionOptions,
        processing_time: float
    ) -> TranscriptionResult:
        """Convert Whisper result to domain model."""
        # Extract segments
        segments = []
        for segment in whisper_result.get("segments", []):
            segments.append(TranscriptionSegment(
                text=segment["text"].strip(),
                start_time=segment["start"],
                end_time=segment["end"],
                confidence=segment.get("confidence", 0.95)
            ))
        
        # Get full text
        full_text = whisper_result.get("text", "").strip()
        
        # Get detected language
        language = whisper_result.get("language", options.language or "unknown")
        
        return TranscriptionResult(
            video_file=video,
            segments=segments,
            full_text=full_text,
            language=language,
            processing_time=processing_time,
            model_name=f"whisper-{self.model_size}",
            created_at=datetime.now()
        )


class FasterWhisperTranscriber(WhisperTranscriber):
    """Optimized Whisper transcriber using faster-whisper.
    
    This implementation uses CTranslate2 for faster inference
    with lower memory usage compared to the original Whisper.
    """
    
    def __init__(
        self,
        model_size: str = "base",
        device: Optional[str] = None,
        compute_type: str = "int8",
        download_root: Optional[Path] = None
    ) -> None:
        """Initialize faster-whisper transcriber.
        
        Args:
            model_size: Size of model to use.
            device: Device for inference.
            compute_type: Computation type (int8, float16, float32).
            download_root: Directory for model downloads.
        """
        super().__init__(model_size, device, download_root)
        self.compute_type = compute_type
        self._model = None
    
    def _load_model(self) -> Any:
        """Load faster-whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                logger.warning(
                    "faster-whisper not installed, falling back to standard Whisper"
                )
                return super()._load_model()
            
            logger.info(f"Loading faster-whisper model: {self.model_size}")
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(self.download_root) if self.download_root else None
            )
        
        return self._model
    
    def _transcribe_sync(
        self,
        model: Any,
        audio_path: str,
        options: dict[str, Any]
    ) -> dict[str, Any]:
        """Synchronous transcription using faster-whisper."""
        # Check if this is a faster-whisper model
        if hasattr(model, 'transcribe') and model.__class__.__name__ == 'WhisperModel':
            # faster-whisper transcribe
            segments, info = model.transcribe(
                audio_path,
                language=options.get("language"),
                task=options.get("task", "transcribe"),
                beam_size=5,
                best_of=5,
                patience=1,
                length_penalty=1,
                temperature=0,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=400,
                    window_size_samples=1024,
                    threshold=0.5
                )
            )
            
            # Convert to standard format
            segment_list = []
            full_text_parts = []
            
            for segment in segments:
                segment_dict = {
                    "text": segment.text,
                    "start": segment.start,
                    "end": segment.end,
                    "confidence": segment.avg_log_prob,
                }
                segment_list.append(segment_dict)
                full_text_parts.append(segment.text)
            
            return {
                "segments": segment_list,
                "text": " ".join(full_text_parts),
                "language": info.language,
            }
        else:
            # Fall back to standard Whisper
            return super()._transcribe_sync(model, audio_path, options)


class BatchWhisperTranscriber(WhisperTranscriber):
    """Whisper transcriber with batch processing support.
    
    This implementation can process multiple videos in parallel
    for improved throughput.
    """
    
    def __init__(
        self,
        model_size: str = "base",
        device: Optional[str] = None,
        batch_size: int = 4,
        download_root: Optional[Path] = None
    ) -> None:
        """Initialize batch transcriber.
        
        Args:
            model_size: Model size to use.
            device: Device for inference.
            batch_size: Number of concurrent transcriptions.
            download_root: Model download directory.
        """
        super().__init__(model_size, device, download_root)
        self.batch_size = batch_size
        self._semaphore = asyncio.Semaphore(batch_size)
    
    async def transcribe(
        self,
        video: VideoFile,
        options: TranscriptionOptions
    ) -> TranscriptionResult:
        """Transcribe with concurrency limiting."""
        async with self._semaphore:
            return await super().transcribe(video, options)
    
    async def transcribe_batch(
        self,
        videos: list[VideoFile],
        options: TranscriptionOptions
    ) -> list[TranscriptionResult]:
        """Transcribe multiple videos in parallel.
        
        Args:
            videos: List of videos to transcribe.
            options: Transcription options for all videos.
        
        Returns:
            List of transcription results.
        """
        tasks = [
            self.transcribe(video, options)
            for video in videos
        ]
        
        return await asyncio.gather(*tasks)