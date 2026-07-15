"""Grouping of alerts into incidents.

An alert is a single detected event. An incident is an operational problem that
can group several alerts. When an upload produces alerts we attach them to an
existing active incident for the dataset (deduplication), or open a new one.
"""

from datetime import datetime, timezone

from app.db import models

# Statuses that still "absorb" new alerts instead of opening a fresh incident.
ACTIVE_STATUSES = ("open", "acknowledged", "muted")
# Statuses considered live for status/severity computation (muted is suppressed).
LIVE_STATUSES = ("open", "acknowledged")
VALID_STATUSES = ("open", "acknowledged", "resolved", "muted")

_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}


def _max_severity(severities) -> str:
    best = "medium"
    for sev in severities:
        if _SEVERITY_RANK.get(sev, 1) > _SEVERITY_RANK.get(best, 1):
            best = sev
    return best


def _build_title(alerts) -> str:
    metrics = {a.get("metric") for a in alerts if a.get("metric")}
    if metrics == {"row_count"}:
        return "Row volume drop detected"
    if metrics == {"schema"}:
        return "Schema change detected"
    if metrics == {"null_rate"}:
        return "Data completeness degraded"
    if metrics == {"rule"}:
        return "Data-quality rule violation"
    return f"{len(alerts)} anomaly(ies) detected"


def assign_incident(db, dataset_id, alert_payloads, run_id=None):
    """Create/attach an incident for a batch of alert payloads.

    Returns the ``Incident`` (or ``None`` if there were no alerts). The caller is
    responsible for persisting the alerts with ``incident_id`` set.
    """
    if not alert_payloads:
        return None

    severity = _max_severity(a.get("severity") for a in alert_payloads)
    now = datetime.now(timezone.utc)

    incident = (
        db.query(models.Incident)
        .filter(
            models.Incident.dataset_id == dataset_id,
            models.Incident.status.in_(ACTIVE_STATUSES),
        )
        .order_by(models.Incident.created_at.desc())
        .first()
    )

    if incident is None:
        incident = models.Incident(
            dataset_id=dataset_id,
            title=_build_title(alert_payloads),
            status="open",
            severity=severity,
        )
        db.add(incident)
        db.flush()
    else:
        incident.updated_at = now
        # Only escalate severity for incidents that are actively being worked.
        if incident.status in LIVE_STATUSES:
            incident.severity = _max_severity([incident.severity, severity])

    return incident


def update_incident(db, incident: models.Incident, *, status=None, assignee=None):
    now = datetime.now(timezone.utc)
    if status is not None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid incident status: {status}")
        incident.status = status
        incident.resolved_at = now if status == "resolved" else None
    if assignee is not None:
        incident.assignee = assignee or None
    incident.updated_at = now
    db.commit()
    db.refresh(incident)
    return incident
