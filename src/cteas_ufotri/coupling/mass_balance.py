from dataclasses import dataclass


@dataclass(frozen=True)
class MassBalance:
    initial_bq_m2: float
    external_input_bq_m2: float
    boundary_output_bq_m2: float
    decay_bq_m2: float
    final_bq_m2: float

    @property
    def residual_bq_m2(self) -> float:
        return (
            self.initial_bq_m2
            + self.external_input_bq_m2
            - self.boundary_output_bq_m2
            - self.decay_bq_m2
            - self.final_bq_m2
        )

    @property
    def relative_error(self) -> float:
        scale = max(
            abs(self.initial_bq_m2) + abs(self.external_input_bq_m2), 1.0e-30
        )
        return abs(self.residual_bq_m2) / scale
