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
    root_tfwt_bq_m2: float = 0.0
    root_obt_bq_m2: float = 0.0

    def __post_init__(self) -> None:
        if min(
            self.plant_tfwt_bq_m2,
            self.plant_obt_bq_m2,
            self.root_tfwt_bq_m2,
            self.root_obt_bq_m2,
        ) < 0.0:
            raise ValueError("Plant root/shoot inventories must be non-negative")
        if self.root_tfwt_bq_m2 > self.plant_tfwt_bq_m2:
            raise ValueError("Root TFWT cannot exceed total plant TFWT")
        if self.root_obt_bq_m2 > self.plant_obt_bq_m2:
            raise ValueError("Root OBT cannot exceed total plant OBT")

    @property
    def shoot_tfwt_bq_m2(self) -> float:
        return max(self.plant_tfwt_bq_m2 - self.root_tfwt_bq_m2, 0.0)

    @property
    def shoot_obt_bq_m2(self) -> float:
        return max(self.plant_obt_bq_m2 - self.root_obt_bq_m2, 0.0)

    @property
    def total_hto_bq_m2(self) -> float:
        return (
            self.soil_hto_bq_m2
            + self.plant_tfwt_bq_m2
            + self.plant_obt_bq_m2
            + self.edible_tfwt_bq_m2
            + self.edible_obt_bq_m2
        )
