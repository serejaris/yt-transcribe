"""Rich-powered console progress callback.

Implements the generic ``ProgressCallback`` protocol using `rich` to provide
interactive progress bars and spinners for each pipeline stage.
"""
from __future__ import annotations

from typing import Dict

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from domain.interfaces import ProgressCallback


_ACTIVE_PROGRESS: Progress | None = None


class RichConsoleProgress(ProgressCallback):
    """A `rich` implementation of :class:`domain.interfaces.ProgressCallback`."""

    def __init__(self) -> None:
        self._console: Console = Console()
        # Create a Progress instance that auto-refreshes
        self._progress: Progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.fields[stage]}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self._console,
            transient=False,  # keep bars after completion so user can scroll back
        )
        self._tasks: Dict[str, int] = {}
        # Start the progress render loop
        self._progress.start()

        # Expose progress globally for bridging utilities
        global _ACTIVE_PROGRESS  # noqa: PLW0603 – intentional global
        _ACTIVE_PROGRESS = self._progress

    # ---------------------------------------------------------------------
    # ProgressCallback protocol implementation
    # ---------------------------------------------------------------------
    def __call__(self, stage: str, progress: float, message: str = "") -> None:  # type: ignore[override]
        """Report progress using `rich`.

        Args:
            stage: Pipeline stage, e.g. ``download``, ``transcribe``, ``save``.
            progress: Percentage (0–100).
            message: Optional human-readable status message.
        """
        if stage not in self._tasks:
            task_id = self._progress.add_task(
                description=message or stage.capitalize(),
                stage=stage.capitalize(),
                total=100,
            )
            self._tasks[stage] = task_id
        else:
            task_id = self._tasks[stage]

        # Update the task
        self._progress.update(
            task_id,
            completed=progress,
            description=message or stage.capitalize(),
        )

        # Optionally stop rendering when all tasks are done
        if progress >= 100:
            self._progress.stop_task(task_id)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def __del__(self) -> None:  # pragma: no cover – best-effort cleanup
        try:
            # Close progress to restore terminal if still active
            if self._progress.started and not self._progress.finished:
                self._progress.stop()
        except Exception:  # noqa: BLE001 – suppress all during interpreter shutdown
            pass

    # ------------------------------------------------------------------
    # Helpers for external integration (e.g., whisper tqdm bridge)
    # ------------------------------------------------------------------
    @property
    def progress(self) -> Progress:  # noqa: D401 – simple property
        """Return underlying Rich ``Progress`` instance."""
        return self._progress


# Utility for other modules
def get_active_rich_progress() -> Progress | None:  # noqa: D401
    """Return the most recently created Rich Progress instance, if any."""
    return _ACTIVE_PROGRESS
