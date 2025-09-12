from __future__ import annotations
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel

StatusStr = Literal[
    "RECEIVED", "REJECTED_MODEL_MISMATCH", "REJECTED_VALIDATION",
    "FILES_SAVED", "SPLIT_DONE", "READY",
    "ERROR_SAVE", "ERROR_SPLIT", "ERROR_UNHANDLED"
]

class VolItem(BaseModel):
    date: str   # YYYY-MM-DD
    count: int

class VolItemByService(BaseModel):
    date: str
    service_type: str
    count: int

class LastSubmissionItem(BaseModel):
    job_id: str
    service_type: str
    status: str
    created_at: str
    user: str

class ServiceMetricsOut(BaseModel):
    service_type: str
    total: int
    by_status: Dict[str, int]
    volumetry: List[VolItem]
    last: List[LastSubmissionItem] = []

class GlobalMetricsOut(BaseModel):
    total: int
    by_service: Dict[str, int]
    by_status: Dict[str, int]
    volumetry: List[VolItemByService]
    last: List[LastSubmissionItem] = []
