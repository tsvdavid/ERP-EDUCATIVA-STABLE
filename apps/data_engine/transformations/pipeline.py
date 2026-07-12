# apps/data_engine/transformations/pipeline.py
"""Sequential TransformationPipeline composing processors and validators."""

import copy
import time
from typing import Any, Dict, List, Optional

from .base import BaseTransformation
from .contracts import TransformationContext
from .exceptions import PipelineException
from .models import (
    TransformationError,
    TransformationReport,
    TransformationResult,
    TransformationStatistics,
)


class TransformationPipeline:
    """Orchestrates sequential, composable execution of ETL transformations and validations."""

    def __init__(self, name: str = "default_pipeline") -> None:
        self.name = name
        self._transformations: List[BaseTransformation] = []
        self._history_snapshots: List[List[Dict[str, Any]]] = []

    @property
    def transformations(self) -> List[BaseTransformation]:
        """Return shallow copy of registered transformations list."""
        return list(self._transformations)

    def add(self, transformation: BaseTransformation) -> "TransformationPipeline":
        """Append a transformation or validator to the end of the pipeline. Supports method chaining."""
        if not isinstance(transformation, BaseTransformation):
            raise TypeError("Only BaseTransformation subclasses can be added to TransformationPipeline.")
        self._transformations.append(transformation)
        return self

    def remove(self, name: str) -> "TransformationPipeline":
        """Remove the first registered transformation matching the given name."""
        for i, t in enumerate(self._transformations):
            if t.name.lower() == name.lower():
                self._transformations.pop(i)
                return self
        raise PipelineException(f"Cannot remove: transformation '{name}' not found in pipeline.")

    def replace(self, name: str, new_transformation: BaseTransformation) -> "TransformationPipeline":
        """Replace an existing transformation matching `name` with `new_transformation`."""
        if not isinstance(new_transformation, BaseTransformation):
            raise TypeError("Replacement must be a BaseTransformation subclass.")
        for i, t in enumerate(self._transformations):
            if t.name.lower() == name.lower():
                self._transformations[i] = new_transformation
                return self
        raise PipelineException(f"Cannot replace: transformation '{name}' not found in pipeline.")

    def execute(
        self,
        records: List[Dict[str, Any]],
        context: Optional[TransformationContext] = None,
    ) -> TransformationReport:
        """Execute all transformations sequentially across all input records.

        Calculates duration (`execution_time_ms`), throughput (`throughput_records_per_sec`),
        and classifies results into accepted or rejected status.
        """
        start_time = time.perf_counter()
        ctx = context or TransformationContext()

        # Save initial state snapshot for rollback ability
        self._history_snapshots.append([dict(rec) for rec in records])

        results: List[TransformationResult] = []
        all_errors: List[TransformationError] = []
        accepted_count = 0
        rejected_count = 0

        for original_rec in records:
            current_rec = dict(original_rec)
            rec_errors: List[TransformationError] = []
            is_rejected = False

            for transformation in self._transformations:
                if not transformation.can_transform(current_rec):
                    continue

                # Run validations
                try:
                    errs = transformation.validate(current_rec)
                    if errs:
                        rec_errors.extend(errs)
                        all_errors.extend(errs)
                        is_rejected = True
                        break  # Stop transforming this rejected record
                except Exception as exc:
                    err = TransformationError(
                        error_code="VALIDATION_CRASH",
                        error_message=str(exc),
                        transformation_name=transformation.name,
                    )
                    rec_errors.append(err)
                    all_errors.append(err)
                    is_rejected = True
                    break

                # Apply transformation
                try:
                    current_rec = transformation.transform(current_rec)
                except Exception as exc:
                    err = TransformationError(
                        error_code="TRANSFORM_CRASH",
                        error_message=str(exc),
                        transformation_name=transformation.name,
                    )
                    rec_errors.append(err)
                    all_errors.append(err)
                    is_rejected = True
                    break

            if is_rejected:
                rejected_count += 1
                status = "REJECTED"
            elif current_rec != original_rec:
                accepted_count += 1
                status = "MODIFIED"
            else:
                accepted_count += 1
                status = "UNCHANGED"

            results.append(
                TransformationResult(
                    transformed_record=current_rec,
                    original_record=dict(original_rec),
                    errors=rec_errors,
                    status=status,
                )
            )

        end_time = time.perf_counter()
        exec_ms = (end_time - start_time) * 1000.0
        exec_sec = end_time - start_time
        total_recs = len(records)
        throughput = (total_recs / exec_sec) if exec_sec > 0 and total_recs > 0 else 0.0

        stats = TransformationStatistics(
            records_processed=total_recs,
            records_accepted=accepted_count,
            records_rejected=rejected_count,
            execution_time_ms=exec_ms,
            throughput_records_per_sec=throughput,
            error_count=len(all_errors),
        )

        return TransformationReport(
            results=results,
            statistics=stats,
            errors=all_errors,
            success=len(all_errors) == 0,
        )

    def rollback(self, records: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Revert records to the initial snapshot captured prior to pipeline execution."""
        if self._history_snapshots:
            return [dict(rec) for rec in self._history_snapshots.pop()]
        if records is not None:
            return [dict(rec) for rec in records]
        raise PipelineException("No history snapshot available to execute rollback.")

    def clone(self) -> "TransformationPipeline":
        """Create a deep clone of this pipeline and its registered transformations."""
        new_pipeline = TransformationPipeline(name=f"{self.name}_clone")
        for t in self._transformations:
            new_pipeline.add(copy.deepcopy(t))
        return new_pipeline
