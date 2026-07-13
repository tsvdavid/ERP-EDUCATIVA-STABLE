# apps/data_engine/pipeline/contracts.py
"""Public protocols and interfaces for pipeline orchestration and execution."""

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class PipelineBuilderContract(Protocol):
    """Protocol for classes constructing PipelineRuntime objects from definitions."""

    def build(self, definition: Any) -> Any:
        """Build an executable PipelineRuntime from a PipelineDefinition."""
        ...


@runtime_checkable
class PipelineExecutorContract(Protocol):
    """Protocol for executing a built PipelineRuntime in the MAC system."""

    def execute(
        self,
        runtime: Any,
        tenant_id: str,
        user_id: str,
        run_id: Optional[str] = None,
        is_dry_run: bool = False,
        step_executor: Optional[Any] = None,
    ) -> Any:
        """Execute the pipeline steps in order and generate an execution report."""
        ...
