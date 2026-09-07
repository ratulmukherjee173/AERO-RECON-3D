"""
AERO RECON-3D — Structured Stage Logger
"""
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)


class StageLogger:
    """Logs stage execution with timing, metrics, and JSON summary output."""

    def __init__(self, job_id: str, stage_name: str, output_dir: Path):
        self.job_id = job_id
        self.stage_name = stage_name
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / "stage_log.json"
        self._log = logging.getLogger(f"aerorecon.{stage_name}")
        self._start: float = 0.0
        self._metrics: dict = {}

    def start(self) -> None:
        self._start = time.perf_counter()
        self._log.info(f">> Starting [{self.stage_name}] for job [{self.job_id}]")

    def info(self, msg: str) -> None:
        self._log.info(msg)

    def warning(self, msg: str) -> None:
        self._log.warning(msg)

    def error(self, msg: str) -> None:
        self._log.error(msg)

    def record(self, **kwargs) -> None:
        """Record key-value metrics."""
        self._metrics.update(kwargs)
        for k, v in kwargs.items():
            self._log.info(f"   {k}: {v}")

    def finish(self, success: bool = True) -> dict:
        elapsed = time.perf_counter() - self._start
        status = "SUCCESS" if success else "FAILED"
        summary = {
            "stage": self.stage_name,
            "job_id": self.job_id,
            "status": status,
            "elapsed_seconds": round(elapsed, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": self._metrics,
        }
        self._log.info(
            f"## [{self.stage_name}] {status} in {elapsed:.2f}s"
        )
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return summary
