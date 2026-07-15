"""Evaluation of configurable data-quality rules against an uploaded snapshot.

Rules are evaluated at upload time, while the raw DataFrame is still available,
so value-level checks (accepted values, uniqueness, regex) are possible without
persisting raw rows.
"""

import re

import pandas as pd

from app.db import models

RULE_TYPES = {
    "column_required",
    "not_null",
    "min_value",
    "max_value",
    "accepted_values",
    "unique",
    "regex",
}


def _alert(rule, message, *, column_name=None, previous=None, current=None):
    return {
        "message": message,
        "severity": rule.severity or "high",
        "column_name": column_name or rule.column_name,
        "metric": "rule",
        "previous_value": str(previous) if previous is not None else None,
        "current_value": str(current) if current is not None else None,
    }


def _evaluate_rule(rule, df: pd.DataFrame) -> list[dict]:
    cfg = rule.config or {}
    col = rule.column_name
    row_count = len(df)

    if rule.rule_type == "column_required":
        if col not in df.columns:
            return [_alert(rule, f"Required column '{col}' is missing")]
        return []

    # Every remaining rule type operates on a specific column.
    if col is None or col not in df.columns:
        # A column-scoped rule whose column is absent is itself a violation.
        if col is not None:
            return [_alert(rule, f"Rule target column '{col}' is missing")]
        return []

    series = df[col]

    if rule.rule_type == "not_null":
        max_null_pct = float(cfg.get("max_null_pct", 0.0))
        null_count = int(series.isna().sum())
        null_pct = (null_count / row_count) if row_count else 0.0
        if null_pct > max_null_pct:
            return [
                _alert(
                    rule,
                    f"Column '{col}' exceeds the allowed null rate "
                    f"({null_pct * 100:.2f}% > {max_null_pct * 100:.2f}%)",
                    current=f"{null_pct * 100:.2f}%",
                )
            ]
        return []

    if rule.rule_type == "min_value":
        value = cfg.get("value")
        numeric = pd.to_numeric(series, errors="coerce")
        actual_min = numeric.min()
        if value is not None and pd.notna(actual_min) and actual_min < float(value):
            return [
                _alert(
                    rule,
                    f"Column '{col}' has values below the allowed minimum",
                    previous=value,
                    current=f"{actual_min:.6g}",
                )
            ]
        return []

    if rule.rule_type == "max_value":
        value = cfg.get("value")
        numeric = pd.to_numeric(series, errors="coerce")
        actual_max = numeric.max()
        if value is not None and pd.notna(actual_max) and actual_max > float(value):
            return [
                _alert(
                    rule,
                    f"Column '{col}' has values above the allowed maximum",
                    previous=value,
                    current=f"{actual_max:.6g}",
                )
            ]
        return []

    if rule.rule_type == "accepted_values":
        allowed = set(str(v) for v in cfg.get("values", []))
        if not allowed:
            return []
        non_null = series.dropna().astype(str)
        invalid = sorted(set(non_null[~non_null.isin(allowed)]))
        if invalid:
            preview = ", ".join(invalid[:5])
            return [
                _alert(
                    rule,
                    f"Column '{col}' contains values outside the accepted set "
                    f"({len(invalid)} distinct: {preview}…)",
                    current=preview,
                )
            ]
        return []

    if rule.rule_type == "unique":
        non_null = series.dropna()
        dup_count = int(non_null.duplicated().sum())
        if dup_count > 0:
            return [
                _alert(
                    rule,
                    f"Column '{col}' has {dup_count} duplicate value(s) "
                    f"but is expected to be unique",
                    current=dup_count,
                )
            ]
        return []

    if rule.rule_type == "regex":
        pattern = cfg.get("pattern")
        if not pattern:
            return []
        try:
            compiled = re.compile(pattern)
        except re.error:
            return [_alert(rule, f"Rule for '{col}' has an invalid regex pattern")]
        non_null = series.dropna().astype(str)
        mismatches = int((~non_null.map(lambda v: bool(compiled.match(v)))).sum())
        if mismatches > 0:
            return [
                _alert(
                    rule,
                    f"Column '{col}' has {mismatches} value(s) not matching "
                    f"the expected pattern",
                    current=mismatches,
                )
            ]
        return []

    return []


def evaluate_rules(db, dataset_id, df: pd.DataFrame) -> list[dict]:
    """Evaluate all active rules for a dataset and return alert payloads."""
    rules = (
        db.query(models.DatasetRule)
        .filter(
            models.DatasetRule.dataset_id == dataset_id,
            models.DatasetRule.is_active.is_(True),
        )
        .all()
    )

    alerts: list[dict] = []
    for rule in rules:
        try:
            alerts.extend(_evaluate_rule(rule, df))
        except Exception:  # pragma: no cover - never let one rule break ingestion
            continue
    return alerts
