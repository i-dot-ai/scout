# assuming Filters class is defined here
from typing import Any
from typing import Dict

from pydantic import BaseModel


class Filters(BaseModel):
    model: str
    filters: Dict[str, Any]
