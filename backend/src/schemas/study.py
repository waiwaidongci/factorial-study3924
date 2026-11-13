from pydantic import BaseModel,Field,model_validator
class StudyInput(BaseModel):
    code:str=Field(min_length=2,max_length=60)
    name:str=Field(min_length=2,max_length=160)
    a_levels:list[str]=Field(min_length=2,max_length=5)
    b_levels:list[str]=Field(min_length=2,max_length=4)
    source_file:str=Field(min_length=2,max_length=160)
    note:str=Field(default='',max_length=600)
    csv_text:str=Field(min_length=20,max_length=1000000)
    @model_validator(mode='after')
    def levels_valid(self):
        for levels in (self.a_levels,self.b_levels):
            if len(set(levels))!=len(levels) or any(not 1<=len(v.strip())<=40 or v!=v.strip() for v in levels):raise ValueError('因子水平需唯一、非空且不带首尾空格')
        return self
