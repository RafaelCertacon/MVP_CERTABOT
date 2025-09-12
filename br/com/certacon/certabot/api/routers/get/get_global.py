from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from br.com.certacon.certabot.api.deps import get_db, require_roles
from br.com.certacon.certabot.db.schemas.metrics import GlobalMetricsOut, ServiceMetricsOut
from br.com.certacon.certabot.utils.metrics import service_metrics, global_metrics

router = APIRouter(tags=["metrics"])

def qparams(
    since: Optional[str] = Query(None, description="YYYY-MM-DD"),
    until: Optional[str] = Query(None, description="YYYY-MM-DD"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Últimos N dias (ignora since/until)"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    limit_last: int = Query(10, ge=0, le=200, description="Qtde de últimos registros a retornar"),
):
    return dict(since=since, until=until, days=days, status=status, limit_last=limit_last)

@router.get("/mvp/metrics", response_model=GlobalMetricsOut, summary="Métricas gerais (todos os serviços)")
def get_metrics_global(params: dict = Depends(qparams), db: Session = Depends(get_db), _=Depends(require_roles("admin","operador"))):
    return global_metrics(db, **params)

@router.get("/mvp/nfe/metrics", response_model=ServiceMetricsOut, summary="Métricas NFE")
def get_metrics_nfe(params: dict = Depends(qparams), db: Session = Depends(get_db), _=Depends(require_roles("admin","operador"))):
    return service_metrics(db, "NFE", **params)

@router.get("/mvp/nfce/metrics", response_model=ServiceMetricsOut, summary="Métricas NFCE")
def get_metrics_nfce(params: dict = Depends(qparams), db: Session = Depends(get_db), _=Depends(require_roles("admin","operador"))):
    return service_metrics(db, "NFCE", **params)

@router.get("/mvp/cte/metrics", response_model=ServiceMetricsOut, summary="Métricas CTE")
def get_metrics_cte(params: dict = Depends(qparams), db: Session = Depends(get_db), _=Depends(require_roles("admin","operador"))):
    return service_metrics(db, "CTE", **params)

@router.get("/mvp/cfe/metrics", response_model=ServiceMetricsOut, summary="Métricas CFE")
def get_metrics_cfe(params: dict = Depends(qparams), db: Session = Depends(get_db), _=Depends(require_roles("admin","operador"))):
    return service_metrics(db, "CFE", **params)

@router.get("/mvp/senatran/metrics", response_model=ServiceMetricsOut, summary="Métricas SENATRAN")
def get_metrics_senatran(params: dict = Depends(qparams), db: Session = Depends(get_db), _=Depends(require_roles("admin","operador"))):
    return service_metrics(db, "SENATRAN", **params)
