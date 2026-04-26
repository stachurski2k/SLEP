from pydantic import BaseModel, ConfigDict


class DatasetSchema(BaseModel):
    id: int
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)
