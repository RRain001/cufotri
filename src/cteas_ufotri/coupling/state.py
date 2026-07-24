from dataclasses import dataclass


@dataclass(frozen=True)
class State:
    soil_water_m: float
    soil_hto_bq_m2: float = 0.0
    plant_tfwt_bq_m2: float = 0.0
    plant_obt_bq_m2: float = 0.0
    edible_tfwt_bq_m2: float = 0.0
    edible_obt_bq_m2: float = 0.0
    harvested_hto_bq_m2: float = 0.0
    harvested_obt_bq_m2: float = 0.0
    cut_plant_hto_bq_m2: float = 0.0
    cut_plant_obt_bq_m2: float = 0.0

    @property
    def total_hto_bq_m2(self) -> float:
        return (
            self.soil_hto_bq_m2
            + self.plant_tfwt_bq_m2
            + self.plant_obt_bq_m2
            + self.edible_tfwt_bq_m2
            + self.edible_obt_bq_m2
        )
