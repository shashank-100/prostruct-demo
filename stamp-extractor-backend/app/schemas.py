from pydantic import BaseModel
from typing import List, Optional

class StampResponse(BaseModel):
    page: int
    symbol_type: str
    bounding_box: List[int]
    engineer_name: Optional[str]
    license_number: Optional[str]
    units: str
