from pydantic import BaseModel,Field
class ReadingInput(BaseModel):
    specimen_code:str=Field(min_length=1,max_length=80)
    temperature:str=Field(min_length=1,max_length=40)
    glaze:str=Field(min_length=1,max_length=40)
    strength_mpa:float=Field(gt=0,le=5000,allow_inf_nan=False)
