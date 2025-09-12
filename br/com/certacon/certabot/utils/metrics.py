from __future__ import annotations
from typing import Optional, Sequence, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, and_
from br.com.certacon.certabot.db import models

def _date_filters(since: Optional[str], until: Optional[str], days: Optional[int]):
    where = []
    if days and not since and not until:
        start = (datetime.utcnow() - timedelta(days=days)).date()
        where.append(models.ServiceSubmission.created_at >= start)
    if since:
        where.append(models.ServiceSubmission.created_at >= since)
    if until:
        where.append(models.ServiceSubmission.created_at < f"{until} 23:59:59.999")
    return where

def service_metrics(
    db: Session, service: str, *,
    since: Optional[str], until: Optional[str], days: Optional[int],
    status: Optional[str], limit_last: int = 10
) -> Dict[str, Any]:
    qbase = db.query(models.ServiceSubmission).filter(models.ServiceSubmission.service_type == service)
    for cond in _date_filters(since, until, days):
        qbase = qbase.filter(cond)
    if status:
        qbase = qbase.filter(models.ServiceSubmission.status == status)

    total = qbase.with_entities(func.count(models.ServiceSubmission.id)).scalar() or 0

    rows = qbase.with_entities(models.ServiceSubmission.status, func.count()).group_by(models.ServiceSubmission.status).all()
    by_status = {s or "": int(c) for s, c in rows}

    day = cast(models.ServiceSubmission.created_at, Date).label("day")
    vrows = qbase.with_entities(day, func.count()).group_by(day).order_by(day).all()
    volumetry = [{"date": d.isoformat(), "count": int(c)} for d, c in vrows]

    lastq = qbase.order_by(models.ServiceSubmission.created_at.desc()).limit(limit_last).all()
    last = [{
        "job_id": s.job_id,
        "service_type": s.service_type,
        "status": s.status,
        "created_at": s.created_at.isoformat() if s.created_at else "",
        "user": s.user.username if s.user else ""
    } for s in lastq]

    return {
        "service_type": service,
        "total": int(total),
        "by_status": by_status,
        "volumetry": volumetry,
        "last": last,
    }

def global_metrics(
    db: Session, *,
    since: Optional[str], until: Optional[str], days: Optional[int],
    status: Optional[str], limit_last: int = 20
) -> Dict[str, Any]:
    qbase = db.query(models.ServiceSubmission)
    for cond in _date_filters(since, until, days):
        qbase = qbase.filter(cond)
    if status:
        qbase = qbase.filter(models.ServiceSubmission.status == status)

    total = qbase.with_entities(func.count(models.ServiceSubmission.id)).scalar() or 0

    br = qbase.with_entities(models.ServiceSubmission.service_type, func.count()).group_by(models.ServiceSubmission.service_type).all()
    by_service = {svc: int(c) for svc, c in br}

    bs = qbase.with_entities(models.ServiceSubmission.status, func.count()).group_by(models.ServiceSubmission.status).all()
    by_status = {s or "": int(c) for s, c in bs}

    day = cast(models.ServiceSubmission.created_at, Date).label("day")
    vv = qbase.with_entities(day, models.ServiceSubmission.service_type, func.count()) \
              .group_by(day, models.ServiceSubmission.service_type) \
              .order_by(day, models.ServiceSubmission.service_type).all()
    volumetry = [{"date": d.isoformat(), "service_type": svc, "count": int(c)} for d, svc, c in vv]

    lastq = qbase.order_by(models.ServiceSubmission.created_at.desc()).limit(limit_last).all()
    last = [{
        "job_id": s.job_id,
        "service_type": s.service_type,
        "status": s.status,
        "created_at": s.created_at.isoformat() if s.created_at else "",
        "user": s.user.username if s.user else ""
    } for s in lastq]

    return {
        "total": int(total),
        "by_service": by_service,
        "by_status": by_status,
        "volumetry": volumetry,
        "last": last,
    }
