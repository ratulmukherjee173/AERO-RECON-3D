"""
AERO RECON-3D — Abstract Base Pipeline Stage
"""
from abc import ABC, abstractmethod
from pathlib import Path
from ..core.logger import StageLogger


class PipelineStage(ABC):
    """All reconstruction stages inherit from this class."""

    def __init__(self, job_id: str, stage_dir: Path):
        self.job_id = job_id
        self.stage_dir = stage_dir
        self.stage_dir.mkdir(parents=True, exist_ok=True)
        self.logger = StageLogger(job_id, self.stage_name, stage_dir)

    @property
    @abstractmethod
    def stage_name(self) -> str:
        ...

    @abstractmethod
    def run(self, inputs: dict) -> dict:
        """
        Execute the stage.

        Parameters
        ----------
        inputs : dict
            Outputs from the preceding stage.

        Returns
        -------
        dict
            Outputs consumed by the next stage, plus 'summary' key
            containing the stage log dict.
        """
        ...
