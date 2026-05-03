from pydantic import BaseModel


class GestureTypeRequest(BaseModel):
    name: str
