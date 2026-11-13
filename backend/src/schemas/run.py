from typing import Literal
from pydantic import BaseModel,Field
class RunInput(BaseModel):
    name:str=Field(min_length=2,max_length=160)
    study_id:int
    alpha:float=Field(default=.05,ge=.001,le=.2,allow_inf_nan=False)
    contrast_family:Literal['all_simple_pairwise']='all_simple_pairwise'
