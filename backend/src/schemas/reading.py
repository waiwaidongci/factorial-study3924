from pydantic import BaseModel,ConfigDict,Field
class ReadingInput(BaseModel):
    # 旧表只有四列：额外列一律报错由 service 层做白名单拦截，这里忽略未知列以保持宽松解析
    model_config = ConfigDict(extra='ignore')
    specimen_code:str=Field(min_length=1,max_length=80)
    temperature:str=Field(min_length=1,max_length=40)
    glaze:str=Field(min_length=1,max_length=40)
    strength_mpa:float=Field(gt=0,le=5000,allow_inf_nan=False)
    measure_no:int=Field(default=1,ge=1,le=999)
