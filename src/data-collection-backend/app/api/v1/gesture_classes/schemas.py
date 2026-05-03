from pydantic import BaseModel


class GestureClassRequest(BaseModel):
    name: str
