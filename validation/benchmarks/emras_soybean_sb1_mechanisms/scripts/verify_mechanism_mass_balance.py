from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def summarize_mass_balance(
    frame: pd.DataFrame,
    protocol: dict[str, Any],
) -> dict[str, float | int | bool]:
    formal = frame["formal_mass_closure_abs_bq_m2"].to_numpy(float)
    internal = frame["internal_transfer_residual_abs_bq_m2"].to_numpy(float)
    numeric = frame.select_dtypes(include=[np.number])
    inventory = numeric.filter(regex="_inventory_bq_m2$")
    concentration = numeric.filter(regex="_bq_l_")
    result = {
        "nan_count": int(numeric.isna().sum().sum()),
        "inf_count": int(np.isinf(numeric.to_numpy()).sum()),
        "negative_inventory_count": int((inventory.to_numpy() < -1.0e-12).sum()),
        "negative_concentration_count": int(
            (concentration.to_numpy() < -1.0e-12).sum()
        ),
        "maximum_formal_mass_closure_abs_bq_m2": float(np.max(formal)),
        "maximum_internal_transfer_residual_abs_bq_m2": float(
            np.max(internal)
        ),
    }
    result["mass_balance_pass"] = bool(
        result["maximum_formal_mass_closure_abs_bq_m2"]
        <= float(
            protocol["success_criteria"][
                "mass_closure_absolute_tolerance_bq_m2"
            ]
        )
        and result["maximum_internal_transfer_residual_abs_bq_m2"]
        <= float(
            protocol["success_criteria"][
                "internal_transfer_absolute_tolerance_bq_m2"
            ]
        )
        and result["inf_count"] == 0
        and result["negative_inventory_count"] == 0
        and result["negative_concentration_count"] == 0
    )
    return result
