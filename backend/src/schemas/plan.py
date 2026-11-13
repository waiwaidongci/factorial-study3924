from pydantic import BaseModel,Field
class PlanInput(BaseModel):
    title:str=Field(min_length=2,max_length=160)
    run_id:int
    contrast_index:int=Field(ge=1)
    action:str=Field(min_length=10,max_length=1200)
    verification:str=Field(min_length=10,max_length=1200)
