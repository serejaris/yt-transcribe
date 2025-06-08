# Video Transcriber MVP

Elegant, minimal video transcription service with clean architecture.

## Features

- 🎥 Download videos from YouTube and other platforms
- 🎙️ High-quality transcription using OpenAI Whisper
- 🏗️ Clean Architecture with clear separation of concerns
- 🔌 Extensible design with dependency injection
- 🚀 Async/await for performance
- 📝 Type hints throughout (Python 3.10+)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python transcribe.py "https://youtube.com/watch?v=..." [output_name]
```

Example:
```bash
python transcribe.py "https://youtube.com/watch?v=dQw4w9WgXcQ" rick_roll
```

This will create `rick_roll.txt` in the current directory.

## Architecture

```
├── domain/               # Core business logic
│   ├── models.py        # Data models
│   ├── interfaces.py    # Protocol definitions
│   └── exceptions.py    # Custom exceptions
├── infrastructure/      # External service implementations
│   ├── youtube_downloader.py
│   └── whisper_transcriber.py
├── application/         # Service orchestration
│   └── service.py
└── transcribe.py       # CLI entry point
```

### Clean Architecture Principles

- **Domain Layer**: Pure business logic, no external dependencies
- **Infrastructure Layer**: Implements domain interfaces for external services
- **Application Layer**: Orchestrates the workflow using dependency injection
- **Presentation Layer**: Simple CLI interface

### Extensibility

Adding new features is straightforward:

- **New video source**: Implement `VideoDownloader` protocol
- **New transcriber**: Implement `Transcriber` protocol  
- **New output format**: Implement `FileStorage` protocol
- **GUI**: Create new entry point using existing services

## Advanced Usage

### Using Different Models

Modify `transcribe.py` to use different Whisper models:

```python
transcriber = WhisperTranscriber(
    model_size="large",  # tiny, base, small, medium, large
    device="cuda"        # cpu, cuda, mps
)
```

### Batch Processing

The service supports batch transcription:

```python
results = await service.process_batch(
    urls=["url1", "url2", "url3"],
    max_concurrent=3
)
```

## Error Handling

The service uses a comprehensive exception hierarchy:

- `DownloadError`: Video download failures
- `TranscriptionError`: Transcription failures
- `StorageError`: File saving failures
- `ConfigurationError`: Invalid settings

## Performance

- Downloads only audio track by default (faster)
- Supports GPU acceleration (CUDA/MPS)
- Async I/O for non-blocking operations
- Optional faster-whisper backend

## License

MIT