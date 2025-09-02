from typing import Literal
from pydantic import BaseModel

ServiceType = Literal["NFE", "CTE", "NFCE", "CFE", "SENATRAN"]

class SubmitOut(BaseModel):
    message: str
    job_id: str
    service_type: ServiceType
    stored_at: str
    user: str
