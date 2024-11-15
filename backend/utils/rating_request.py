# assuming RatingRequest class is defined here
from pydantic import BaseModel


class RatingRequest(BaseModel):
    result_id: str
    good_response: bool
