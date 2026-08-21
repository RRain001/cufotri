"""V3-P3 plant/food-chain framework; no UFOTRI food-chain physics."""

from .balance import (
    FoodChainMassBalance,
    FoodChainMassBalanceError,
    MassBalanceError,
)
from .model import (
    FoodChainModel,
    FoodChainModelError,
    PlantModel,
    advance,
    harvest_product,
)
from .parameters import (
    DEFAULT_PARAMETER_NAMES,
    EXPECTED_PARAMETER_UNITS,
    FoodChainParameterError,
    FoodChainParameters,
)
from .physics import (
    FrameworkOnlyPhysics,
    PlantPhysics,
    PlantPhysicsResult,
    SyntheticTransferKernel,
    ZeroTransferKernel,
)
from .state import (
    CropCompartment,
    FoodChainStateError,
    HarvestProduct,
    LeafActivityInput,
    PlantInputs,
    PlantState,
    RootZoneActivityInput,
    receive_leaf_activity,
    receive_root_zone_activity,
)

# Descriptive aliases keep the plant-oriented contract discoverable while the
# package remains named for the broader future food-chain boundary.
FoodChainPhysicsResult = PlantPhysicsResult
PlantParameters = FoodChainParameters

__all__ = [
    "CropCompartment",
    "DEFAULT_PARAMETER_NAMES",
    "EXPECTED_PARAMETER_UNITS",
    "FoodChainMassBalance",
    "FoodChainMassBalanceError",
    "FoodChainModel",
    "FoodChainModelError",
    "FoodChainParameterError",
    "FoodChainParameters",
    "FoodChainPhysicsResult",
    "FoodChainStateError",
    "FrameworkOnlyPhysics",
    "HarvestProduct",
    "LeafActivityInput",
    "MassBalanceError",
    "PlantInputs",
    "PlantModel",
    "PlantParameters",
    "PlantPhysics",
    "PlantPhysicsResult",
    "PlantState",
    "RootZoneActivityInput",
    "SyntheticTransferKernel",
    "ZeroTransferKernel",
    "advance",
    "harvest_product",
    "receive_leaf_activity",
    "receive_root_zone_activity",
]
