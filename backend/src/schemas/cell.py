from pydantic import BaseModel
class CellSummary(BaseModel):
    id:int
    study_id:int
    temperature:str
    glaze:str
    n:int
    raw_reading_count:int
    mean:float
    std:float
