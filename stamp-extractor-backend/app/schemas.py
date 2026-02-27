from pydantic import BaseModel
from typing import List, Optional

class StampInfo(BaseModel):
    symbol_type: str
    bounding_box: List[int]
    engineer_name: Optional[str]
    license_number: Optional[str]

class StampResponse(BaseModel):
    page: int
    stamps: List[StampInfo]
    raw_text: Optional[str]
    units: str
