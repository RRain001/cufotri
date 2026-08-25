"""V3 P7.5B controlled end-to-end orchestration boundary.

The pipeline calls existing typed module APIs in one explicit interval. It
does not contain transport, storage, biological, transfer, intake, or dose
equations, and it does not load external parameter databases or atmospheric
executables.  Forcing is interval-representative at the interval-start
timestamp; all emitted endpoint records use the interval-end timestamp.
"""

from .pipeline_runner import (
    V3PipelineConfig,
    V3PipelineParameters,
    V3PipelineRunner,
)
from .pipeline_state import V3PipelineLedger, V3SimulationState
from .validation import (
    PipelineInputError,
    PipelineSerializationError,
    PipelineStateError,
    V3PipelineValidationError,
)


__all__ = [
    "PipelineInputError",
    "PipelineSerializationError",
    "PipelineStateError",
    "V3PipelineConfig",
    "V3PipelineLedger",
    "V3PipelineParameters",
    "V3PipelineRunner",
    "V3PipelineValidationError",
    "V3SimulationState",
]
