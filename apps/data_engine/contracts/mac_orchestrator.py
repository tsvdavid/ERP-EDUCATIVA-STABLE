'''Contract for the MAC orchestrator.

The orchestrator coordinates the execution flow of the MAC pipeline. It does **not** contain
any concrete implementation – only the abstract interface that concrete classes must
implement.
''' 

from abc import ABC, abstractmethod
from typing import Any, Dict


class MacOrchestrator(ABC):
    """Abstract base class defining the orchestrator contract.

    Implementations are responsible for receiving input data, invoking the various
    engine components in the correct order, and returning a result dictionary.
    """

    @abstractmethod
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the MAC pipeline.

        Parameters
        ----------
        payload: Dict[str, Any]
            Input data required by the pipeline.

        Returns
        -------
        Dict[str, Any]
            Result of the processing.
        """
        raise NotImplementedError
