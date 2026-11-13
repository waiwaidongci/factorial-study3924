from pydantic import BaseModel
class CellSummary(BaseModel):
    id:int
    study_id:int
    temperature:str
    glaze:str
    n:int
    mean:float
    std:float
