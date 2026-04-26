from pydantic import BaseModel


class DatasetRequest(BaseModel):
    name: str
    description: str
