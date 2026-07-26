"""Derive a holdout verdict from frozen preregistered metric rules."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import math
from pathlib import Path
from typing import Any, Mapping


ALLOWED_COMPARATORS = {
    "LT",
    "LE",
    "GT",
    "GE",
    "BETWEEN_CLOSED",
    "ABS_LE",
}


@dataclass(frozen=True)
class MetricEvaluation:
    metric_id: str
    status: str
    comparator: str
    threshold: float | tuple[float, float]
    expected_unit: str
    actual_unit: str | None
    value: float | None
    detail: str


@dataclass(frozen=True)
class HoldoutEvaluation:
    required_metric_count: int
    passed_metric_count: int
    failed_metric_count: int
    missing_metric_count: int
    metric_results: tuple[MetricEvaluation, ...]
    derived_verdict: str

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["metric_results"] = [
            asdict(result) for result in self.metric_results
        ]
        return value


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _threshold(rule: Mapping[str, Any]) -> float | tuple[float, float]:
    comparator = rule.get("comparator")
    value = rule.get("threshold")
    if comparator == "BETWEEN_CLOSED":
        if (
            not isinstance(value, list)
            or len(value) != 2
            or any(_finite_number(item) is None for item in value)
        ):
            raise ValueError("BETWEEN_CLOSED requires two finite thresholds")
        lower, upper = (float(value[0]), float(value[1]))
        if lower > upper:
            raise ValueError("BETWEEN_CLOSED lower threshold exceeds upper")
        return lower, upper
    number = _finite_number(value)
    if number is None:
        raise ValueError(f"{comparator} requires one finite threshold")
    if comparator == "ABS_LE" and number < 0.0:
        raise ValueError("ABS_LE threshold must be non-negative")
    return number


def _compare(
    value: float,
    comparator: str,
    threshold: float | tuple[float, float],
) -> bool:
    if comparator == "LT":
        return value < float(threshold)
    if comparator == "LE":
        return value <= float(threshold)
    if comparator == "GT":
        return value > float(threshold)
    if comparator == "GE":
        return value >= float(threshold)
    if comparator == "ABS_LE":
        return abs(value) <= float(threshold)
    if comparator == "BETWEEN_CLOSED":
        lower, upper = threshold
        return lower <= value <= upper
    raise ValueError(f"unsupported metric comparator: {comparator}")


def derive_holdout_verdict(
    preregistration: Mapping[str, Any],
    holdout_metrics: Any,
) -> HoldoutEvaluation:
    """Evaluate every required metric without dynamic expressions or eval."""

    rules = preregistration.get("primary_metrics")
    if not isinstance(rules, list) or not rules:
        raise ValueError("preregistration primary_metrics must be non-empty")
    if not isinstance(holdout_metrics, list):
        raise ValueError("holdout metrics must be a list")
    provided: dict[str, Mapping[str, Any]] = {}
    for metric in holdout_metrics:
        if not isinstance(metric, Mapping):
            raise ValueError("holdout metric must be a mapping")
        metric_id = metric.get("metric_id")
        if not isinstance(metric_id, str) or not metric_id:
            raise ValueError("holdout metric_id must be non-empty")
        if metric_id in provided:
            raise ValueError(f"duplicate holdout metric: {metric_id}")
        provided[metric_id] = metric

    results: list[MetricEvaluation] = []
    failed = 0
    missing = 0
    inconclusive_missing = False
    required_count = 0
    seen_rules: set[str] = set()
    for rule in rules:
        if not isinstance(rule, Mapping):
            raise ValueError("primary metric rule must be a mapping")
        metric_id = rule.get("metric_id")
        if not isinstance(metric_id, str) or not metric_id:
            raise ValueError("primary metric rule id must be non-empty")
        if metric_id in seen_rules:
            raise ValueError(f"duplicate primary metric rule: {metric_id}")
        seen_rules.add(metric_id)
        if rule.get("required") is not True:
            continue
        required_count += 1
        comparator = str(rule.get("comparator", ""))
        if comparator not in ALLOWED_COMPARATORS:
            raise ValueError(f"unsupported metric comparator: {comparator}")
        expected_unit = str(rule.get("value_unit", ""))
        if not expected_unit:
            raise ValueError(f"metric {metric_id} has no frozen value_unit")
        threshold = _threshold(rule)
        supplied = provided.get(metric_id)
        if supplied is None:
            missing += 1
            missing_policy = rule.get("missing_policy")
            if missing_policy == "FAIL":
                failed += 1
                status = "FAIL"
            elif missing_policy == "INCONCLUSIVE":
                inconclusive_missing = True
                status = "INCONCLUSIVE"
            else:
                raise ValueError(
                    f"metric {metric_id} has invalid missing_policy"
                )
            results.append(
                MetricEvaluation(
                    metric_id=metric_id,
                    status=status,
                    comparator=comparator,
                    threshold=threshold,
                    expected_unit=expected_unit,
                    actual_unit=None,
                    value=None,
                    detail="required metric is missing",
                )
            )
            continue
        actual_unit = supplied.get("value_unit")
        number = _finite_number(supplied.get("value"))
        if number is None:
            failed += 1
            results.append(
                MetricEvaluation(
                    metric_id=metric_id,
                    status="FAIL",
                    comparator=comparator,
                    threshold=threshold,
                    expected_unit=expected_unit,
                    actual_unit=(
                        str(actual_unit) if actual_unit is not None else None
                    ),
                    value=None,
                    detail="metric value is nonnumeric or non-finite",
                )
            )
            continue
        if actual_unit != expected_unit:
            failed += 1
            results.append(
                MetricEvaluation(
                    metric_id=metric_id,
                    status="FAIL",
                    comparator=comparator,
                    threshold=threshold,
                    expected_unit=expected_unit,
                    actual_unit=(
                        str(actual_unit) if actual_unit is not None else None
                    ),
                    value=number,
                    detail="metric unit differs from preregistration",
                )
            )
            continue
        passed = _compare(number, comparator, threshold)
        if not passed:
            failed += 1
        results.append(
            MetricEvaluation(
                metric_id=metric_id,
                status="PASS" if passed else "FAIL",
                comparator=comparator,
                threshold=threshold,
                expected_unit=expected_unit,
                actual_unit=str(actual_unit),
                value=number,
                detail="frozen comparator evaluated",
            )
        )

    if required_count <= 0:
        raise ValueError("at least one required primary metric is mandatory")
    passed_count = sum(result.status == "PASS" for result in results)
    if failed:
        verdict = "FAIL"
    elif inconclusive_missing:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "PASS"
    return HoldoutEvaluation(
        required_metric_count=required_count,
        passed_metric_count=passed_count,
        failed_metric_count=failed,
        missing_metric_count=missing,
        metric_results=tuple(results),
        derived_verdict=verdict,
    )


def _csv_by_id(
    path: Path,
    *,
    id_column: str,
    value_column: str,
    label: str,
) -> dict[str, float]:
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames:
                raise ValueError(f"{label} has no CSV header")
            if id_column not in reader.fieldnames or value_column not in reader.fieldnames:
                raise ValueError(
                    f"{label} lacks {id_column} or {value_column}"
                )
            values: dict[str, float] = {}
            for row in reader:
                identifier = str(row.get(id_column, "")).strip()
                if not identifier or identifier in values:
                    raise ValueError(
                        f"{label} has missing or duplicate identifier"
                    )
                try:
                    value = float(str(row.get(value_column, "")).strip())
                except ValueError as exc:
                    raise ValueError(
                        f"{label} contains a nonnumeric value"
                    ) from exc
                if not math.isfinite(value):
                    raise ValueError(f"{label} contains a non-finite value")
                values[identifier] = value
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise ValueError(f"cannot parse metric source {label}") from exc
    if not values:
        raise ValueError(f"{label} has no data rows")
    return values


def recompute_holdout_metrics(
    preregistration: Mapping[str, Any],
    *,
    raw_files: Mapping[str, Path],
    result_files: Mapping[str, Path],
    holdout_ids: list[str],
) -> list[dict[str, Any]]:
    """Recompute frozen primary metrics from snapshot observation/results."""

    required_ids = set(holdout_ids)
    if not required_ids or len(required_ids) != len(holdout_ids):
        raise ValueError("holdout IDs must be nonempty and unique")
    recomputed: list[dict[str, Any]] = []
    for rule in preregistration.get("primary_metrics", []):
        if rule.get("required") is not True:
            continue
        calculation = rule.get("calculation")
        if not isinstance(calculation, Mapping):
            raise ValueError(
                f"metric {rule.get('metric_id')} lacks frozen calculation"
            )
        method = calculation.get("method")
        if method != "NORMALIZED_RMSE":
            raise ValueError(f"unsupported frozen metric method: {method}")
        if rule.get("value_unit") != "1":
            raise ValueError("NORMALIZED_RMSE value_unit must be 1")
        observation_role = str(calculation.get("observation_role", ""))
        result_reference = str(calculation.get("result_file", ""))
        if observation_role not in raw_files:
            raise ValueError(
                f"missing observation role for metric: {observation_role}"
            )
        if result_reference not in result_files:
            raise ValueError(
                f"missing result file for metric: {result_reference}"
            )
        observations = _csv_by_id(
            raw_files[observation_role],
            id_column=str(calculation.get("observation_id_column", "")),
            value_column=str(calculation.get("observation_value_column", "")),
            label=f"{rule['metric_id']} observations",
        )
        predictions = _csv_by_id(
            result_files[result_reference],
            id_column=str(calculation.get("prediction_id_column", "")),
            value_column=str(calculation.get("prediction_value_column", "")),
            label=f"{rule['metric_id']} predictions",
        )
        if set(predictions) != required_ids:
            raise ValueError(
                f"metric {rule['metric_id']} prediction IDs differ from holdout"
            )
        if not required_ids.issubset(observations):
            raise ValueError(
                f"metric {rule['metric_id']} observations omit holdout IDs"
            )
        observed = [observations[identifier] for identifier in holdout_ids]
        predicted = [predictions[identifier] for identifier in holdout_ids]
        denominator = max(
            sum(abs(value) for value in observed) / len(observed),
            1.0e-300,
        )
        value = math.sqrt(
            sum(
                (candidate - reference) ** 2
                for candidate, reference in zip(predicted, observed)
            )
            / len(observed)
        ) / denominator
        recomputed.append(
            {
                "metric_id": rule["metric_id"],
                "value": value,
                "value_unit": rule["value_unit"],
            }
        )
    if not recomputed:
        raise ValueError("no required holdout metric was recomputed")
    return recomputed
