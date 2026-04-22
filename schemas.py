from pydantic import BaseModel

class AskResponse(BaseModel):
    answer: str

class IngestResponse(BaseModel):
    message: str
    count: int
